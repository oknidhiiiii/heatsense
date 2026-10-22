/**
 * Adaptive Level of Detail (LOD) Heatmap Generator with Web Worker Offloading and LRU Caching.
 * Automatically selects optimal raster dimensions (256, 512, or 1024) based on camera altitude.
 */

import { GridCell, MapGridResponse } from '../types/api';
import { getTemperatureRgb } from './colorScale';
import { heatmapLruCache } from './heatmapCache';

let workerInstance: Worker | null = null;
let nextRequestId = 1;
const pendingRequests = new Map<
  string,
  {
    resolve: (res: { dataUrl: string; width: number; height: number }) => void;
    reject: (err: Error) => void;
  }
>();

function getWorker(): Worker | null {
  if (typeof window === 'undefined' || typeof window.Worker === 'undefined') {
    return null;
  }

  if (!workerInstance) {
    try {
      workerInstance = new Worker(
        new URL('../workers/heatmap.worker.ts', import.meta.url),
        { type: 'module' }
      );

      workerInstance.onmessage = (event) => {
        const { id, bitmap, dataUrl, width, height, error } = event.data;
        const pending = pendingRequests.get(id);
        if (!pending) return;

        pendingRequests.delete(id);

        if (error) {
          pending.reject(new Error(error));
          return;
        }

        if (bitmap) {
          // Convert ImageBitmap to Data URL on main thread canvas
          try {
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            if (ctx) {
              ctx.drawImage(bitmap, 0, 0);
              const url = canvas.toDataURL();
              bitmap.close();
              pending.resolve({ dataUrl: url, width, height });
              return;
            }
          } catch (e) {
            bitmap.close();
            pending.reject(e as Error);
            return;
          }
        }

        if (dataUrl) {
          pending.resolve({ dataUrl, width, height });
          return;
        }

        pending.reject(new Error('Worker returned empty response'));
      };

      workerInstance.onerror = (err) => {
        console.warn('Heatmap worker error, will fallback to sync generator:', err);
      };
    } catch (e) {
      console.warn('Failed to initialize heatmap worker:', e);
      workerInstance = null;
    }
  }

  return workerInstance;
}

/**
 * Determine Adaptive Level of Detail (LOD) canvas resolution based on camera altitude.
 */
export function getAdaptiveLodSize(cameraHeight: number): 256 | 512 | 1024 {
  if (cameraHeight > 800000) {
    // High altitude (> 800 km): Overview mode (super fast 256x256)
    return 256;
  }
  if (cameraHeight > 200000) {
    // Mid altitude (200 km to 800 km): Regional district mode (512x512)
    return 512;
  }
  // Low altitude (< 200 km): Intra-urban high detail mode (1024x1024)
  return 1024;
}

/**
 * Synchronous fallback generator using standard in-thread HTMLCanvasElement.
 */
export function generateHeatmapCanvasSync(
  gridData: MapGridResponse,
  targetBbox: [number, number, number, number],
  boundaryPolygons: [number, number][][],
  canvasSize = 512
): HTMLCanvasElement | null {
  const [minLat, minLon, maxLat, maxLon] = targetBbox;
  if (maxLat <= minLat || maxLon <= minLon) return null;

  const validCells = gridData.cells.filter(
    (c): c is GridCell & { value: number } => c.value !== null && !isNaN(c.value)
  );
  if (validCells.length === 0) return null;

  const temps = validCells.map((c) => c.value);
  const minT = Math.min(...temps);
  const maxT = Math.max(...temps);

  const cellLats = validCells.map((c) => c.latitude);
  const cellLons = validCells.map((c) => c.longitude);
  const gMinLat = Math.min(...cellLats);
  const gMaxLat = Math.max(...cellLats);
  const gMinLon = Math.min(...cellLons);
  const gMaxLon = Math.max(...cellLons);

  const res = gridData.grid_definition?.resolution_deg || 0.1;
  const cols = Math.max(2, Math.min(64, Math.round((gMaxLon - gMinLon) / res) + 1));
  const rows = Math.max(2, Math.min(64, Math.round((gMaxLat - gMinLat) / res) + 1));

  const coarseCanvas = document.createElement('canvas');
  coarseCanvas.width = cols;
  coarseCanvas.height = rows;
  const coarseCtx = coarseCanvas.getContext('2d');
  if (!coarseCtx) return null;

  const imgData = coarseCtx.createImageData(cols, rows);
  const data = imgData.data;
  const gridVals = new Float32Array(cols * rows).fill(NaN);

  for (const cell of validCells) {
    const c = Math.round(((cell.longitude - gMinLon) / (gMaxLon - gMinLon || 1)) * (cols - 1));
    const r = Math.round(((gMaxLat - cell.latitude) / (gMaxLat - gMinLat || 1)) * (rows - 1));
    if (c >= 0 && c < cols && r >= 0 && r < rows) {
      gridVals[r * cols + c] = cell.value;
    }
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const idx = r * cols + c;
      let val = gridVals[idx];
      if (isNaN(val)) {
        let bestDist = Infinity;
        let bestVal = (minT + maxT) / 2;
        for (let dr = -3; dr <= 3; dr++) {
          for (let dc = -3; dc <= 3; dc++) {
            const nr = r + dr;
            const nc = c + dc;
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
              const nVal = gridVals[nr * cols + nc];
              if (!isNaN(nVal)) {
                const dist = dr * dr + dc * dc;
                if (dist < bestDist) {
                  bestDist = dist;
                  bestVal = nVal;
                }
              }
            }
          }
        }
        val = bestVal;
      }

      const [red, green, blue] = getTemperatureRgb(val, minT, maxT);
      const pIdx = idx * 4;
      data[pIdx] = red;
      data[pIdx + 1] = green;
      data[pIdx + 2] = blue;
      data[pIdx + 3] = 230;
    }
  }

  coarseCtx.putImageData(imgData, 0, 0);

  const mainCanvas = document.createElement('canvas');
  mainCanvas.width = canvasSize;
  mainCanvas.height = canvasSize;
  const ctx = mainCanvas.getContext('2d');
  if (!ctx) return null;

  ctx.save();

  ctx.beginPath();
  let hasValidPoly = false;
  for (const poly of boundaryPolygons) {
    if (!poly || poly.length < 3) continue;
    for (let i = 0; i < poly.length; i++) {
      const [lon, lat] = poly[i];
      const x = ((lon - minLon) / (maxLon - minLon)) * canvasSize;
      const y = ((maxLat - lat) / (maxLat - minLat)) * canvasSize;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.closePath();
    hasValidPoly = true;
  }

  if (hasValidPoly) {
    ctx.clip();
  }

  const gx = ((gMinLon - minLon) / (maxLon - minLon)) * canvasSize;
  const gy = ((maxLat - gMaxLat) / (maxLat - minLat)) * canvasSize;
  const gw = ((gMaxLon - gMinLon) / (maxLon - minLon)) * canvasSize;
  const gh = ((gMaxLat - gMinLat) / (maxLat - minLat)) * canvasSize;

  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.filter = 'blur(4px)';
  ctx.drawImage(coarseCanvas, gx, gy, gw, gh);

  ctx.restore();

  return mainCanvas;
}

/**
 * Asynchronously generate continuous thermal heatmap with Web Worker and LRU cache.
 */
export async function generateContinuousHeatmapAsync(
  gridData: MapGridResponse,
  targetBbox: [number, number, number, number],
  boundaryPolygons: [number, number][][],
  cameraHeight: number,
  cacheKeyParams: {
    regionId: string;
    layer: string;
    validAt: string;
    theme: string;
  }
): Promise<{ dataUrl: string; width: number; height: number } | null> {
  const lodSize = getAdaptiveLodSize(cameraHeight);
  const cacheKey = `${cacheKeyParams.regionId}:${cacheKeyParams.layer}:${cacheKeyParams.validAt}:${lodSize}:${cacheKeyParams.theme}`;

  // 1. Check LRU memory cache
  const cached = heatmapLruCache.get(cacheKey);
  if (cached) {
    return cached;
  }

  // 2. Try offloading to Web Worker
  const worker = getWorker();
  if (worker) {
    try {
      const requestId = `req_${nextRequestId++}`;
      const promise = new Promise<{ dataUrl: string; width: number; height: number }>(
        (resolve, reject) => {
          pendingRequests.set(requestId, { resolve, reject });
        }
      );

      worker.postMessage({
        id: requestId,
        gridData: {
          cells: gridData.cells,
          grid_definition: gridData.grid_definition,
        },
        targetBbox,
        boundaryPolygons,
        canvasSize: lodSize,
      });

      const result = await promise;
      heatmapLruCache.set(cacheKey, {
        dataUrl: result.dataUrl,
        width: result.width,
        height: result.height,
        timestamp: Date.now(),
      });
      return result;
    } catch (err) {
      console.warn('Worker heatmap generation failed, falling back to sync:', err);
    }
  }

  // 3. Fallback to synchronous in-thread canvas
  const canvas = generateHeatmapCanvasSync(gridData, targetBbox, boundaryPolygons, lodSize);
  if (!canvas) return null;

  const dataUrl = canvas.toDataURL();
  const entry = {
    dataUrl,
    width: lodSize,
    height: lodSize,
    timestamp: Date.now(),
  };
  heatmapLruCache.set(cacheKey, entry);
  return entry;
}

/**
 * Dedicated Web Worker for Continuous Heatmap Rasterization and Boundary Stencil Clipping.
 * Utilizes reusable OffscreenCanvases and vectorized nearest-neighbor infill for high performance.
 */

import { getTemperatureRgb } from '../utils/colorScale';

export interface HeatmapWorkerRequest {
  id: string;
  gridData: {
    cells: Array<{ latitude: number; longitude: number; value: number | null }>;
    grid_definition?: { resolution_deg?: number };
  };
  targetBbox: [number, number, number, number];
  boundaryPolygons: [number, number][][];
  canvasSize: number;
}

export interface HeatmapWorkerResponse {
  id: string;
  bitmap?: ImageBitmap;
  dataUrl?: string;
  width: number;
  height: number;
  error?: string;
}

// Reusable canvas contexts to avoid GPU context recreation and GC thrashing
let coarseCanvas: OffscreenCanvas | null = null;
let coarseCtx: OffscreenCanvasRenderingContext2D | null = null;
let mainCanvas: OffscreenCanvas | null = null;
let mainCtx: OffscreenCanvasRenderingContext2D | null = null;

self.onmessage = async (event: MessageEvent<HeatmapWorkerRequest>) => {
  const { id, gridData, targetBbox, boundaryPolygons, canvasSize } = event.data;

  try {
    const [minLat, minLon, maxLat, maxLon] = targetBbox;
    if (maxLat <= minLat || maxLon <= minLon) {
      self.postMessage({ id, error: 'Invalid bounding box' });
      return;
    }

    const validCells = gridData.cells.filter(
      (c): c is { latitude: number; longitude: number; value: number } =>
        c.value !== null && !isNaN(c.value)
    );

    if (validCells.length === 0) {
      self.postMessage({ id, error: 'No valid temperature cells found' });
      return;
    }

    const temps = validCells.map((c) => c.value);
    const minT = Math.min(...temps);
    const maxT = Math.max(...temps);

    // 1. Determine grid spatial bounds
    const cellLats = validCells.map((c) => c.latitude);
    const cellLons = validCells.map((c) => c.longitude);
    const gMinLat = Math.min(...cellLats);
    const gMaxLat = Math.max(...cellLats);
    const gMinLon = Math.min(...cellLons);
    const gMaxLon = Math.max(...cellLons);

    const res = gridData.grid_definition?.resolution_deg || 0.1;
    const cols = Math.max(2, Math.min(64, Math.round((gMaxLon - gMinLon) / res) + 1));
    const rows = Math.max(2, Math.min(64, Math.round((gMaxLat - gMinLat) / res) + 1));

    // 2. Reuse coarse canvas
    if (!coarseCanvas) {
      coarseCanvas = new OffscreenCanvas(cols, rows);
      coarseCtx = coarseCanvas.getContext('2d');
    } else {
      if (coarseCanvas.width !== cols) coarseCanvas.width = cols;
      if (coarseCanvas.height !== rows) coarseCanvas.height = rows;
    }

    if (!coarseCtx) {
      self.postMessage({ id, error: 'Failed to create coarse OffscreenCanvas context' });
      return;
    }

    const imgData = coarseCtx.createImageData(cols, rows);
    const data = imgData.data;
    const gridVals = new Float32Array(cols * rows).fill(NaN);
    const knownPoints: { r: number; c: number; val: number }[] = [];

    const lonSpan = gMaxLon - gMinLon || 1;
    const latSpan = gMaxLat - gMinLat || 1;

    for (const cell of validCells) {
      const c = Math.round(((cell.longitude - gMinLon) / lonSpan) * (cols - 1));
      const r = Math.round(((gMaxLat - cell.latitude) / latSpan) * (rows - 1));
      if (c >= 0 && c < cols && r >= 0 && r < rows) {
        gridVals[r * cols + c] = cell.value;
        knownPoints.push({ r, c, val: cell.value });
      }
    }

    // Fast infill using known points list
    const numKnown = knownPoints.length;
    const defaultVal = (minT + maxT) / 2;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const idx = r * cols + c;
        let val = gridVals[idx];

        if (isNaN(val)) {
          if (numKnown === 0) {
            val = defaultVal;
          } else {
            let bestDist = Infinity;
            let bestVal = defaultVal;
            for (let k = 0; k < numKnown; k++) {
              const kp = knownPoints[k];
              const dr = r - kp.r;
              const dc = c - kp.c;
              const dist = dr * dr + dc * dc;
              if (dist < bestDist) {
                bestDist = dist;
                bestVal = kp.val;
                if (dist <= 1) break; // Early exit on immediate neighbor
              }
            }
            val = bestVal;
          }
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

    // 3. Reuse main smoothed OffscreenCanvas
    const width = canvasSize;
    const height = canvasSize;
    if (!mainCanvas) {
      mainCanvas = new OffscreenCanvas(width, height);
      mainCtx = mainCanvas.getContext('2d');
    } else {
      if (mainCanvas.width !== width) mainCanvas.width = width;
      if (mainCanvas.height !== height) mainCanvas.height = height;
    }

    if (!mainCtx) {
      self.postMessage({ id, error: 'Failed to create main OffscreenCanvas context' });
      return;
    }

    mainCtx.clearRect(0, 0, width, height);
    mainCtx.save();

    // Draw clipping stencil path
    mainCtx.beginPath();
    let hasValidPoly = false;
    for (const poly of boundaryPolygons) {
      if (!poly || poly.length < 3) continue;
      for (let i = 0; i < poly.length; i++) {
        const [lon, lat] = poly[i];
        const x = ((lon - minLon) / (maxLon - minLon)) * width;
        const y = ((maxLat - lat) / (maxLat - minLat)) * height;
        if (i === 0) {
          mainCtx.moveTo(x, y);
        } else {
          mainCtx.lineTo(x, y);
        }
      }
      mainCtx.closePath();
      hasValidPoly = true;
    }

    if (hasValidPoly) {
      mainCtx.clip();
    }

    const gx = ((gMinLon - minLon) / (maxLon - minLon)) * width;
    const gy = ((maxLat - gMaxLat) / (maxLat - minLat)) * height;
    const gw = ((gMaxLon - gMinLon) / (maxLon - minLon)) * width;
    const gh = ((gMaxLat - gMinLat) / (maxLat - minLat)) * height;

    mainCtx.imageSmoothingEnabled = true;
    mainCtx.imageSmoothingQuality = 'high';
    try {
      mainCtx.filter = 'blur(4px)';
    } catch (_) {}
    mainCtx.drawImage(coarseCanvas, gx, gy, gw, gh);

    mainCtx.restore();

    // 4. Transfer output back to main thread
    if (typeof mainCanvas.transferToImageBitmap === 'function') {
      const bitmap = mainCanvas.transferToImageBitmap();
      (self as unknown as Worker).postMessage(
        {
          id,
          bitmap,
          width,
          height,
        },
        [bitmap]
      );
    } else {
      const blob = await mainCanvas.convertToBlob();
      const reader = new FileReader();
      const dataUrl = await new Promise<string>((resolve, reject) => {
        reader.onloadend = () => resolve(reader.result as string);
        reader.onerror = () => reject(new Error('Failed to read canvas blob'));
        reader.readAsDataURL(blob);
      });
      self.postMessage({
        id,
        dataUrl,
        width,
        height,
      });
    }
  } catch (err) {
    self.postMessage({
      id,
      error: String(err),
    });
  }
};

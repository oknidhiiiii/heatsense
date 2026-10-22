/**
 * Dedicated Web Worker for Continuous Heatmap Rasterization and Boundary Stencil Clipping.
 * Offloads heavy bilinear interpolation and polygon ray-containment math from the main thread.
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

    // 2. Coarse grid offscreen canvas
    const coarseCanvas = new OffscreenCanvas(cols, rows);
    const coarseCtx = coarseCanvas.getContext('2d');
    if (!coarseCtx) {
      self.postMessage({ id, error: 'Failed to create coarse OffscreenCanvas context' });
      return;
    }

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

    // Nearest-neighbor fill for unassigned pixels
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

    // 3. Main smoothed OffscreenCanvas with boundary stencil clipping
    const width = canvasSize;
    const height = canvasSize;
    const mainCanvas = new OffscreenCanvas(width, height);
    const ctx = mainCanvas.getContext('2d');
    if (!ctx) {
      self.postMessage({ id, error: 'Failed to create main OffscreenCanvas context' });
      return;
    }

    ctx.save();

    // Draw clipping stencil path
    ctx.beginPath();
    let hasValidPoly = false;
    for (const poly of boundaryPolygons) {
      if (!poly || poly.length < 3) continue;
      for (let i = 0; i < poly.length; i++) {
        const [lon, lat] = poly[i];
        const x = ((lon - minLon) / (maxLon - minLon)) * width;
        const y = ((maxLat - lat) / (maxLat - minLat)) * height;
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

    // Bilinear coarse grid drawn with smooth scaling
    const gx = ((gMinLon - minLon) / (maxLon - minLon)) * width;
    const gy = ((maxLat - gMaxLat) / (maxLat - minLat)) * height;
    const gw = ((gMaxLon - gMinLon) / (maxLon - minLon)) * width;
    const gh = ((gMaxLat - gMinLat) / (maxLat - minLat)) * height;

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    try {
      ctx.filter = 'blur(4px)';
    } catch (_) {
      // Ignore filter if unsupported in current OffscreenCanvas environment
    }
    ctx.drawImage(coarseCanvas, gx, gy, gw, gh);

    ctx.restore();

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
      // Fallback: convert to blob and dataUrl
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

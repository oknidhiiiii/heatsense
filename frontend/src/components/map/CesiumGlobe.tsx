import React, { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { GridCell, LocationItem, MapGridResponse } from '../../types/api';
import { getTemperatureRgb } from '../../utils/colorScale';
import { CITIES_DATA, CityData, findCityById, getCityAtLocation } from '../../utils/cityBoundaries';

// Set Cesium Ion token if configured
const ION_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN;
if (ION_TOKEN) {
  Cesium.Ion.defaultAccessToken = ION_TOKEN;
}

function createImageryProvider(type: 'osm' | 'dark'): Cesium.ImageryProvider {
  if (type === 'osm') {
    return new Cesium.UrlTemplateImageryProvider({
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      subdomains: ['a', 'b', 'c'],
      maximumLevel: 19,
      credit: new Cesium.Credit('© OpenStreetMap contributors'),
    });
  }
  return new Cesium.UrlTemplateImageryProvider({
    url: 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    maximumLevel: 16,
    credit: new Cesium.Credit('Tiles © Esri (World Dark Gray)'),
  });
}

function getCartographicFromScreen(
  viewer: Cesium.Viewer,
  position: Cesium.Cartesian2
): { lat: number; lon: number } | null {
  let cartesian = viewer.camera.pickEllipsoid(position, viewer.scene.globe.ellipsoid);

  if (!cartesian) {
    const ray = viewer.camera.getPickRay(position);
    if (ray) {
      cartesian = viewer.scene.globe.pick(ray, viewer.scene);
    }
  }

  if (cartesian) {
    const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
    return {
      lat: Cesium.Math.toDegrees(cartographic.latitude),
      lon: Cesium.Math.toDegrees(cartographic.longitude),
    };
  }
  return null;
}

function flyToCity(viewer: Cesium.Viewer, city: CityData) {
  viewer.camera.cancelFlight();

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const duration = prefersReducedMotion ? 0 : 1.6;

  if (city.bbox) {
    const [minLat, minLon, maxLat, maxLon] = city.bbox;
    const padLat = Math.max(0.04, (maxLat - minLat) * 0.18);
    const padLon = Math.max(0.04, (maxLon - minLon) * 0.18);

    const rect = Cesium.Rectangle.fromDegrees(
      minLon - padLon,
      minLat - padLat,
      maxLon + padLon,
      maxLat + padLat
    );

    viewer.camera.flyTo({
      destination: rect,
      duration,
    });
  } else {
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(
        city.longitude,
        city.latitude,
        city.cameraHeight || 80000.0
      ),
      duration,
    });
  }
}

function generateContinuousHeatmapCanvas(
  gridData: MapGridResponse,
  targetBbox: [number, number, number, number],
  boundaryPolygons: [number, number][][]
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

  // 2. Offscreen grid canvas to capture raw thermal points
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

  // Nearest-neighbor fill for any unassigned pixels
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

  // 3. Main canvas with hardware bilinear upscaling and stencil boundary clipping
  const mainCanvas = document.createElement('canvas');
  const width = 512;
  const height = 512;
  mainCanvas.width = width;
  mainCanvas.height = height;
  const ctx = mainCanvas.getContext('2d');
  if (!ctx) return null;

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

  // Draw bilinear coarse grid scaled to geographic coordinates
  const gx = ((gMinLon - minLon) / (maxLon - minLon)) * width;
  const gy = ((maxLat - gMaxLat) / (maxLat - minLat)) * height;
  const gw = ((gMaxLon - gMinLon) / (maxLon - minLon)) * width;
  const gh = ((gMaxLat - gMinLat) / (maxLat - minLat)) * height;

  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.filter = 'blur(4px)';
  ctx.drawImage(coarseCanvas, gx, gy, gw, gh);

  ctx.restore();

  return mainCanvas;
}

interface CesiumGlobeProps {
  selectedLocation: LocationItem | null;
  gridData: MapGridResponse | null;
  selectedCell: GridCell | null;
  onCellSelect: (cell: GridCell | null) => void;
  isLoading: boolean;
  basemap?: 'osm' | 'dark';
  hoveredCityId: string | null;
  onCityHover: (cityId: string | null) => void;
  onCitySelect: (city: CityData) => void;
}

export const CesiumGlobe: React.FC<CesiumGlobeProps> = ({
  selectedLocation,
  gridData,
  selectedCell,
  onCellSelect,
  isLoading,
  basemap = 'osm',
  hoveredCityId,
  onCityHover,
  onCitySelect,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Cesium.Viewer | null>(null);
  const gridDataSourceRef = useRef<Cesium.CustomDataSource | null>(null);
  const cityBoundaryDataSourceRef = useRef<Cesium.CustomDataSource | null>(null);
  const cityEntitiesRef = useRef<Record<string, Cesium.Entity>>({});
  const heatImageryLayerRef = useRef<Cesium.ImageryLayer | null>(null);
  const basemapLayerRef = useRef<Cesium.ImageryLayer | null>(null);

  const lastHoveredRef = useRef<string | null>(null);
  const lastFlownLocationIdRef = useRef<string | null>(null);
  const gridDataRef = useRef<MapGridResponse | null>(gridData);
  gridDataRef.current = gridData;

  // 1. Initialize Cesium Viewer (runs ONCE on mount)
  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    const baseImagery = ION_TOKEN ? undefined : createImageryProvider(basemap);

    const viewer = new Cesium.Viewer(containerRef.current, {
      baseLayer: baseImagery ? new Cesium.ImageryLayer(baseImagery) : undefined,
      terrainProvider: new Cesium.EllipsoidTerrainProvider(),
      animation: false,
      timeline: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      baseLayerPicker: false,
      navigationHelpButton: false,
      infoBox: false,
      selectionIndicator: false,
      fullscreenButton: false,
    });

    if (viewer.imageryLayers.length > 0) {
      basemapLayerRef.current = viewer.imageryLayers.get(0);
    }

    viewer.scene.globe.enableLighting = false;
    viewer.scene.globe.depthTestAgainstTerrain = false;
    viewer.canvas.style.touchAction = 'none';

    // Initial camera position framing Maharashtra pilot
    viewer.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(76.2, 19.3, 1350000.0),
    });

    // Custom data sources
    const cityDs = new Cesium.CustomDataSource('cityBoundaries');
    viewer.dataSources.add(cityDs);
    cityBoundaryDataSourceRef.current = cityDs;

    const gridDs = new Cesium.CustomDataSource('temperatureGrid');
    viewer.dataSources.add(gridDs);
    gridDataSourceRef.current = gridDs;

    // Create city border entities ONCE to completely avoid recreation and flickering
    const entitiesCache: Record<string, Cesium.Entity> = {};
    const isInitialDark = basemap === 'dark';

    CITIES_DATA.forEach((city) => {
      const cartesianPoints: Cesium.Cartesian3[] = [];

      city.polygonCoordinates.forEach(([lon, lat]) => {
        cartesianPoints.push(Cesium.Cartesian3.fromDegrees(lon, lat));
      });

      // Sleek polyline border
      const borderEntity = cityDs.entities.add({
        id: `border_${city.id}`,
        properties: {
          cityId: city.id,
          cityName: city.name,
        },
        polyline: {
          positions: cartesianPoints,
          width: 1.5,
          material: isInitialDark
            ? Cesium.Color.WHITE.withAlpha(0.28)
            : Cesium.Color.BLACK.withAlpha(0.32),
          clampToGround: true,
        },
      });

      entitiesCache[city.id] = borderEntity;
    });
    cityEntitiesRef.current = entitiesCache;

    // Screen-space event handlers for clicking and hovering
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

    // Left click: select cell or city, and fly smoothly to clicked area
    handler.setInputAction((movement: Cesium.ScreenSpaceEventHandler.PositionedEvent) => {
      let targetCity: CityData | null = null;
      let targetCell: GridCell | null = null;

      // Check geographic coordinates via point-in-polygon
      const coords = getCartographicFromScreen(viewer, movement.position);
      if (coords) {
        targetCity = getCityAtLocation(coords.lat, coords.lon);

        const currentGrid = gridDataRef.current;
        if (currentGrid && currentGrid.cells) {
          targetCell =
            currentGrid.cells.find((c) => {
              if (c.bounds) {
                const [minLat, minLon, maxLat, maxLon] = c.bounds;
                return (
                  coords.lat >= minLat &&
                  coords.lat <= maxLat &&
                  coords.lon >= minLon &&
                  coords.lon <= maxLon
                );
              }
              return (
                Math.abs(c.latitude - coords.lat) <= 0.05 &&
                Math.abs(c.longitude - coords.lon) <= 0.05
              );
            }) ?? null;
        }
      }

      // If clicked inside any city area, fly to it immediately and notify React
      if (targetCity) {
        lastFlownLocationIdRef.current = targetCity.id;
        flyToCity(viewer, targetCity);
        onCitySelect(targetCity);
        onCellSelect(targetCell);
        return;
      }

      if (targetCell) {
        onCellSelect(targetCell);
        return;
      }

      onCellSelect(null);
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    // Mouse move: smooth hover detection anywhere inside city polygon area (NO flicker)
    handler.setInputAction((movement: Cesium.ScreenSpaceEventHandler.MotionEvent) => {
      let hoveredId: string | null = null;

      const coords = getCartographicFromScreen(viewer, movement.endPosition);
      if (coords) {
        const city = getCityAtLocation(coords.lat, coords.lon);
        if (city) {
          hoveredId = city.id;
        }
      }

      // Only notify React when hover target transitions
      if (hoveredId !== lastHoveredRef.current) {
        lastHoveredRef.current = hoveredId;
        onCityHover(hoveredId);
        viewer.canvas.style.cursor = hoveredId ? 'pointer' : 'default';
      }
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

    viewerRef.current = viewer;

    return () => {
      handler.destroy();
      if (!viewer.isDestroyed()) {
        viewer.destroy();
      }
      viewerRef.current = null;
    };
  }, [onCellSelect, onCityHover, onCitySelect]);

  // 2. Ultra-smooth border update on hover (white in dark mode, black in light mode)
  useEffect(() => {
    const cache = cityEntitiesRef.current;
    if (!cache) return;

    const isDarkMode = basemap === 'dark';

    CITIES_DATA.forEach((city) => {
      const borderEntity = cache[city.id];
      if (!borderEntity || !borderEntity.polyline) return;

      const isHovered = hoveredCityId === city.id;
      const isSelected = selectedLocation?.id === city.id;

      if (isHovered) {
        // High-contrast border when hovered: White in Dark mode, Black in Light mode
        borderEntity.polyline.width = new Cesium.ConstantProperty(3.5);
        const highlightColor = isDarkMode ? Cesium.Color.WHITE : Cesium.Color.BLACK;
        borderEntity.polyline.material = new Cesium.ColorMaterialProperty(highlightColor);
      } else if (isSelected) {
        // Selected city border
        borderEntity.polyline.width = new Cesium.ConstantProperty(2.5);
        const selectedColor = isDarkMode
          ? Cesium.Color.WHITE.withAlpha(0.85)
          : Cesium.Color.BLACK.withAlpha(0.85);
        borderEntity.polyline.material = new Cesium.ColorMaterialProperty(selectedColor);
      } else {
        // Subtle resting border
        borderEntity.polyline.width = new Cesium.ConstantProperty(1.5);
        const restingColor = isDarkMode
          ? Cesium.Color.WHITE.withAlpha(0.28)
          : Cesium.Color.BLACK.withAlpha(0.32);
        borderEntity.polyline.material = new Cesium.ColorMaterialProperty(restingColor);
      }
    });
  }, [hoveredCityId, selectedLocation, basemap]);

  // 3. Basemap switching without clearing to 0 layers
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || ION_TOKEN) return;

    const newProvider = createImageryProvider(basemap);
    const newLayer = viewer.imageryLayers.addImageryProvider(newProvider, 0);

    const oldLayer = basemapLayerRef.current;
    if (oldLayer && oldLayer !== newLayer) {
      viewer.imageryLayers.remove(oldLayer);
    }
    basemapLayerRef.current = newLayer;
  }, [basemap]);

  // 4. Camera flight to selected location
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    if (selectedLocation && selectedLocation.id === lastFlownLocationIdRef.current) {
      return;
    }

    lastFlownLocationIdRef.current = selectedLocation ? selectedLocation.id : null;
    viewer.camera.cancelFlight();

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const duration = prefersReducedMotion ? 0 : 1.8;

    if (selectedLocation && selectedLocation.bbox) {
      const [minLat, minLon, maxLat, maxLon] = selectedLocation.bbox;
      const padLat = Math.max(0.04, (maxLat - minLat) * 0.18);
      const padLon = Math.max(0.04, (maxLon - minLon) * 0.18);

      const rect = Cesium.Rectangle.fromDegrees(
        minLon - padLon,
        minLat - padLat,
        maxLon + padLon,
        maxLat + padLat
      );

      viewer.camera.flyTo({
        destination: rect,
        duration,
      });
    } else if (selectedLocation) {
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(
          selectedLocation.longitude,
          selectedLocation.latitude,
          selectedLocation.type === 'city' ? 55000.0 : 400000.0
        ),
        duration,
      });
    } else {
      // Overview
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(76.2, 19.3, 1350000.0),
        duration,
      });
    }
  }, [selectedLocation]);

  // 5A. Render continuous thermal heatmap strictly clipped to city or state boundary
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    // Remove previous heatmap layer
    if (heatImageryLayerRef.current) {
      viewer.imageryLayers.remove(heatImageryLayerRef.current);
      heatImageryLayerRef.current = null;
    }

    if (!gridData || !gridData.cells || gridData.cells.length === 0) {
      return;
    }

    // Determine target bounding box and boundary polygons
    let targetBbox: [number, number, number, number];
    let boundaryPolygons: [number, number][][];

    if (selectedLocation) {
      const city = findCityById(selectedLocation.id);
      if (city) {
        targetBbox = city.bbox;
        boundaryPolygons = [city.polygonCoordinates];
      } else if (selectedLocation.bbox) {
        targetBbox = selectedLocation.bbox;
        boundaryPolygons = [];
      } else {
        targetBbox = [17.8, 72.7, 20.3, 75.2];
        boundaryPolygons = [];
      }
    } else {
      // Overview mode: clip continuous heatmap strictly to active Maharashtra districts
      const pilotCities = CITIES_DATA.filter((c) => {
        if (c.state !== 'Maharashtra') return false;
        const [cMinLat, cMinLon, cMaxLat, cMaxLon] = c.bbox;
        return !(cMaxLat < 17.8 || cMinLat > 20.3 || cMaxLon < 72.7 || cMinLon > 75.2);
      });

      targetBbox = [17.89, 72.75, 20.15, 75.15];
      boundaryPolygons = pilotCities.map((c) => c.polygonCoordinates);
    }

    const canvas = generateContinuousHeatmapCanvas(gridData, targetBbox, boundaryPolygons);
    if (!canvas) return;

    const [minLat, minLon, maxLat, maxLon] = targetBbox;
    const rectangle = Cesium.Rectangle.fromDegrees(minLon, minLat, maxLon, maxLat);

    const heatProvider = new Cesium.SingleTileImageryProvider({
      url: canvas.toDataURL(),
      rectangle,
      tileWidth: 512,
      tileHeight: 512,
    });

    const heatLayer = viewer.imageryLayers.addImageryProvider(heatProvider);
    heatLayer.alpha = 0.82;
    heatImageryLayerRef.current = heatLayer;
  }, [gridData, selectedLocation]);

  // 5B. Render inspected cell reticle outline
  useEffect(() => {
    const dataSource = gridDataSourceRef.current;
    if (!dataSource) return;

    dataSource.entities.removeAll();

    if (selectedCell && selectedCell.bounds) {
      const [minLat, minLon, maxLat, maxLon] = selectedCell.bounds;
      dataSource.entities.add({
        id: `reticle_${selectedCell.id}`,
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArray([
            minLon, minLat,
            maxLon, minLat,
            maxLon, maxLat,
            minLon, maxLat,
            minLon, minLat,
          ]),
          width: 2.5,
          material: Cesium.Color.WHITE,
          clampToGround: true,
        },
      });
    }
  }, [selectedCell]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      {isLoading && (
        <div
          style={{
            position: 'absolute',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(22, 27, 34, 0.9)',
            border: '1px solid #30363d',
            borderRadius: '20px',
            padding: '8px 16px',
            fontSize: '0.85rem',
            color: '#58a6ff',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            zIndex: 10,
          }}
        >
          <span className="spinner" /> Updating City Heat Grid...
        </div>
      )}
    </div>
  );
};

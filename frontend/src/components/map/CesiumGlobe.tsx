import React, { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { GridCell, LocationItem, MapGridResponse } from '../../types/api';
import { getTemperatureHex } from '../../utils/colorScale';
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
  // 1. Pick ellipsoid (fast and reliable on EllipsoidTerrainProvider)
  let cartesian = viewer.camera.pickEllipsoid(position, viewer.scene.globe.ellipsoid);

  // 2. Fallback to ray casting against globe
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
  const lastHoveredRef = useRef<string | null>(null);
  const lastFlownLocationIdRef = useRef<string | null>(null);

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

    viewer.scene.globe.enableLighting = false;
    viewer.scene.globe.depthTestAgainstTerrain = false;

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

      // Sleek polyline border (pure border outline)
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

      // 1. Check picked entity directly
      const picked = viewer.scene.pick(movement.position);
      if (Cesium.defined(picked) && picked.id && picked.id.properties) {
        if (picked.id.properties.cityId) {
          const cId = picked.id.properties.cityId.getValue();
          targetCity = findCityById(cId) ?? null;
        }
        if (picked.id.properties.cellData) {
          targetCell = picked.id.properties.cellData.getValue();
        }
      }

      // 2. If no city picked directly from polyline, check geographic coordinates via point-in-polygon
      if (!targetCity) {
        const coords = getCartographicFromScreen(viewer, movement.position);
        if (coords) {
          targetCity = getCityAtLocation(coords.lat, coords.lon);
        }
      }

      // 3. If clicked inside any city area, fly to it immediately and notify React
      if (targetCity) {
        lastFlownLocationIdRef.current = targetCity.id;
        flyToCity(viewer, targetCity);
        onCitySelect(targetCity);
        if (targetCell) {
          onCellSelect(targetCell);
        } else {
          onCellSelect(null);
        }
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

      // 1. Check direct entity pick (e.g. cursor directly over polyline border)
      const picked = viewer.scene.pick(movement.endPosition);
      if (Cesium.defined(picked) && picked.id && picked.id.properties) {
        if (picked.id.properties.cityId) {
          hoveredId = picked.id.properties.cityId.getValue();
        }
      }

      // 2. If not on border line, check if cursor is anywhere inside the city polygon area
      if (!hoveredId) {
        const coords = getCartographicFromScreen(viewer, movement.endPosition);
        if (coords) {
          const city = getCityAtLocation(coords.lat, coords.lon);
          if (city) {
            hoveredId = city.id;
          }
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

  // 2. Ultra-smooth border update on hover (mutates existing entity properties in place: white in dark mode, black in light mode)
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
        // Selected city border: Crisp white in dark mode, crisp black in light mode
        borderEntity.polyline.width = new Cesium.ConstantProperty(2.5);
        const selectedColor = isDarkMode
          ? Cesium.Color.WHITE.withAlpha(0.85)
          : Cesium.Color.BLACK.withAlpha(0.85);
        borderEntity.polyline.material = new Cesium.ColorMaterialProperty(selectedColor);
      } else {
        // Subtle resting border: Semi-transparent white in dark mode, semi-transparent black in light mode
        borderEntity.polyline.width = new Cesium.ConstantProperty(1.5);
        const restingColor = isDarkMode
          ? Cesium.Color.WHITE.withAlpha(0.28)
          : Cesium.Color.BLACK.withAlpha(0.32);
        borderEntity.polyline.material = new Cesium.ColorMaterialProperty(restingColor);
      }
    });
  }, [hoveredCityId, selectedLocation, basemap]);

  // 3. Basemap switching without clearing to 0 layers (prevents Cesium Ion token prompt)
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || ION_TOKEN) return;

    const newProvider = createImageryProvider(basemap);
    const newLayer = viewer.imageryLayers.addImageryProvider(newProvider);

    setTimeout(() => {
      if (!viewer.isDestroyed()) {
        while (viewer.imageryLayers.length > 1) {
          const oldLayer = viewer.imageryLayers.get(0);
          if (oldLayer !== newLayer) {
            viewer.imageryLayers.remove(oldLayer);
          } else {
            break;
          }
        }
      }
    }, 150);
  }, [basemap]);

  // 4. Camera flight to selected location (for search dropdown or pill navigation)
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    // Skip if flight was already initiated by direct click on the area
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

  // 5. Render city-wise heatmaps (filters ocean cells and applies dynamic thermal normalization)
  useEffect(() => {
    const dataSource = gridDataSourceRef.current;
    if (!dataSource) return;

    dataSource.entities.removeAll();

    if (!gridData || !gridData.cells || gridData.cells.length === 0) {
      return;
    }

    // A. Filter out offshore open ocean cells
    let activeCells = gridData.cells.filter((cell) => {
      if (cell.latitude < 19.35 && cell.longitude < 72.75) {
        return false;
      }
      return true;
    });

    // B. Focus heat grid on city domains
    if (selectedLocation && selectedLocation.bbox) {
      const [minLat, minLon, maxLat, maxLon] = selectedLocation.bbox;
      activeCells = activeCells.filter(
        (c) =>
          c.latitude >= minLat - 0.05 &&
          c.latitude <= maxLat + 0.05 &&
          c.longitude >= minLon - 0.05 &&
          c.longitude <= maxLon + 0.05
      );
    } else {
      activeCells = activeCells.filter((c) =>
        CITIES_DATA.some((city) => {
          const [cMinLat, cMinLon, cMaxLat, cMaxLon] = city.bbox;
          return (
            c.latitude >= cMinLat - 0.12 &&
            c.latitude <= cMaxLat + 0.12 &&
            c.longitude >= cMinLon - 0.12 &&
            c.longitude <= cMaxLon + 0.12
          );
        })
      );
    }

    // C. Dynamic temperature normalization
    const temps = activeCells
      .map((c) => c.value)
      .filter((v): v is number => v !== null);
    const minT = temps.length > 0 ? Math.min(...temps) : 18;
    const maxT = temps.length > 0 ? Math.max(...temps) : 35;

    const isSelected = (c: GridCell) => selectedCell && selectedCell.id === c.id;

    activeCells.forEach((cell) => {
      if (!cell.bounds) return;
      const [minLat, minLon, maxLat, maxLon] = cell.bounds;
      const hexColor =
        cell.value !== null ? getTemperatureHex(cell.value, minT, maxT) : '#4a5568';
      const alpha = isSelected(cell) ? 0.95 : 0.70;
      const outlineColor = isSelected(cell)
        ? Cesium.Color.WHITE
        : Cesium.Color.BLACK.withAlpha(0.2);

      dataSource.entities.add({
        id: cell.id,
        properties: {
          cellData: cell,
        },
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray([
            minLon, minLat,
            maxLon, minLat,
            maxLon, maxLat,
            minLon, maxLat,
          ]),
          material: Cesium.Color.fromCssColorString(hexColor).withAlpha(alpha),
          outline: true,
          outlineColor,
          outlineWidth: isSelected(cell) ? 3 : 1,
          height: 0,
        },
      });
    });
  }, [gridData, selectedCell, selectedLocation]);

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

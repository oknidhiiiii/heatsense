import React, { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { GridCell, LocationItem, MapGridResponse } from '../../types/api';
import {
  CITIES_DATA,
  CityData,
  findCityById,
  getCityAtLocation,
  loadCityBoundariesGeoJSON,
} from '../../utils/cityBoundaries';
import { generateContinuousHeatmapAsync } from '../../utils/heatmapGenerator';

// Set Cesium Ion token if configured
const ION_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN;
if (ION_TOKEN) {
  Cesium.Ion.defaultAccessToken = ION_TOKEN;
}

function createDarkBaseProvider(): Cesium.ImageryProvider {
  return new Cesium.UrlTemplateImageryProvider({
    url: 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    maximumLevel: 16,
    credit: new Cesium.Credit('Tiles (c) Esri (World Dark Gray Base)'),
  });
}

function createDarkReferenceProvider(): Cesium.ImageryProvider {
  return new Cesium.UrlTemplateImageryProvider({
    url: 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
    maximumLevel: 16,
    credit: new Cesium.Credit('Tiles (c) Esri (World Dark Gray Reference)'),
  });
}

function createOsmProvider(): Cesium.ImageryProvider {
  return new Cesium.UrlTemplateImageryProvider({
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    subdomains: ['a', 'b', 'c'],
    maximumLevel: 19,
    credit: new Cesium.Credit('(c) OpenStreetMap contributors'),
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
  const cityBorderEntitiesRef = useRef<Record<string, Cesium.Entity>>({});
  const cityLabelEntitiesRef = useRef<Record<string, Cesium.Entity>>({});
  const heatImageryLayerRef = useRef<Cesium.ImageryLayer | null>(null);
  const basemapLayerRef = useRef<Cesium.ImageryLayer | null>(null);
  const referenceLayerRef = useRef<Cesium.ImageryLayer | null>(null);

  const lastHoveredRef = useRef<string | null>(null);
  const lastFlownLocationIdRef = useRef<string | null>(null);
  const gridDataRef = useRef<MapGridResponse | null>(gridData);
  gridDataRef.current = gridData;

  // 1. Initialize Cesium Viewer (runs ONCE on mount)
  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    // Prefetch high-resolution GeoJSON boundaries in background
    loadCityBoundariesGeoJSON().catch(() => {});

    const viewer = new Cesium.Viewer(containerRef.current, {
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

    if (!ION_TOKEN) {
      if (basemap === 'dark') {
        const baseLayer = viewer.imageryLayers.addImageryProvider(createDarkBaseProvider());
        basemapLayerRef.current = baseLayer;
        const refLayer = viewer.imageryLayers.addImageryProvider(createDarkReferenceProvider());
        referenceLayerRef.current = refLayer;
      } else {
        const baseLayer = viewer.imageryLayers.addImageryProvider(createOsmProvider());
        basemapLayerRef.current = baseLayer;
      }
    }

    viewer.scene.globe.enableLighting = false;
    viewer.scene.globe.depthTestAgainstTerrain = false;
    viewer.scene.globe.tileCacheSize = 100;
    viewer.scene.globe.maximumScreenSpaceError = 2.0;
    viewer.scene.globe.loadingDescendantLimit = 16;
    viewer.scene.globe.preloadAncestors = false;
    viewer.scene.globe.preloadSiblings = false;
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

    // Create city border and label entities with Tiered Spatial Clustering
    const borderEntitiesCache: Record<string, Cesium.Entity> = {};
    const labelEntitiesCache: Record<string, Cesium.Entity> = {};
    const isInitialDark = basemap === 'dark';

    CITIES_DATA.forEach((city) => {
      const cartesianPoints: Cesium.Cartesian3[] = [];

      city.polygonCoordinates.forEach(([lon, lat]) => {
        cartesianPoints.push(Cesium.Cartesian3.fromDegrees(lon, lat));
      });

      // Tiered spatial clustering visibility thresholds
      const isTier1 = city.tier === 1;
      const isTier2 = city.tier === 2;
      const maxMarkerDist = isTier1 ? 5500000.0 : isTier2 ? 2000000.0 : 850000.0;
      const maxLabelDist = isTier1 ? 4000000.0 : isTier2 ? 1600000.0 : 650000.0;
      const fontStr = isTier1
        ? '600 12.5px -apple-system, BlinkMacSystemFont, "SF Pro Text", Inter, sans-serif'
        : isTier2
        ? '600 11.5px -apple-system, BlinkMacSystemFont, "SF Pro Text", Inter, sans-serif'
        : '500 10.5px -apple-system, BlinkMacSystemFont, "SF Pro Text", Inter, sans-serif';
      const pointSize = isTier1 ? 5.5 : isTier2 ? 4.5 : 3.5;

      // 1. Sleek polyline border
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
          distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
            0.0,
            isTier1 ? 5500000.0 : isTier2 ? 2500000.0 : 1200000.0
          ),
        },
      });
      borderEntitiesCache[city.id] = borderEntity;

      // 2. High-contrast tiered city label and anchor marker
      const labelEntity = cityDs.entities.add({
        id: `label_${city.id}`,
        position: Cesium.Cartesian3.fromDegrees(city.longitude, city.latitude),
        properties: {
          cityId: city.id,
          cityName: city.name,
        },
        point: {
          pixelSize: pointSize,
          color: isInitialDark
            ? Cesium.Color.WHITE.withAlpha(0.85)
            : Cesium.Color.BLACK.withAlpha(0.75),
          outlineColor: isInitialDark
            ? Cesium.Color.BLACK.withAlpha(0.8)
            : Cesium.Color.WHITE.withAlpha(0.8),
          outlineWidth: 1.5,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, maxMarkerDist),
        },
        label: {
          text: city.name,
          font: fontStr,
          fillColor: isInitialDark ? Cesium.Color.WHITE : Cesium.Color.BLACK,
          outlineColor: isInitialDark
            ? Cesium.Color.fromCssColorString('rgba(0, 0, 0, 0.9)')
            : Cesium.Color.fromCssColorString('rgba(255, 255, 255, 0.9)'),
          outlineWidth: 3,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -7),
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, maxLabelDist),
          scale: 1.0,
        },
      });
      labelEntitiesCache[city.id] = labelEntity;
    });

    cityBorderEntitiesRef.current = borderEntitiesCache;
    cityLabelEntitiesRef.current = labelEntitiesCache;

    // Screen-space event handlers for clicking and hovering
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

    // Left click: select cell or city, and fly smoothly to clicked area
    handler.setInputAction((movement: Cesium.ScreenSpaceEventHandler.PositionedEvent) => {
      let targetCity: CityData | null = null;
      let targetCell: GridCell | null = null;

      // 1. Check if user clicked directly on a city label/point entity
      const picked = viewer.scene.pick(movement.position);
      if (Cesium.defined(picked) && picked.id && picked.id.properties) {
        if (picked.id.properties.cityId) {
          const cId = picked.id.properties.cityId.getValue();
          targetCity = findCityById(cId) ?? null;
        }
      }

      // 2. If no entity picked directly, check geographic coordinates via point-in-polygon
      const coords = getCartographicFromScreen(viewer, movement.position);
      if (coords) {
        if (!targetCity) {
          targetCity = getCityAtLocation(coords.lat, coords.lon);
        }

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

      // If clicked inside any city area or on city label, fly to it immediately and notify React
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

    // Animation Frame Throttling for Ray-Casting & Hover Detection
    let pendingHoverPos: Cesium.Cartesian2 | null = null;
    let hoverRafId: number | null = null;

    const processHoverThrottled = () => {
      hoverRafId = null;
      if (!pendingHoverPos || viewer.isDestroyed()) return;

      const pos = pendingHoverPos;
      pendingHoverPos = null;

      let hoveredId: string | null = null;

      // Direct entity pick (cursor directly over city label or point)
      const picked = viewer.scene.pick(pos);
      if (Cesium.defined(picked) && picked.id && picked.id.properties) {
        if (picked.id.properties.cityId) {
          hoveredId = picked.id.properties.cityId.getValue();
        }
      }

      // Check if cursor is inside city polygon area
      if (!hoveredId) {
        const coords = getCartographicFromScreen(viewer, pos);
        if (coords) {
          const city = getCityAtLocation(coords.lat, coords.lon);
          if (city) {
            hoveredId = city.id;
          }
        }
      }

      // Notify React only when hover target transitions
      if (hoveredId !== lastHoveredRef.current) {
        lastHoveredRef.current = hoveredId;
        onCityHover(hoveredId);
        viewer.canvas.style.cursor = hoveredId ? 'pointer' : 'default';
      }
    };

    handler.setInputAction((movement: Cesium.ScreenSpaceEventHandler.MotionEvent) => {
      pendingHoverPos = movement.endPosition;
      if (hoverRafId === null) {
        hoverRafId = requestAnimationFrame(processHoverThrottled);
      }
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

    viewerRef.current = viewer;

    return () => {
      if (hoverRafId !== null) {
        cancelAnimationFrame(hoverRafId);
      }
      handler.destroy();
      if (!viewer.isDestroyed()) {
        viewer.destroy();
      }
      viewerRef.current = null;
    };
  }, [onCellSelect, onCityHover, onCitySelect]);

  // 2. High-contrast border & label update on hover (white in dark mode, black in light mode)
  useEffect(() => {
    const borders = cityBorderEntitiesRef.current;
    const labels = cityLabelEntitiesRef.current;
    if (!borders || !labels) return;

    const isDarkMode = basemap === 'dark';

    CITIES_DATA.forEach((city) => {
      const borderEntity = borders[city.id];
      const labelEntity = labels[city.id];

      const isHovered = hoveredCityId === city.id;
      const isSelected = selectedLocation?.id === city.id;

      // Update Border Outline
      if (borderEntity && borderEntity.polyline) {
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
      }

      // Update City Label & Marker
      if (labelEntity) {
        if (labelEntity.label) {
          if (isHovered) {
            labelEntity.label.fillColor = new Cesium.ConstantProperty(
              isDarkMode
                ? Cesium.Color.fromCssColorString('#00f0ff')
                : Cesium.Color.fromCssColorString('#0284c7')
            );
            labelEntity.label.scale = new Cesium.ConstantProperty(1.25);
          } else if (isSelected) {
            labelEntity.label.fillColor = new Cesium.ConstantProperty(
              isDarkMode ? Cesium.Color.WHITE : Cesium.Color.BLACK
            );
            labelEntity.label.scale = new Cesium.ConstantProperty(1.15);
          } else {
            labelEntity.label.fillColor = new Cesium.ConstantProperty(
              isDarkMode ? Cesium.Color.WHITE.withAlpha(0.92) : Cesium.Color.BLACK.withAlpha(0.85)
            );
            labelEntity.label.scale = new Cesium.ConstantProperty(1.0);
          }

          labelEntity.label.outlineColor = new Cesium.ConstantProperty(
            isDarkMode
              ? Cesium.Color.fromCssColorString('rgba(0, 0, 0, 0.9)')
              : Cesium.Color.fromCssColorString('rgba(255, 255, 255, 0.9)')
          );
        }

        if (labelEntity.point) {
          if (isHovered || isSelected) {
            labelEntity.point.pixelSize = new Cesium.ConstantProperty(7);
            labelEntity.point.color = new Cesium.ConstantProperty(
              isDarkMode
                ? Cesium.Color.fromCssColorString('#00f0ff')
                : Cesium.Color.fromCssColorString('#0284c7')
            );
          } else {
            const isTier1 = city.tier === 1;
            const isTier2 = city.tier === 2;
            const defaultSize = isTier1 ? 5.5 : isTier2 ? 4.5 : 3.5;
            labelEntity.point.pixelSize = new Cesium.ConstantProperty(defaultSize);
            labelEntity.point.color = new Cesium.ConstantProperty(
              isDarkMode ? Cesium.Color.WHITE.withAlpha(0.85) : Cesium.Color.BLACK.withAlpha(0.75)
            );
          }
        }
      }
    });
  }, [hoveredCityId, selectedLocation, basemap]);

  // 3. Basemap switching without clearing to 0 layers
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || ION_TOKEN) return;

    if (basemap === 'dark') {
      const newBaseProvider = createDarkBaseProvider();
      const newBaseLayer = viewer.imageryLayers.addImageryProvider(newBaseProvider, 0);

      const oldBase = basemapLayerRef.current;
      if (oldBase && oldBase !== newBaseLayer) {
        viewer.imageryLayers.remove(oldBase);
      }
      basemapLayerRef.current = newBaseLayer;

      // Add dark reference layer for city and road labels
      if (!referenceLayerRef.current) {
        const refProvider = createDarkReferenceProvider();
        const refLayer = viewer.imageryLayers.addImageryProvider(refProvider);
        referenceLayerRef.current = refLayer;
      }
    } else {
      const newBaseProvider = createOsmProvider();
      const newBaseLayer = viewer.imageryLayers.addImageryProvider(newBaseProvider, 0);

      const oldBase = basemapLayerRef.current;
      if (oldBase && oldBase !== newBaseLayer) {
        viewer.imageryLayers.remove(oldBase);
      }
      basemapLayerRef.current = newBaseLayer;

      // Remove dark reference layer in OSM mode
      if (referenceLayerRef.current) {
        viewer.imageryLayers.remove(referenceLayerRef.current);
        referenceLayerRef.current = null;
      }
    }
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

  // 5A. Render continuous thermal heatmap with Web Worker, Adaptive LOD, LRU Cache, and Layer Cross-Fade
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    if (!gridData || !gridData.cells || gridData.cells.length === 0) {
      if (heatImageryLayerRef.current) {
        viewer.imageryLayers.remove(heatImageryLayerRef.current);
        heatImageryLayerRef.current = null;
      }
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

    let isSubscribed = true;
    const cameraHeight = viewer.camera.positionCartographic?.height || 800000.0;
    const regionId = selectedLocation ? selectedLocation.id : 'overview_MH';
    const validAt = gridData.valid_at || 'latest';
    const layer = gridData.layer || 'temp';

    generateContinuousHeatmapAsync(gridData, targetBbox, boundaryPolygons, cameraHeight, {
      regionId,
      layer,
      validAt,
      theme: basemap,
    }).then((raster) => {
      if (!isSubscribed || !raster || viewer.isDestroyed()) return;

      const [minLat, minLon, maxLat, maxLon] = targetBbox;
      const rectangle = Cesium.Rectangle.fromDegrees(minLon, minLat, maxLon, maxLat);

      const heatProvider = new Cesium.SingleTileImageryProvider({
        url: raster.dataUrl,
        rectangle,
        tileWidth: raster.width,
        tileHeight: raster.height,
      });

      const newHeatLayer = viewer.imageryLayers.addImageryProvider(heatProvider);
      const oldHeatLayer = heatImageryLayerRef.current;
      heatImageryLayerRef.current = newHeatLayer;

      // Raise reference layer above heatmap so city labels and roads remain sharp
      if (referenceLayerRef.current) {
        viewer.imageryLayers.raiseToTop(referenceLayerRef.current);
      }

      // Smooth 250ms Layer Cross-Fade Transition
      const startTime = performance.now();
      const crossFadeDuration = 250;
      const targetAlpha = 0.82;
      newHeatLayer.alpha = 0.0;

      const animateCrossFade = (currentTime: number) => {
        if (viewer.isDestroyed()) return;
        const elapsed = currentTime - startTime;
        const progress = Math.min(1.0, elapsed / crossFadeDuration);
        const ease = 1 - Math.pow(1 - progress, 3); // Cubic ease out

        newHeatLayer.alpha = ease * targetAlpha;
        if (oldHeatLayer) {
          oldHeatLayer.alpha = (1.0 - ease) * targetAlpha;
        }

        if (progress < 1.0) {
          requestAnimationFrame(animateCrossFade);
        } else {
          if (oldHeatLayer && !viewer.isDestroyed()) {
            viewer.imageryLayers.remove(oldHeatLayer);
          }
          newHeatLayer.alpha = targetAlpha;
        }
      };

      requestAnimationFrame(animateCrossFade);
    });

    return () => {
      isSubscribed = false;
    };
  }, [gridData, selectedLocation, basemap]);

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

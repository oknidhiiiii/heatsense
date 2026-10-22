import React, { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { GridCell, LocationItem, MapGridResponse } from '../../types/api';
import { getTemperatureHex } from '../../utils/colorScale';

// Set Cesium Ion token if configured
const ION_TOKEN = import.meta.env.VITE_CESIUM_ION_TOKEN;
if (ION_TOKEN) {
  Cesium.Ion.defaultAccessToken = ION_TOKEN;
}

interface CesiumGlobeProps {
  selectedLocation: LocationItem | null;
  gridData: MapGridResponse | null;
  selectedCell: GridCell | null;
  onCellSelect: (cell: GridCell | null) => void;
  isLoading: boolean;
}

export const CesiumGlobe: React.FC<CesiumGlobeProps> = ({
  selectedLocation,
  gridData,
  selectedCell,
  onCellSelect,
  isLoading,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Cesium.Viewer | null>(null);
  const entityCollectionRef = useRef<Cesium.CustomDataSource | null>(null);

  // 1. Initialize Cesium Viewer
  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    // Use token-free Carto Dark Matter imagery provider by default
    const baseImagery = ION_TOKEN
      ? undefined
      : new Cesium.UrlTemplateImageryProvider({
          url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
          subdomains: ['a', 'b', 'c', 'd'],
          maximumLevel: 19,
          credit: new Cesium.Credit('© OpenStreetMap contributors, © CARTO'),
        });

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

    // Initial camera position framing India
    viewer.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(78.9629, 20.5937, 7500000.0),
    });

    // Custom data source for temperature grid polygons
    const gridDataSource = new Cesium.CustomDataSource('temperatureGrid');
    viewer.dataSources.add(gridDataSource);
    entityCollectionRef.current = gridDataSource;

    // Screen-space click handler for picking grid cells
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((movement: Cesium.ScreenSpaceEventHandler.PositionedEvent) => {
      const pickedObject = viewer.scene.pick(movement.position);
      if (Cesium.defined(pickedObject) && pickedObject.id && pickedObject.id.properties) {
        const cellData: GridCell = pickedObject.id.properties.cellData.getValue();
        onCellSelect(cellData);
      } else {
        onCellSelect(null);
      }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    viewerRef.current = viewer;

    return () => {
      handler.destroy();
      if (!viewer.isDestroyed()) {
        viewer.destroy();
      }
      viewerRef.current = null;
    };
  }, [onCellSelect]);

  // 2. Camera flight to selected location
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    // Cancel any existing flight so fast clicks don't conflict
    viewer.camera.cancelFlight();

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const duration = prefersReducedMotion ? 0 : 1.8;

    if (selectedLocation && selectedLocation.bbox) {
      const [minLat, minLon, maxLat, maxLon] = selectedLocation.bbox;
      // Add slight padding to the rectangle
      const padLat = Math.max(0.08, (maxLat - minLat) * 0.25);
      const padLon = Math.max(0.08, (maxLon - minLon) * 0.25);

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
          selectedLocation.type === 'city' ? 60000.0 : 400000.0
        ),
        duration,
      });
    } else {
      // Return to India overview
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(78.9629, 20.5937, 7500000.0),
        duration,
      });
    }
  }, [selectedLocation]);

  // 3. Render temperature grid cells on globe
  useEffect(() => {
    const dataSource = entityCollectionRef.current;
    if (!dataSource) return;

    dataSource.entities.removeAll();

    if (!gridData || !gridData.cells || gridData.cells.length === 0) {
      return;
    }

    const isSelected = (c: GridCell) => selectedCell && selectedCell.id === c.id;

    gridData.cells.forEach((cell) => {
      if (!cell.bounds) return;
      const [minLat, minLon, maxLat, maxLon] = cell.bounds;
      const hexColor = cell.value !== null ? getTemperatureHex(cell.value) : '#4a5568';
      const alpha = isSelected(cell) ? 0.95 : 0.65;
      const outlineColor = isSelected(cell) ? Cesium.Color.WHITE : Cesium.Color.BLACK.withAlpha(0.2);

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
  }, [gridData, selectedCell]);

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
          <span className="spinner" /> Updating Heat Grid...
        </div>
      )}
    </div>
  );
};

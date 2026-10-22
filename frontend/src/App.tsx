import React, { useEffect, useState, useCallback } from 'react';
import './App.css';
import { api } from './services/api';
import {
  GridCell,
  HealthResponse,
  LayerType,
  LocationItem,
  MapGridResponse,
} from './types/api';
import { Header } from './components/controls/Header';
import { CesiumGlobe } from './components/map/CesiumGlobe';
import { Legend } from './components/map/Legend';
import { HistoryChart } from './components/charts/HistoryChart';
import { CellInspector } from './components/inspector/CellInspector';
import { MetricsModal } from './components/models/MetricsModal';
import { CityData } from './utils/cityBoundaries';

export const App: React.FC = () => {
  const [selectedLocation, setSelectedLocation] = useState<LocationItem | null>(null);
  const [activeLayer, setActiveLayer] = useState<LayerType>('forecast24');
  const [gridData, setGridData] = useState<MapGridResponse | null>(null);
  const [selectedCell, setSelectedCell] = useState<GridCell | null>(null);
  const [isLoadingGrid, setIsLoadingGrid] = useState(false);
  const [isMetricsOpen, setIsMetricsOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [basemap, setBasemap] = useState<'osm' | 'dark'>('osm');
  const [hoveredCityId, setHoveredCityId] = useState<string | null>(null);

  // Check backend health on startup
  useEffect(() => {
    api.getHealth()
      .then(setHealth)
      .catch(() => {});
  }, []);

  // Fetch regional map grid whenever layer or selected location changes
  useEffect(() => {
    const controller = new AbortController();
    setIsLoadingGrid(true);

    const regionId = selectedLocation ? selectedLocation.id : 'state_IN_MH';
    const bbox = selectedLocation?.bbox;

    api.getGridLayer(regionId, activeLayer, bbox, controller.signal)
      .then((data) => {
        setGridData(data);
        setIsLoadingGrid(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setIsLoadingGrid(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [activeLayer, selectedLocation]);

  const handleCellSelect = useCallback((cell: GridCell | null) => {
    setSelectedCell(cell);
  }, []);

  const handleCitySelect = useCallback((city: CityData) => {
    setSelectedLocation({
      id: city.id,
      name: city.name,
      type: 'city',
      country_code: 'IN',
      admin1: city.state,
      latitude: city.latitude,
      longitude: city.longitude,
      bbox: city.bbox,
      coverage_status: 'supported',
    });
    setSelectedCell(null);
  }, []);

  const activeLat = selectedCell?.latitude ?? selectedLocation?.latitude ?? 18.93;
  const activeLon = selectedCell?.longitude ?? selectedLocation?.longitude ?? 72.83;
  const activeName = selectedCell
    ? `Grid Cell ${selectedCell.id}`
    : selectedLocation?.name ?? 'Mumbai Region';

  return (
    <div className="app-container">
      <Header
        health={health}
        selectedLocation={selectedLocation}
        onSelectLocation={(loc) => {
          setSelectedLocation(loc);
          setSelectedCell(null);
        }}
        activeLayer={activeLayer}
        onSelectLayer={setActiveLayer}
        onOpenMetrics={() => setIsMetricsOpen(true)}
        basemap={basemap}
        onToggleBasemap={() => setBasemap((b) => (b === 'osm' ? 'dark' : 'osm'))}
        hoveredCityId={hoveredCityId}
        onCityHover={setHoveredCityId}
      />

      <main className="main-content">
        <CesiumGlobe
          selectedLocation={selectedLocation}
          gridData={gridData}
          selectedCell={selectedCell}
          onCellSelect={handleCellSelect}
          isLoading={isLoadingGrid}
          basemap={basemap}
          hoveredCityId={hoveredCityId}
          onCityHover={setHoveredCityId}
          onCitySelect={handleCitySelect}
        />

        <Legend layer={activeLayer} gridData={gridData} />

        <CellInspector
          cell={selectedCell}
          layer={activeLayer}
          gridData={gridData}
          onClose={() => setSelectedCell(null)}
        />

        <div className="bottom-chart-dock">
          <HistoryChart
            latitude={activeLat}
            longitude={activeLon}
            locationName={activeName}
          />
        </div>
      </main>

      <MetricsModal
        isOpen={isMetricsOpen}
        onClose={() => setIsMetricsOpen(false)}
      />
    </div>
  );
};
export default App;

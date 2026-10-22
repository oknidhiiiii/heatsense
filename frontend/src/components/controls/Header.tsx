import React, { useState, useEffect, useRef } from 'react';
import { Search, RotateCcw, BarChart2, Layers } from 'lucide-react';
import { LocationItem, LayerType, HealthResponse } from '../../types/api';
import { api } from '../../services/api';
import { CITIES_DATA } from '../../utils/cityBoundaries';

interface HeaderProps {
  health: HealthResponse | null;
  selectedLocation: LocationItem | null;
  onSelectLocation: (loc: LocationItem | null) => void;
  activeLayer: LayerType;
  onSelectLayer: (layer: LayerType) => void;
  onOpenMetrics: () => void;
  basemap: 'osm' | 'dark';
  onToggleBasemap: () => void;
  hoveredCityId: string | null;
  onCityHover: (cityId: string | null) => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  selectedLocation,
  onSelectLocation,
  activeLayer,
  onSelectLayer,
  onOpenMetrics,
  basemap,
  onToggleBasemap,
  hoveredCityId,
  onCityHover,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<LocationItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSuggestions([]);
      return;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => {
      api.searchLocations(searchQuery.trim(), 6, controller.signal)
        .then((res) => {
          setSuggestions(res.items);
          setIsOpen(true);
        })
        .catch(() => {});
    }, 200);

    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [searchQuery]);

  // Click outside listener to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="apple-floating-chrome">
      {/* 1. Left Island: Search & City Exploration */}
      <div className="apple-search-island" ref={searchRef}>
        <div className="island-brand-row">
          <div className="brand-badge-group">
            <span className="brand-wordmark">HeatSense</span>
            <span className="brand-dot-live" title="Inference Engine Active" />
          </div>
          {health?.model_loaded && (
            <span className="ml-status-text">AI Pilot Active</span>
          )}
        </div>

        <div className="search-bar-pill">
          <Search size={15} className="search-pill-icon" />
          <input
            type="text"
            className="search-pill-input"
            placeholder="Search Indian city or region..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => suggestions.length > 0 && setIsOpen(true)}
          />
          {selectedLocation && (
            <button
              className="search-pill-clear"
              onClick={() => {
                setSearchQuery('');
                onSelectLocation(null);
              }}
              title="Recenter Overview"
            >
              <RotateCcw size={13} />
            </button>
          )}
        </div>

        {isOpen && suggestions.length > 0 && (
          <div className="apple-suggestions-menu">
            {suggestions.map((loc) => (
              <div
                key={loc.id}
                className={`suggestion-row ${hoveredCityId === loc.id ? 'active' : ''}`}
                onClick={() => {
                  onSelectLocation(loc);
                  setSearchQuery(loc.name);
                  setIsOpen(false);
                  onCityHover(null);
                }}
                onMouseEnter={() => onCityHover(loc.id)}
                onMouseLeave={() => onCityHover(null)}
              >
                <div className="loc-text-group">
                  <span className="loc-primary-name">{loc.name}</span>
                  <span className="loc-secondary-meta">
                    {[loc.admin1, loc.country_code].filter(Boolean).join(', ')}
                  </span>
                </div>
                <span className={`status-pill ${loc.coverage_status}`}>
                  {loc.coverage_status === 'supported' ? 'Supported' : 'Out of Pilot'}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Minimalist City Pills */}
        <div className="city-pill-strip">
          <button
            className={`pill-item ${!selectedLocation ? 'selected' : ''}`}
            onClick={() => {
              setSearchQuery('');
              onSelectLocation(null);
            }}
            onMouseEnter={() => onCityHover(null)}
          >
            All Cities
          </button>
          {CITIES_DATA.map((city) => (
            <button
              key={city.id}
              className={`pill-item ${selectedLocation?.id === city.id ? 'selected' : ''} ${
                hoveredCityId === city.id ? 'hovered' : ''
              }`}
              onClick={() => {
                onSelectLocation({
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
                setSearchQuery(city.name);
              }}
              onMouseEnter={() => onCityHover(city.id)}
              onMouseLeave={() => onCityHover(null)}
            >
              {city.name}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Right Island: iOS Segmented Controller & Utility Actions */}
      <div className="apple-control-island">
        <div className="ios-segmented-control">
          <button
            className={`seg-tab ${activeLayer === 'historical' ? 'active' : ''}`}
            onClick={() => onSelectLayer('historical')}
          >
            Historical
          </button>
          <button
            className={`seg-tab ${activeLayer === 'forecast24' ? 'active' : ''}`}
            onClick={() => onSelectLayer('forecast24')}
          >
            +24h Forecast
          </button>
          <button
            className={`seg-tab ${activeLayer === 'forecast48' ? 'active' : ''}`}
            onClick={() => onSelectLayer('forecast48')}
          >
            +48h Forecast
          </button>
        </div>

        <div className="utility-cluster">
          <button
            className="glass-action-btn"
            onClick={onToggleBasemap}
            title={`Basemap: ${basemap === 'osm' ? 'OpenStreetMap Standard' : 'Carto Dark'}`}
          >
            <Layers size={15} />
            <span>{basemap === 'osm' ? 'Standard' : 'Dark'}</span>
          </button>

          <button
            className="glass-action-btn"
            onClick={onOpenMetrics}
            title="Inspect Model Card and Verification Metrics"
          >
            <BarChart2 size={15} />
            <span>Model Specs</span>
          </button>
        </div>
      </div>
    </div>
  );
};

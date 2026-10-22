import React, { useState, useEffect, useRef } from 'react';
import { Search, RotateCcw, BarChart2, Map } from 'lucide-react';
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
    <header className="app-header">
      <div className="brand-section">
        <span className="brand-title">HeatSense</span>
        <span className="brand-badge">India Pilot</span>
        {health && (
          <span
            className="brand-badge"
            style={{
              color: health.model_loaded ? '#3fb950' : '#d29922',
              borderColor: health.model_loaded ? 'rgba(63, 185, 80, 0.3)' : 'rgba(210, 153, 34, 0.3)',
            }}
          >
            {health.model_loaded ? 'ML Online' : 'Connecting'}
          </span>
        )}
      </div>

      {/* Location Search Bar with City Chips */}
      <div className="search-and-chips-container">
        <div className="search-container" ref={searchRef}>
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search city (e.g. Mumbai, Pune, Thane, Nashik)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => suggestions.length > 0 && setIsOpen(true)}
            />
            {selectedLocation && (
              <button
                className="clear-button"
                onClick={() => {
                  setSearchQuery('');
                  onSelectLocation(null);
                }}
                title="Return to Regional Overview"
              >
                <RotateCcw size={14} />
              </button>
            )}
          </div>

          {isOpen && suggestions.length > 0 && (
            <ul className="suggestions-dropdown">
              {suggestions.map((loc) => (
                <li
                  key={loc.id}
                  className={`suggestion-item ${hoveredCityId === loc.id ? 'highlighted' : ''}`}
                  onClick={() => {
                    onSelectLocation(loc);
                    setSearchQuery(loc.name);
                    setIsOpen(false);
                    onCityHover(null);
                  }}
                  onMouseEnter={() => onCityHover(loc.id)}
                  onMouseLeave={() => onCityHover(null)}
                >
                  <div className="loc-name-col">
                    <span className="loc-name">{loc.name}</span>
                    <span className="loc-admin">
                      {[loc.admin1, loc.country_code].filter(Boolean).join(', ')}
                    </span>
                  </div>
                  <span className={`badge-coverage ${loc.coverage_status}`}>
                    {loc.coverage_status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Quick City Selector Chips with Hover Outlining */}
        <div className="city-chips-bar">
          <button
            className={`city-chip ${!selectedLocation ? 'active' : ''}`}
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
              className={`city-chip ${selectedLocation?.id === city.id ? 'active' : ''} ${
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

      {/* Layer Controls & Basemap Switcher */}
      <div className="layer-controls">
        <div className="layer-button-group">
          <button
            className={`layer-btn ${activeLayer === 'historical' ? 'active' : ''}`}
            onClick={() => onSelectLayer('historical')}
          >
            Historical
          </button>
          <button
            className={`layer-btn ${activeLayer === 'forecast24' ? 'active' : ''}`}
            onClick={() => onSelectLayer('forecast24')}
          >
            Forecast +24h
          </button>
          <button
            className={`layer-btn ${activeLayer === 'forecast48' ? 'active' : ''}`}
            onClick={() => onSelectLayer('forecast48')}
          >
            Forecast +48h
          </button>
        </div>

        <button
          className="basemap-toggle-btn"
          onClick={onToggleBasemap}
          title={`Switch basemap (current: ${basemap === 'osm' ? 'OpenStreetMap Standard' : 'Carto Dark'})`}
        >
          <Map size={15} />
          <span>{basemap === 'osm' ? 'OSM Standard' : 'OSM Dark'}</span>
        </button>

        <button className="metrics-btn" onClick={onOpenMetrics} title="View Model Card & Evaluation Metrics">
          <BarChart2 size={16} />
          <span>Model Specs</span>
        </button>
      </div>
    </header>
  );
};

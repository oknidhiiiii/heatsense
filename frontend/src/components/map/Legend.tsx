import React from 'react';
import { LayerType, MapGridResponse } from '../../types/api';
import { COLOR_STOPS } from '../../utils/colorScale';

interface LegendProps {
  layer: LayerType;
  gridData: MapGridResponse | null;
}

export const Legend: React.FC<LegendProps> = ({ layer, gridData }) => {
  const getLayerLabel = () => {
    switch (layer) {
      case 'historical':
        return 'Historical Reanalysis (ERA5-Land)';
      case 'forecast24':
        return 'HeatSense Prediction (+24h)';
      case 'forecast48':
        return 'HeatSense Prediction (+48h)';
      default:
        return 'HeatSense Temperature';
    }
  };

  const gradientString = `linear-gradient(to right, ${COLOR_STOPS.map((s) => s.hex).join(', ')})`;

  return (
    <div className="legend-container">
      <div className="legend-header">
        <span className="legend-title">{getLayerLabel()}</span>
        <span className="legend-unit">°C</span>
      </div>

      <div className="legend-bar-wrapper">
        <div className="legend-bar" style={{ background: gradientString }} />
        <div className="legend-labels">
          {COLOR_STOPS.map((stop) => (
            <span key={stop.temp} className="legend-tick">
              {stop.temp}°
            </span>
          ))}
        </div>
      </div>

      {gridData && (
        <div className="legend-meta">
          <div>
            <span className="meta-label">Valid Time:</span>{' '}
            <span className="meta-val">{new Date(gridData.valid_at).toLocaleString()}</span>
          </div>
          {gridData.initialized_at && (
            <div>
              <span className="meta-label">Initialized:</span>{' '}
              <span className="meta-val">{new Date(gridData.initialized_at).toLocaleString()}</span>
            </div>
          )}
          <div>
            <span className="meta-label">Resolution:</span>{' '}
            <span className="meta-val">~9 km (0.1°)</span>
          </div>
        </div>
      )}
    </div>
  );
};

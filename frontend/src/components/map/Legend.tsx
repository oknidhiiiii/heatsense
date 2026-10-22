import React from 'react';
import { LayerType, MapGridResponse } from '../../types/api';

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

  // Compute actual min and max across cells
  const temps = (gridData?.cells || [])
    .map((c) => c.value)
    .filter((v): v is number => v !== null);

  const minVal = temps.length > 0 ? Math.round(Math.min(...temps) * 10) / 10 : 18;
  const maxVal = temps.length > 0 ? Math.round(Math.max(...temps) * 10) / 10 : 38;
  const midVal = Math.round(((minVal + maxVal) / 2) * 10) / 10;

  // Vibrant thermal gradient matching dynamic normalization
  const gradientString =
    'linear-gradient(to right, #10b981 0%, #84cc16 20%, #eab308 40%, #f97316 60%, #ef4444 80%, #d946ef 100%)';

  return (
    <div className="legend-container">
      <div className="legend-header">
        <span className="legend-title">{getLayerLabel()}</span>
        <span className="legend-unit">°C</span>
      </div>

      <div className="legend-bar-wrapper">
        <div className="legend-bar" style={{ background: gradientString }} />
        <div className="legend-labels">
          <span className="legend-tick">{minVal}° (Cool)</span>
          <span className="legend-tick">{midVal}° (Moderate)</span>
          <span className="legend-tick">{maxVal}° (Heat Island)</span>
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
            <span className="meta-val">~9 km (City Heatmap)</span>
          </div>
        </div>
      )}
    </div>
  );
};

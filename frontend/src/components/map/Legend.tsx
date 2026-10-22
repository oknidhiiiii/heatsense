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
        return 'Observed Historical';
      case 'forecast24':
        return '+24h Temperature Forecast';
      case 'forecast48':
        return '+48h Temperature Forecast';
      default:
        return 'Thermal Index';
    }
  };

  const temps = (gridData?.cells || [])
    .map((c) => c.value)
    .filter((v): v is number => v !== null);

  const minVal = temps.length > 0 ? Math.round(Math.min(...temps) * 10) / 10 : 18;
  const maxVal = temps.length > 0 ? Math.round(Math.max(...temps) * 10) / 10 : 38;
  const midVal = Math.round(((minVal + maxVal) / 2) * 10) / 10;

  const gradientString =
    'linear-gradient(to right, #10b981 0%, #84cc16 22%, #eab308 45%, #f97316 68%, #ef4444 86%, #d946ef 100%)';

  return (
    <div className="apple-legend-pill">
      <div className="legend-title-row">
        <span className="legend-heading">{getLayerLabel()}</span>
        <span className="legend-temp-span">
          {minVal}° to {maxVal}°C
        </span>
      </div>

      <div className="legend-gradient-track" style={{ background: gradientString }} />

      <div className="legend-ticks-row">
        <span className="tick-label">Cool</span>
        <span className="tick-label">{midVal}°C</span>
        <span className="tick-label">Heat Island</span>
      </div>
    </div>
  );
};

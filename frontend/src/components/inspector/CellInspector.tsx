import React from 'react';
import { X, Thermometer, MapPin } from 'lucide-react';
import { GridCell, LayerType, MapGridResponse } from '../../types/api';
import { getTemperatureHex } from '../../utils/colorScale';
import { formatToIST } from '../../utils/timeFormat';

interface CellInspectorProps {
  cell: GridCell | null;
  layer: LayerType;
  gridData: MapGridResponse | null;
  onClose: () => void;
}

export const CellInspector: React.FC<CellInspectorProps> = ({
  cell,
  layer,
  gridData,
  onClose,
}) => {
  if (!cell) return null;

  const color = cell.value !== null ? getTemperatureHex(cell.value) : '#94a3b8';

  const getSourceDetails = () => {
    if (layer === 'historical') {
      return {
        name: 'ERA5-Land Hourly Reanalysis',
        version: 'Copernicus C3S (v1)',
      };
    }
    return {
      name: gridData?.model_id || 'HeatSense ML Regressor',
      version: gridData?.model_version || 'v1',
    };
  };

  const source = getSourceDetails();

  return (
    <div className="apple-inspector-sheet">
      <div className="inspector-sheet-header">
        <div className="sheet-title-col">
          <div className="sheet-pin-row">
            <MapPin size={15} className="pin-accent" />
            <span className="sheet-cell-title">Sector {cell.id}</span>
          </div>
          <span className="sheet-coords">
            {cell.latitude.toFixed(2)}°N, {cell.longitude.toFixed(2)}°E
          </span>
        </div>
        <button className="sheet-close-btn" onClick={onClose} title="Close Detail">
          <X size={15} />
        </button>
      </div>

      <div className="inspector-sheet-body">
        <div className="hero-metric-row">
          <div className="hero-temp-block" style={{ color }}>
            <Thermometer size={24} />
            <span className="hero-temp-val">
              {cell.value !== null ? `${cell.value.toFixed(1)}°C` : 'No Data'}
            </span>
          </div>
          <span className="hero-layer-pill">
            {layer === 'historical'
              ? 'Observed'
              : layer === 'forecast24'
              ? '+24h Forecast'
              : '+48h Forecast'}
          </span>
        </div>

        <div className="spec-grid-lux">
          <div className="spec-cell">
            <span className="spec-k">Native Spacing</span>
            <span className="spec-v">~9 km (0.1°)</span>
          </div>
          <div className="spec-cell">
            <span className="spec-k">Provider</span>
            <span className="spec-v">{source.name}</span>
          </div>
          <div className="spec-cell">
            <span className="spec-k">Release</span>
            <span className="spec-v">{source.version}</span>
          </div>
          <div className="spec-cell">
            <span className="spec-k">Data Quality</span>
            <span className="spec-v">Verified Nominal</span>
          </div>
          {gridData?.valid_at && (
            <div className="spec-cell full-width">
              <span className="spec-k">Observation Time (IST)</span>
              <span className="spec-v">{formatToIST(gridData.valid_at).fullDateTimeIST}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

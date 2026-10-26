import React, { useEffect, useState } from 'react';
import { X, CheckCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import { ModelMetric } from '../../types/api';
import { api } from '../../services/api';
import { formatToIST } from '../../utils/timeFormat';

interface MetricsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MetricsModal: React.FC<MetricsModalProps> = ({ isOpen, onClose }) => {
  const [metrics, setMetrics] = useState<ModelMetric[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    const controller = new AbortController();
    setLoading(true);
    setError(null);

    api.getModelMetrics(controller.signal)
      .then((res) => {
        setMetrics(res.items);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Failed to load model metrics');
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <ShieldCheck size={22} className="modal-icon" />
            <div>
              <h3>HeatSense ML Model Card & Verification</h3>
              <span className="modal-subtitle">Direct Multi-Horizon Evaluated on Held-Out Test Windows</span>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="modal-loading">Loading saved evaluation report...</div>
          ) : error ? (
            <div className="modal-error">{error}</div>
          ) : (
            <>
              <div className="metrics-summary-banner">
                <CheckCircle size={18} className="text-green" />
                <span>
                  All predictions are produced exclusively by HeatSense-trained models. No external weather forecasts are used as inputs or silent replacements.
                </span>
              </div>

              <div className="table-responsive">
                <table className="metrics-table">
                  <thead>
                    <tr>
                      <th>Horizon</th>
                      <th>Model ID</th>
                      <th>Metric</th>
                      <th>Test Value</th>
                      <th>Baseline (Diurnal)</th>
                      <th>Test Window</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.map((m, idx) => (
                      <tr key={idx}>
                        <td>
                          <span className="horizon-tag">+{m.horizon_hours}h</span>
                        </td>
                        <td className="code-font">{m.model_id}</td>
                        <td className="font-semibold">{m.metric_name.toUpperCase()}</td>
                        <td className="metric-val">
                          {m.metric_value.toFixed(3)} {m.unit}
                        </td>
                        <td className="baseline-val">
                          {m.baseline_value !== undefined && m.baseline_value !== null
                            ? `${m.baseline_value.toFixed(3)} ${m.unit}`
                            : 'N/A'}
                        </td>
                        <td className="date-font">
                          {formatToIST(m.test_start).shortDate} to {formatToIST(m.test_end).shortDate}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="limitations-callout">
                <AlertTriangle size={18} className="text-yellow" />
                <div>
                  <strong>Operational Forecasting Constraints:</strong>
                  <p>
                    Reanalysis models do not have access to future atmospheric radiation or synoptic fronts. HeatSense forecasts utilize causal temperature lags and solar geometry to forecast short-term diurnal curves without future leakage.
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import './App.css';
import { api } from './services/api';
import { HealthResponse } from './types/api';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    api.getHealth(controller.signal)
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Failed to connect to HeatSense API');
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="brand-section">
          <span className="brand-title">HeatSense</span>
          <span className="brand-badge">India Pilot v0.1</span>
        </div>

        <div className="header-status">
          <div className="status-indicator">
            <span
              className={`status-dot ${loading ? 'loading' : error ? 'error' : ''}`}
              title={error ? error : loading ? 'Checking API...' : 'API Operational'}
            />
            <span>
              {loading
                ? 'Connecting API...'
                : error
                ? 'API Disconnected'
                : `API v${health?.version || '0.1.0'} (Active)`}
            </span>
          </div>
          {health && (
            <span className="brand-badge">
              Regions: {health.supported_regions.join(', ')}
            </span>
          )}
        </div>
      </header>

      <main className="main-content">
        <div className="map-placeholder-view">
          <div className="map-card">
            <h2>HeatSense Geospatial Intelligence</h2>
            <p>
              Interactive heat intelligence platform combining historical climate reanalysis (ERA5-Land)
              and HeatSense-trained ML models for +24h and +48h temperature forecasting.
            </p>

            <div className="feature-grid">
              <div className="feature-item">
                <div className="title">Target Geography</div>
                <div className="value">India (Maharashtra Pilot Domain)</div>
              </div>
              <div className="feature-item">
                <div className="title">Forecast Horizons</div>
                <div className="value">+24h & +48h Air Temp (°C)</div>
              </div>
              <div className="feature-item">
                <div className="title">Model Engine</div>
                <div className="value">Random Forest & XGBoost</div>
              </div>
              <div className="feature-item">
                <div className="title">Grid Resolution</div>
                <div className="value">~9 km (0.1° ERA5-Land Native)</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;

import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { HistoricalPoint, HistoricalResponse } from '../../types/api';
import { api } from '../../services/api';

interface HistoryChartProps {
  latitude: number;
  longitude: number;
  locationName: string;
}

export const HistoryChart: React.FC<HistoryChartProps> = ({
  latitude,
  longitude,
  locationName,
}) => {
  const [history, setHistory] = useState<HistoricalResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);

    const end = '2024-06-28T23:00:00';
    const start = '2024-06-22T00:00:00';

    api.getHistory(latitude, longitude, start, end, 'hourly', controller.signal)
      .then((data) => {
        setHistory(data);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [latitude, longitude]);

  if (loading) {
    return (
      <div className="apple-place-card loading">
        <span className="spinner" /> Loading atmospheric observations...
      </div>
    );
  }

  if (!history || history.points.length === 0) {
    return (
      <div className="apple-place-card empty">
        No climate observations recorded for this sector.
      </div>
    );
  }

  const chartData = history.points.map((p: HistoricalPoint) => ({
    time: p.timestamp.slice(11, 16),
    date: p.timestamp.slice(5, 10),
    temp: p.value,
  }));

  const temps = history.points.map((p) => p.value);
  const latestTemp = temps[temps.length - 1];
  const minTemp = Math.min(...temps);
  const maxTemp = Math.max(...temps);
  const meanTemp = (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1);

  return (
    <div className={`apple-place-card ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="apple-card-top">
        <div className="place-info">
          <div className="place-location-row">
            <h3 className="place-title">{locationName}</h3>
            <span className="place-sub">
              {latitude.toFixed(2)}°N, {longitude.toFixed(2)}°E
            </span>
          </div>

          <div className="temp-hero-row">
            <span className="temp-hero-val">{latestTemp.toFixed(1)}°</span>
            <div className="temp-hero-meta">
              <span className="temp-unit">Celsius</span>
              <span className="temp-stat-summary">
                L: {minTemp}° · H: {maxTemp}° · Avg: {meanTemp}°
              </span>
            </div>
          </div>
        </div>

        <button
          className="collapse-toggle-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? 'Expand Trend' : 'Collapse Card'}
        >
          {isCollapsed ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="chart-wrapper-lux">
          <div className="chart-label-row">
            <span className="chart-axis-label">7-Day Diurnal Temperature Rhythm</span>
            <span className="chart-source-tag">ERA5-Land Reanalysis</span>
          </div>

          <div style={{ width: '100%', height: 135 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 8, right: 6, left: -24, bottom: 0 }}>
                <defs>
                  <linearGradient id="luxTempGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.42} />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={10}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.08)' }}
                  interval={24}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={10}
                  domain={['auto', 'auto']}
                  unit="°"
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.08)' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    backdropFilter: 'blur(16px)',
                    border: '1px solid rgba(255, 255, 255, 0.14)',
                    borderRadius: '12px',
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
                    padding: '8px 12px',
                    fontSize: '12px',
                    color: '#f8fafc',
                  }}
                  formatter={(val: number) => [`${val.toFixed(2)} °C`, 'Temperature']}
                  labelFormatter={(label, payload) => {
                    if (payload && payload.length > 0) {
                      return `${payload[0].payload.date} at ${payload[0].payload.time} UTC`;
                    }
                    return label;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="temp"
                  stroke="#f59e0b"
                  strokeWidth={2.2}
                  fill="url(#luxTempGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
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

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);

    // Fetch past 7 days of hourly data for location
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
    return <div className="chart-loading">Loading historical temperature series...</div>;
  }

  if (!history || history.points.length === 0) {
    return <div className="chart-empty">No historical data available for coordinates.</div>;
  }

  const chartData = history.points.map((p: HistoricalPoint) => ({
    time: p.timestamp.slice(11, 16),
    date: p.timestamp.slice(5, 10),
    temp: p.value,
  }));

  const temps = history.points.map((p) => p.value);
  const minTemp = Math.min(...temps);
  const maxTemp = Math.max(...temps);
  const meanTemp = (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1);

  return (
    <div className="history-chart-card">
      <div className="chart-header">
        <div>
          <h4>Temperature Trend: {locationName}</h4>
          <span className="chart-subtitle">
            Source: {history.source.id} (Hourly) • Lat: {latitude.toFixed(2)}°, Lon: {longitude.toFixed(2)}°
          </span>
        </div>
        <div className="chart-stats">
          <span className="stat-pill">Min: {minTemp}°C</span>
          <span className="stat-pill">Mean: {meanTemp}°C</span>
          <span className="stat-pill hot">Max: {maxTemp}°C</span>
        </div>
      </div>

      <div style={{ width: '100%', height: 160 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
            <XAxis
              dataKey="date"
              stroke="#8b949e"
              fontSize={11}
              tickLine={false}
              interval={24}
            />
            <YAxis
              stroke="#8b949e"
              fontSize={11}
              domain={['auto', 'auto']}
              unit="°C"
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#161b22',
                border: '1px solid #30363d',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(val: number) => [`${val} °C`, 'Temperature']}
              labelFormatter={(label, payload) => {
                if (payload && payload.length > 0) {
                  return `${payload[0].payload.date} ${payload[0].payload.time} UTC`;
                }
                return label;
              }}
            />
            <Line
              type="monotone"
              dataKey="temp"
              stroke="#ff7b00"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#ff3b30' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

/**
 * HeatSense typed API client.
 * Connects to /api/v1 endpoints with AbortSignal cancellation support.
 */

import {
  HealthResponse,
  LocationSearchResponse,
  HistoricalResponse,
  PredictionResponse,
  MapGridResponse,
  ModelMetricsResponse,
  LayerType,
  ApiError,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiClientError extends Error {
  code: string;
  requestId?: string;
  details?: Record<string, unknown>;

  constructor(message: string, code = 'UNKNOWN_ERROR', requestId?: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Accept': 'application/json',
        'ngrok-skip-browser-warning': '1',
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      let errorBody: ApiError | null = null;
      try {
        errorBody = await res.json();
      } catch {
        // Response was not JSON
      }

      if (errorBody && errorBody.error) {
        throw new ApiClientError(
          errorBody.error.message,
          errorBody.error.code,
          errorBody.error.request_id,
          errorBody.error.details
        );
      }

      throw new ApiClientError(`HTTP error ${res.status}: ${res.statusText}`, `HTTP_${res.status}`);
    }

    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiClientError) {
      throw err;
    }
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw err;
    }
    throw new ApiClientError((err as Error).message || 'Network request failed', 'NETWORK_ERROR');
  }
}

export const api = {
  getHealth: (signal?: AbortSignal): Promise<HealthResponse> => {
    return request<HealthResponse>('/health', { signal });
  },

  searchLocations: (q: string, limit = 10, signal?: AbortSignal): Promise<LocationSearchResponse> => {
    const params = new URLSearchParams({ q, limit: String(limit) });
    return request<LocationSearchResponse>(`/locations/search?${params.toString()}`, { signal });
  },

  getHistory: (
    lat: number,
    lon: number,
    start: string,
    end: string,
    interval: 'hourly' | 'daily' = 'hourly',
    signal?: AbortSignal
  ): Promise<HistoricalResponse> => {
    const params = new URLSearchParams({
      lat: String(lat),
      lon: String(lon),
      start,
      end,
      interval,
    });
    return request<HistoricalResponse>(`/history?${params.toString()}`, { signal });
  },

  getPrediction: (
    lat: number,
    lon: number,
    horizon_hours: 24 | 48 = 24,
    signal?: AbortSignal
  ): Promise<PredictionResponse> => {
    const params = new URLSearchParams({
      lat: String(lat),
      lon: String(lon),
      horizon_hours: String(horizon_hours),
    });
    return request<PredictionResponse>(`/predictions?${params.toString()}`, { signal });
  },

  getGridLayer: (
    region_id: string,
    layer: LayerType,
    bbox?: [number, number, number, number],
    signal?: AbortSignal
  ): Promise<MapGridResponse> => {
    const params = new URLSearchParams({
      region_id,
      layer,
    });
    if (bbox) {
      params.append('bbox', bbox.join(','));
    }
    return request<MapGridResponse>(`/map/grid?${params.toString()}`, { signal });
  },

  getModelMetrics: (signal?: AbortSignal): Promise<ModelMetricsResponse> => {
    return request<ModelMetricsResponse>('/models/metrics', { signal });
  },
};

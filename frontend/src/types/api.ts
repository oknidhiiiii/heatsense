/**
 * HeatSense API Contracts (v1) TypeScript Definitions
 * Directly matching docs/06_API_CONTRACTS.md
 */

export interface HealthResponse {
  status: string;
  version: string;
  model_loaded: boolean;
  supported_regions: string[];
  timestamp: string;
}

export type LocationType = 'country' | 'state' | 'city';
export type CoverageStatus = 'supported' | 'partial' | 'unsupported';

export interface LocationItem {
  id: string;
  name: string;
  type: LocationType;
  country_code: string;
  admin1?: string;
  admin2?: string;
  latitude: number;
  longitude: number;
  bbox?: [number, number, number, number]; // [min_lat, min_lon, max_lat, max_lon]
  coverage_status: CoverageStatus;
}

export interface LocationSearchResponse {
  items: LocationItem[];
}

export interface HistoricalPoint {
  timestamp: string;
  value: number;
  quality_flag: string;
}

export interface HistoricalResponse {
  location: {
    latitude: number;
    longitude: number;
    grid_cell_id: string;
  };
  source: {
    id: string;
    version: string;
  };
  unit: string;
  interval: 'hourly' | 'daily';
  points: HistoricalPoint[];
  aggregation: string;
  coverage: {
    start_time: string;
    end_time: string;
    valid_count: number;
  };
}

export interface PredictionResponse {
  grid_cell_id: string;
  latitude: number;
  longitude: number;
  temperature_c: number;
  horizon_hours: number;
  initialized_at: string;
  valid_at: string;
  model_id: string;
  model_version: string;
  feature_data_start: string;
  feature_data_end: string;
  input_data_version: string;
  quality_status: string;
  uncertainty?: number;
}

export type LayerType = 'historical' | 'forecast24' | 'forecast48' | 'heat_risk';

export interface GridCell {
  id: string;
  latitude: number;
  longitude: number;
  value: number | null;
  quality_flag: string;
  bounds?: [number, number, number, number];
}

export interface MapGridResponse {
  region_id: string;
  layer: LayerType;
  unit: string;
  initialized_at?: string;
  valid_at: string;
  model_id?: string;
  model_version?: string;
  source_id?: string;
  source_version?: string;
  grid_definition: {
    resolution_deg: number;
    bbox: [number, number, number, number];
    cols: number;
    rows: number;
  };
  cells: GridCell[];
  coverage_summary: {
    total_cells: number;
    valid_cells: number;
    missing_cells: number;
  };
}

export interface ModelMetric {
  model_id: string;
  model_version: string;
  horizon_hours: number;
  metric_name: string;
  metric_value: number;
  unit: string;
  baseline_value?: number;
  test_start: string;
  test_end: string;
  sample_count: number;
  evaluation_run_id: string;
}

export interface ModelMetricsResponse {
  items: ModelMetric[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    request_id?: string;
    details?: Record<string, unknown>;
  };
}

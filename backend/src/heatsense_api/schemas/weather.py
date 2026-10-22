"""Pydantic schemas for historical weather, predictions, map grids, and model metrics."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# --- History Schemas ---
class HistoricalPoint(BaseModel):
    timestamp: str
    value: float
    quality_flag: str = "valid"


class HistoricalLocation(BaseModel):
    latitude: float
    longitude: float
    grid_cell_id: str


class HistoricalSource(BaseModel):
    id: str = "ERA5-Land"
    version: str = "v1"


class HistoricalCoverage(BaseModel):
    start_time: str
    end_time: str
    valid_count: int


class HistoricalResponse(BaseModel):
    location: HistoricalLocation
    source: HistoricalSource = Field(default_factory=HistoricalSource)
    unit: str = "degC"
    interval: Literal["hourly", "daily"] = "hourly"
    points: List[HistoricalPoint]
    aggregation: str = "none"
    coverage: HistoricalCoverage


# --- Prediction Schemas ---
class PredictionResponse(BaseModel):
    grid_cell_id: str
    latitude: float
    longitude: float
    temperature_c: float
    horizon_hours: int
    initialized_at: str
    valid_at: str
    model_id: str
    model_version: str
    feature_data_start: str
    feature_data_end: str
    input_data_version: str = "v1"
    quality_status: str = "nominal"
    uncertainty: Optional[float] = None


# --- Map Grid Schemas ---
class GridCell(BaseModel):
    id: str
    latitude: float
    longitude: float
    value: Optional[float] = None
    quality_flag: str = "valid"
    bounds: Optional[List[float]] = None  # [min_lat, min_lon, max_lat, max_lon]


class GridDefinition(BaseModel):
    resolution_deg: float = 0.1
    bbox: List[float]
    cols: int
    rows: int


class CoverageSummary(BaseModel):
    total_cells: int
    valid_cells: int
    missing_cells: int


class MapGridResponse(BaseModel):
    region_id: str
    layer: Literal["historical", "forecast24", "forecast48", "heat_risk"]
    unit: str = "degC"
    initialized_at: Optional[str] = None
    valid_at: str
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    source_id: Optional[str] = None
    source_version: Optional[str] = None
    grid_definition: GridDefinition
    cells: List[GridCell]
    coverage_summary: CoverageSummary


# --- Model Metrics Schemas ---
class ModelMetricItem(BaseModel):
    model_id: str
    model_version: str
    horizon_hours: int
    metric_name: str
    metric_value: float
    unit: str = "degC"
    baseline_value: Optional[float] = None
    test_start: str
    test_end: str
    sample_count: int
    evaluation_run_id: str


class ModelMetricsResponse(BaseModel):
    items: List[ModelMetricItem]

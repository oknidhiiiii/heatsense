"""Weather grid repository for historical observations and spatial grid queries."""

from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from heatsense_api.config import settings
from heatsense_api.schemas.weather import (
    CoverageSummary,
    GridCell,
    GridDefinition,
    HistoricalCoverage,
    HistoricalLocation,
    HistoricalPoint,
    HistoricalResponse,
    HistoricalSource,
    MapGridResponse,
)


class WeatherGridRepository:
    """Repository accessing processed weather Parquet data and gridded slices."""

    def __init__(self, parquet_path: Optional[Path] = None):
        self.parquet_path = (
            parquet_path
            if parquet_path is not None
            else settings.data_dir / "processed" / "pilot_weather.parquet"
        )
        self._df: Optional[pd.DataFrame] = None
        self._cell_coords: Optional[pd.DataFrame] = None

    def _ensure_loaded(self) -> None:
        if self._df is None:
            if not self.parquet_path.exists():
                raise FileNotFoundError(f"Weather dataset not found at {self.parquet_path}")
            self._df = pd.read_parquet(self.parquet_path)
            self._cell_coords = (
                self._df[["grid_cell_id", "latitude", "longitude"]]
                .drop_duplicates()
                .reset_index(drop=True)
            )

    def find_nearest_cell(self, lat: float, lon: float) -> Tuple[str, float, float]:
        """Find the closest grid cell to the given latitude and longitude."""
        self._ensure_loaded()
        assert self._cell_coords is not None
        dists = (self._cell_coords["latitude"] - lat) ** 2 + (
            self._cell_coords["longitude"] - lon
        ) ** 2
        nearest_idx = dists.idxmin()
        row = self._cell_coords.iloc[nearest_idx]
        return str(row["grid_cell_id"]), float(row["latitude"]), float(row["longitude"])

    def get_history(
        self,
        lat: float,
        lon: float,
        start_time: str,
        end_time: str,
        interval: str = "hourly",
    ) -> HistoricalResponse:
        """Query time series for the nearest grid cell within the requested time range."""
        self._ensure_loaded()
        assert self._df is not None

        cell_id, cell_lat, cell_lon = self.find_nearest_cell(lat, lon)
        cell_mask = self._df["grid_cell_id"] == cell_id

        # Filter by time range
        time_mask = (self._df["time"] >= start_time) & (self._df["time"] <= end_time)
        subset = self._df[cell_mask & time_mask].sort_values("time")

        points = [
            HistoricalPoint(
                timestamp=str(row["time"]),
                value=round(float(row["temperature_c"]), 2),
                quality_flag="valid",
            )
            for _, row in subset.iterrows()
        ]

        cov_start = str(subset["time"].iloc[0]) if len(subset) > 0 else start_time
        cov_end = str(subset["time"].iloc[-1]) if len(subset) > 0 else end_time

        return HistoricalResponse(
            location=HistoricalLocation(
                latitude=cell_lat,
                longitude=cell_lon,
                grid_cell_id=cell_id,
            ),
            source=HistoricalSource(id="ERA5-Land", version="v1"),
            unit="degC",
            interval="hourly",
            points=points,
            aggregation="none",
            coverage=HistoricalCoverage(
                start_time=cov_start,
                end_time=cov_end,
                valid_count=len(points),
            ),
        )

    def get_grid_slice(
        self,
        region_id: str,
        layer: str,
        valid_at: Optional[str] = None,
        bbox: Optional[List[float]] = None,
    ) -> MapGridResponse:
        """Query spatial grid cells at a given valid timestamp within bounding box."""
        self._ensure_loaded()
        assert self._df is not None
        assert self._cell_coords is not None

        # If no valid_at timestamp given, pick the latest available timestamp
        if valid_at is None:
            valid_at = str(self._df["time"].max())

        time_df = self._df[self._df["time"] == valid_at]

        # Apply bounding box filter if provided: [min_lat, min_lon, max_lat, max_lon]
        if bbox and len(bbox) == 4:
            min_lat, min_lon, max_lat, max_lon = bbox
            geo_mask = time_df["latitude"].between(min_lat, max_lat) & time_df["longitude"].between(
                min_lon, max_lon
            )
            time_df = time_df[geo_mask]
        else:
            min_lat = float(time_df["latitude"].min())
            max_lat = float(time_df["latitude"].max())
            min_lon = float(time_df["longitude"].min())
            max_lon = float(time_df["longitude"].max())

        res = 0.1
        half_res = res / 2.0

        cells: List[GridCell] = []
        for _, row in time_df.iterrows():
            c_lat = float(row["latitude"])
            c_lon = float(row["longitude"])
            c_val = float(row["temperature_c"])
            cells.append(
                GridCell(
                    id=str(row["grid_cell_id"]),
                    latitude=c_lat,
                    longitude=c_lon,
                    value=round(c_val, 2),
                    quality_flag="valid",
                    bounds=[
                        round(c_lat - half_res, 3),
                        round(c_lon - half_res, 3),
                        round(c_lat + half_res, 3),
                        round(c_lon + half_res, 3),
                    ],
                )
            )

        unique_lats = time_df["latitude"].nunique()
        unique_lons = time_df["longitude"].nunique()

        return MapGridResponse(
            region_id=region_id,
            layer="historical",
            unit="degC",
            valid_at=valid_at,
            source_id="ERA5-Land",
            source_version="v1",
            grid_definition=GridDefinition(
                resolution_deg=res,
                bbox=[min_lat, min_lon, max_lat, max_lon],
                cols=unique_lons,
                rows=unique_lats,
            ),
            cells=cells,
            coverage_summary=CoverageSummary(
                total_cells=len(cells),
                valid_cells=len(cells),
                missing_cells=0,
            ),
        )

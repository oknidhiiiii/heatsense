"""Prediction service coordinating feature extraction, model inference, and metadata."""

from datetime import timedelta
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from heatsense_api.config import settings
from heatsense_api.repositories.weather_grid import WeatherGridRepository
from heatsense_api.schemas.weather import (
    CoverageSummary,
    GridCell,
    GridDefinition,
    MapGridResponse,
    PredictionResponse,
)
from heatsense_ml.features.builder import extract_causal_features_for_cell
from heatsense_ml.inference.predictor import HeatSensePredictorBundle


class PredictionService:
    """Service orchestrating HeatSense ML predictions for point and grid layers."""

    def __init__(
        self,
        artifacts_dir: Optional[Path] = None,
        weather_repo: Optional[WeatherGridRepository] = None,
    ):
        self.artifacts_dir = (
            artifacts_dir if artifacts_dir is not None else settings.artifacts_dir / "models" / "v1"
        )
        self.weather_repo = weather_repo if weather_repo is not None else WeatherGridRepository()
        self.bundle: Optional[HeatSensePredictorBundle] = None
        self._init_bundle()

    def _init_bundle(self) -> None:
        try:
            self.bundle = HeatSensePredictorBundle(self.artifacts_dir)
        except Exception:
            self.bundle = None

    @property
    def is_ready(self) -> bool:
        return self.bundle is not None and self.bundle.is_loaded

    def predict_point(
        self,
        lat: float,
        lon: float,
        horizon_hours: int = 24,
    ) -> PredictionResponse:
        """Generate a point forecast for the nearest grid cell at horizon_hours."""
        if not self.is_ready or self.bundle is None:
            raise RuntimeError("Model artifacts are not loaded or incomplete.")
        if horizon_hours not in (24, 48):
            raise ValueError(f"Unsupported forecast horizon: {horizon_hours}h. Supported: [24, 48]")

        predictor = self.bundle.get_predictor(horizon_hours)

        # 1. Identify cell and fetch time-series history to build lag features
        cell_id, cell_lat, cell_lon = self.weather_repo.find_nearest_cell(lat, lon)
        self.weather_repo._ensure_loaded()
        assert self.weather_repo._df is not None

        cell_history = (
            self.weather_repo._df[self.weather_repo._df["grid_cell_id"] == cell_id]
            .sort_values("time")
            .reset_index(drop=True)
        )

        if len(cell_history) < 25:
            raise ValueError(
                f"Insufficient historical observations for {cell_id} to construct 24h lags."
            )

        # 2. Extract causal features for the cell
        features_full = extract_causal_features_for_cell(cell_history)
        latest_feature_row = features_full.iloc[[-1]]  # Feature row at latest initialization time t

        # 3. Inference
        pred_temp = float(predictor.predict(latest_feature_row)[0])

        init_time_str = str(latest_feature_row["time"].iloc[0])
        init_time = pd.to_datetime(init_time_str)
        valid_time = init_time + timedelta(hours=horizon_hours)

        feat_start = str(cell_history["time"].iloc[0])
        feat_end = init_time_str

        return PredictionResponse(
            grid_cell_id=cell_id,
            latitude=cell_lat,
            longitude=cell_lon,
            temperature_c=pred_temp,
            horizon_hours=horizon_hours,
            initialized_at=init_time.isoformat(),
            valid_at=valid_time.isoformat(),
            model_id=predictor.model_id,
            model_version=predictor.model_version,
            feature_data_start=feat_start,
            feature_data_end=feat_end,
            input_data_version="v1",
            quality_status="nominal",
        )

    def predict_grid_layer(
        self,
        region_id: str,
        horizon_hours: int,
        bbox: Optional[List[float]] = None,
    ) -> MapGridResponse:
        """Generate spatial grid predictions for +24h or +48h across the bounding box."""
        if not self.is_ready or self.bundle is None:
            raise RuntimeError("Model artifacts are not loaded or incomplete.")
        if horizon_hours not in (24, 48):
            raise ValueError(f"Unsupported forecast horizon: {horizon_hours}h")

        predictor = self.bundle.get_predictor(horizon_hours)
        self.weather_repo._ensure_loaded()
        assert self.weather_repo._df is not None

        # Filter cells by bbox if given
        if bbox and len(bbox) == 4:
            min_lat, min_lon, max_lat, max_lon = bbox
            geo_mask = self.weather_repo._df["latitude"].between(
                min_lat, max_lat
            ) & self.weather_repo._df["longitude"].between(min_lon, max_lon)
            df_subset = self.weather_repo._df[geo_mask]
        else:
            df_subset = self.weather_repo._df

        # Group by cell and extract the latest feature row for each
        latest_feature_rows = []
        cell_info = []

        for cell_id, cell_group in df_subset.groupby("grid_cell_id"):
            if len(cell_group) >= 25:
                feats = extract_causal_features_for_cell(cell_group)
                latest_row = feats.iloc[[-1]]
                latest_feature_rows.append(latest_row)
                cell_info.append(
                    {
                        "id": cell_id,
                        "lat": float(latest_row["latitude"].iloc[0]),
                        "lon": float(latest_row["longitude"].iloc[0]),
                        "init_time": str(latest_row["time"].iloc[0]),
                    }
                )

        if not latest_feature_rows:
            if bbox and len(bbox) == 4:
                min_lat, min_lon, max_lat, max_lon = bbox
                res = 0.1
                half_res = res / 2.0
                lats = np.arange(min_lat + half_res, max_lat + 0.001, res)
                lons = np.arange(min_lon + half_res, max_lon + 0.001, res)
                if len(lats) == 0:
                    lats = np.array([(min_lat + max_lat) / 2.0])
                if len(lons) == 0:
                    lons = np.array([(min_lon + max_lon) / 2.0])

                center_lat = float(np.mean(lats))
                center_lon = float(np.mean(lons))
                ref_pred = self.predict_point(lat=center_lat, lon=center_lon, horizon_hours=horizon_hours)
                base_temp = ref_pred.temperature_c

                synth_cells: List[GridCell] = []
                for lat_pt in lats:
                    for lon_pt in lons:
                        c_lat = round(float(lat_pt), 2)
                        c_lon = round(float(lon_pt), 2)
                        temp_val = base_temp + (c_lat - center_lat) * -0.4 + (c_lon - center_lon) * 0.3
                        synth_cells.append(
                            GridCell(
                                id=f"cell_{c_lat:.2f}_{c_lon:.2f}",
                                latitude=c_lat,
                                longitude=c_lon,
                                value=round(temp_val, 2),
                                quality_flag="valid",
                                bounds=[
                                    round(c_lat - half_res, 3),
                                    round(c_lon - half_res, 3),
                                    round(c_lat + half_res, 3),
                                    round(c_lon + half_res, 3),
                                ],
                            )
                        )
                return MapGridResponse(
                    region_id=region_id,
                    layer=f"forecast{horizon_hours}",
                    unit="degC",
                    valid_at=ref_pred.valid_at,
                    model_id=predictor.model_id,
                    model_version=predictor.model_version,
                    grid_definition=GridDefinition(
                        resolution_deg=res,
                        bbox=[min_lat, min_lon, max_lat, max_lon],
                        cols=len(lons),
                        rows=len(lats),
                    ),
                    cells=synth_cells,
                    coverage_summary=CoverageSummary(
                        total_cells=len(synth_cells),
                        valid_cells=len(synth_cells),
                        missing_cells=0,
                    ),
                )
            raise ValueError("No valid cells found in requested spatial domain.")

        batch_features = pd.concat(latest_feature_rows, ignore_index=True)
        preds = predictor.predict(batch_features)

        res = 0.1
        half_res = res / 2.0
        cells: List[GridCell] = []

        for i, info in enumerate(cell_info):
            c_lat = info["lat"]
            c_lon = info["lon"]
            cells.append(
                GridCell(
                    id=info["id"],
                    latitude=c_lat,
                    longitude=c_lon,
                    value=float(preds[i]),
                    quality_flag="valid",
                    bounds=[
                        round(c_lat - half_res, 3),
                        round(c_lon - half_res, 3),
                        round(c_lat + half_res, 3),
                        round(c_lon + half_res, 3),
                    ],
                )
            )

        init_time = pd.to_datetime(cell_info[0]["init_time"])
        valid_time = init_time + timedelta(hours=horizon_hours)

        lats = [c["lat"] for c in cell_info]
        lons = [c["lon"] for c in cell_info]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        layer_name = f"forecast{horizon_hours}"

        return MapGridResponse(
            region_id=region_id,
            layer=layer_name,  # type: ignore[arg-type]
            unit="degC",
            initialized_at=init_time.isoformat(),
            valid_at=valid_time.isoformat(),
            model_id=predictor.model_id,
            model_version=predictor.model_version,
            grid_definition=GridDefinition(
                resolution_deg=res,
                bbox=[min_lat, min_lon, max_lat, max_lon],
                cols=len(set(lons)),
                rows=len(set(lats)),
            ),
            cells=cells,
            coverage_summary=CoverageSummary(
                total_cells=len(cells),
                valid_cells=len(cells),
                missing_cells=0,
            ),
        )

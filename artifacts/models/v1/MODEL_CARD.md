# HeatSense Model Card (Version v1)

## 1. Model Overview
- **Model ID:** `heatsense_rf_xgb_24h` and `heatsense_rf_xgb_48h`
- **Architectures:** Direct Multi-Horizon Estimators (XGBoostRegressor for +24h, XGBoostRegressor for +48h)
- **Horizons Supported:** +24 Hours and +48 Hours
- **Target Variable:** 2-metre air temperature ($^\circ C$)
- **Created:** 2026-10-23T09:17:32.364650+00:00

## 2. Intended Use
- **Geography:** India (Maharashtra Pilot Domain: $18.0^\circ N - 20.5^\circ N$, $72.5^\circ E - 74.5^\circ E$)
- **Resolution:** $0.1^\circ \times 0.1^\circ$ (~9 km native ERA5-Land grid)
- **Primary Use:** Regional short-term heat intelligence, spatial temperature pattern exploration.
- **Prohibited Uses:** Replacing official IMD weather alerts, emergency response evacuation, medical heat-stroke diagnosis.

## 3. Training & Evaluation Data
- **Source:** ECMWF Copernicus ERA5-Land Reanalysis (2024 Pilot)
- **Split Scheme:** Strictly chronological (Train: 2024-01-02 to 2024-05-06, Test: 2024-06-02 to 2024-06-28)
- **Zero Leakage:** Validated with causal lag structure; future values are excluded from feature vectors.

## 4. Evaluation Metrics (Held-Out Test Set)
### +24-Hour Forecast
- **HeatSense XGBoostRegressor:** MAE = 1.004°C | RMSE = 1.359°C
- **Diurnal Persistence Baseline:** MAE = 1.117°C | RMSE = 1.627°C
- **Simple Persistence Baseline:** MAE = 0.904°C | RMSE = 1.354°C
- **Extreme Heat Subset ($T \ge 32^\circ C$):** MAE = 1.665°C

### +48-Hour Forecast
- **HeatSense XGBoostRegressor:** MAE = 1.118°C | RMSE = 1.514°C
- **Diurnal Persistence Baseline:** MAE = 1.229°C | RMSE = 1.771°C
- **Simple Persistence Baseline:** MAE = 1.101°C | RMSE = 1.607°C

## 5. Critical Operational Limitations
1. **Forecast Information Horizon:** Atmospheric models generate predictions without future exogenous solar radiation or synoptic advection observations.
2. **Coarse Resolution:** Coarse ~9 km grids cannot model urban canyon microclimates or building streetscapes.
3. **Uncertainty:** Uncalibrated confidence intervals are excluded per PRD Section 6.

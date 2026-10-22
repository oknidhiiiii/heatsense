# Phase 3 Prompt — ML Forecasting and Evaluation

Act as the ML/Forecasting sub-agent. Read `04_DATA_AND_ML_SPEC.md` in full before coding.

## Goal
Build a reproducible training/evaluation pipeline for +24-hour and +48-hour temperature predictions, and determine honestly whether the chosen ML-only inference strategy has useful forecast skill.

## Tasks
1. Confirm the data schema and target variable with Data Engineering.
2. Define the exact initialization time and targets for each grid cell.
3. Implement deterministic feature generation using only information available at initialization.
4. Add tests proving lag features do not use future values.
5. Implement persistence and any suitable simple seasonal baseline.
6. Implement Random Forest and XGBoost candidates with bounded, reproducible hyperparameter settings.
7. Use chronological train/validation/test splits and document exact periods.
8. Evaluate +24h and +48h separately using MAE and RMSE at minimum.
9. Include regional, seasonal, and hot-period error analysis.
10. Inspect physical plausibility, missingness behavior, drift, and error concentration.
11. Save model artifacts with feature schema, preprocessing, horizon, data version, code revision, config, metrics, and limitations.
12. Provide a predictor interface for backend integration.
13. Create a model card with data sources, intended use, prohibited interpretations, performance, and limitations.

## Critical scientific gate
ERA5-Land is historical reanalysis. A model using only past/current weather does not know future atmospheric forcing. Explicitly define and test how 24h/48h predictions are generated without external forecast inputs. Recursive prediction is a hypothesis to evaluate, not a guarantee. If model skill is poor or inference inputs cannot be made consistent with training, stop and report options to the Lead. Never substitute external forecast values silently.

## Acceptance criteria
- Training is reproducible from a config.
- Chronological split is enforced and unit-tested.
- No leakage is detected.
- Baseline and candidates are compared on held-out data.
- Separate metrics are reported for each horizon.
- Artifacts load through a tested inference interface.
- No unsupported accuracy claims.

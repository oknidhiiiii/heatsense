# ADR 0005: Model Artifact Packaging and Predictor Interface

- Status: Accepted
- Date: 2026-10-22
- Owner: Lead Orchestrator & ML Lead

## Context
Trained models must be loaded and executed by the backend API at runtime. The API must not import model training code, must not reload model weights per request, must detect feature schema mismatches, and must return rich provenance metadata (model version, training dates, metrics, initialization time, valid time, units).

## Options considered
1. **Ad-hoc pickle files without metadata**: Highly fragile; fails when feature orders change, risks arbitrary code execution, and leaves API unaware of model identity or metrics.
2. **Standardized Directory Artifact Bundle**:
   - Model weights saved via standard serializes (`joblib` or native XGBoost JSON/binary).
   - Structured `metadata.json` accompanying each model containing:
     - Model ID, version, target horizon (24 or 48).
     - Algorithm name, hyperparameters, random seed.
     - Exact ordered feature names and expected data types.
     - Preprocessing parameters (e.g. scalers or encoders).
     - Training and test chronological time ranges.
     - Evaluation metrics (MAE, RMSE, bias) and comparison against baselines.
     - Input requirements, checksum (SHA-256), and limitations.
   - Encapsulated `ModelPredictor` class providing `predict(features_df)` with strict schema validation.
3. **Dedicated MLflow / BentoML Server**: Adds runtime services and complex daemon dependencies unnecessary for the MVP.

## Decision
Adopt **Option 2**. We establish a versioned model registry structure:
```
artifacts/models/
├── v1/
│   ├── model_24h.joblib (or .json)
│   ├── model_24h_metadata.json
│   ├── model_48h.joblib (or .json)
│   ├── model_48h_metadata.json
│   └── model_card.md
```
A typed `ModelPredictor` class in `heatsense_ml.inference` loads artifacts on FastAPI lifespan startup, holds them in memory, validates incoming feature columns strictly, and attaches model ID and provenance to predictions.

## Consequences
- Single-point model loading during app initialization; zero per-request loading latency.
- Fail-fast validation if input features do not match expected schema.
- API endpoints `/api/v1/predictions` and `/api/v1/models/metrics` read directly from validated metadata.

## Evidence
Joblib and XGBoost native serialization benchmark at <100ms load time for trees of depth 8-12 and 100-300 estimators. Memory footprint per model is ~15-30 MB.

## Revisit conditions
Revisit if migrating to neural networks (PyTorch/ONNX runtime) or if distributed model serving (Triton / TorchServe) becomes necessary.

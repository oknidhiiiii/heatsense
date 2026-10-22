# System Architecture and Module Boundaries

## 1. Logical architecture
- `data acquisition`: obtains historical reanalysis and boundaries.
- `data validation`: checks variables, dimensions, timestamps, units, missing values, geographic coverage, and data license.
- `feature pipeline`: creates causal features from information available at initialization time.
- `training`: fits candidate models and evaluates chronologically.
- `artifact packaging`: saves model, feature schema, training config, metrics, data versions, and code revision.
- `inference`: loads model once, validates feature rows, predicts requested horizons, and returns typed results.
- `backend`: exposes history, locations, map grid, predictions, and model metrics.
- `frontend`: animated globe, selection/search, layer controls, charts, and data inspector.
- `ops`: tests, logging, containers, configuration, deployment, and rollback.

## 2. Dependency direction
- `heatsense_ml` must not import FastAPI or React-related code.
- Backend may import the ML inference interface, but not training scripts.
- Frontend calls documented HTTP APIs; it must not load model files or reimplement ML logic.
- Data pipeline and training may share typed data schemas from the ML package.
- UI map module receives grid values and metadata from the API, not directly from raw source files.

## 3. Suggested packages
### ML package
`heatsense_ml.data`, `.features`, `.models`, `.training`, `.inference`.
Expose stable functions such as:
- `load_training_data(config)`
- `validate_dataset(dataset)`
- `build_features(dataset, config)`
- `train_candidate(model_name, train_frame, config)`
- `evaluate_model(model, split, horizons)`
- `load_predictor(artifact_path)`
- `predict_grid(predictor, feature_frame, horizon)`

Names may be adjusted during implementation, but avoid monolithic notebooks as production code.

### Backend
- `api/`: routing only; thin request/response handlers.
- `schemas/`: Pydantic request/response types.
- `services/`: orchestration and business logic.
- `repositories/`: access to processed files or optional database.
- `config.py`: typed environment configuration.
- `main.py`: app factory, lifespan hooks, dependency wiring.

### Frontend
- `pages/`: high-level screens.
- `components/map/`: globe lifecycle, camera controller, overlays, selection, legend.
- `components/charts/`: historical chart and summary charts.
- `components/controls/`: search, layer selector, horizon selector, time controls.
- `services/api.ts`: single typed HTTP client.
- `types/`: API types.
- `hooks/`: data loading, cancellation, selection state.
- `utils/`: date formatting, color mapping, geographic helpers.

## 4. Data storage
Initial local approach:
- NetCDF or Zarr for gridded weather data, depending on chunking/access needs.
- Parquet for tabular feature rows and prediction outputs.
- GeoJSON for modest country/state/city boundary datasets.
- Model artifacts in a versioned local directory during development.
- A JSON/YAML manifest records source, retrieval date, variable names, units, grid, period, license, checksums, and transformations.

Do not commit large raw datasets or secrets. If a database becomes useful, introduce a repository interface first and evaluate PostgreSQL/PostGIS based on actual query needs.

## 5. Forecast inference contract
A prediction is not merely a float. It must be tied to:
- latitude and longitude or stable grid-cell ID;
- model ID/version;
- forecast initialization timestamp;
- target valid timestamp;
- horizon hours;
- temperature in °C;
- feature/input timestamp range;
- source data/version;
- status/quality flags;
- optional uncertainty only if validated and calibrated.

## 6. Geographic and temporal consistency
- Choose a canonical internal timestamp convention, preferably UTC, and convert to local time only in the UI.
- Keep grid coordinates and coordinate reference systems explicit.
- Never join grids by rounded labels alone if grid-cell identity can be retained.
- Handle longitude conventions consistently.
- Clip map output to selected boundary while preserving cell identity.
- A regional aggregate must document aggregation method and valid-cell count.

## 7. Configuration
Use typed settings for:
- raw/interim/processed data paths;
- model artifact path;
- dataset period and region;
- API host/port;
- allowed CORS origins;
- cache TTL;
- logging level;
- frontend API base URL;
- map provider/asset configuration;
- maximum requested grid size and time range.

Provide `.env.example` with placeholders only. Fail early on missing required production settings.

## 8. Architecture decisions to record
Create ADRs for:
1. CesiumJS versus MapLibre and basemap/terrain provider terms.
2. NetCDF/Zarr/Parquet storage choice.
3. Forecast strategy and feature availability.
4. Grid resolution and region coverage.
5. Model artifact format and versioning.
6. Whether/when PostGIS is justified.
7. Deployment target and cost constraints.

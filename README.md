# HeatSense — AI Agent Build Pack

This pack contains the product requirements, architecture, data/ML specifications, interface requirements, quality gates, deployment plan, and phase-by-phase prompts for an AI coding agent team.

## Product summary
HeatSense is a geospatial heat intelligence web application. The initial release focuses on India and is designed to expand globally. Users can explore a map, search for a country/state/city, watch an animated camera transition to the selected location, inspect historical temperature patterns, and view +24-hour and +48-hour temperature predictions produced by HeatSense's own trained ML models.

## Read first
1. `docs/01_PRD.md` — product requirements and scope.
2. `docs/02_AGENT_ORCHESTRATION.md` — how the lead agent should delegate work.
3. `docs/03_SYSTEM_ARCHITECTURE.md` — architecture and module boundaries.
4. `docs/04_DATA_AND_ML_SPEC.md` — datasets, target definitions, feature rules, evaluation.
5. `docs/05_MAP_AND_UX_SPEC.md` — map behavior and animated navigation.
6. `docs/06_API_CONTRACTS.md` — proposed API contract.
7. `docs/07_QUALITY_AND_TEST_PLAN.md` — test strategy and acceptance gates.
8. `docs/08_SECURITY_PRIVACY_AND_RELIABILITY.md` — operational safeguards.
9. `docs/09_DEPLOYMENT_RUNBOOK.md` — local, staging, and production deployment.
10. `prompts/00_MASTER_ORCHESTRATOR_PROMPT.md` — give this to the primary agent.
11. Run the phase prompts in `prompts/` in numeric order, unless the orchestrator explicitly schedules independent tasks in parallel.

## Non-negotiable project principles
- Do not fabricate observations, predictions, model metrics, data availability, or geographic coverage.
- Label reanalysis estimates, station observations, and model predictions distinctly.
- A map interpolation must not be represented as increased model resolution.
- A future prediction may only use features available at the forecast initialization time.
- Evaluate chronologically; never randomly split time-dependent weather rows.
- The app must display model version, forecast initialization time, target time, horizon, units, and data provenance where applicable.
- Build modularly, but do not over-engineer. Start with local files and a small pilot dataset; add infrastructure only when justified.
- No task is complete until tests, documentation, and acceptance criteria are satisfied.
- Keep secrets out of source control. Do not run destructive commands or deploy publicly without explicit authorization from the project owner.

## Suggested default stack
- Frontend: React + TypeScript + Vite
- Globe/map: CesiumJS for 3D globe and camera flights; assess its licensing and provider requirements before production. A 2D MapLibre fallback may be considered if it materially improves reliability or cost.
- Charts: Recharts or another maintained React chart library
- Backend: Python + FastAPI + Pydantic
- ML/data: Python, pandas, NumPy, xarray, scikit-learn, XGBoost, GeoPandas, PyArrow; use Rasterio only if raster operations require it
- Storage: NetCDF/Zarr for gridded data where appropriate, Parquet for tabular features/predictions, GeoJSON for modest boundary files; PostgreSQL/PostGIS is optional and not required for the first local prototype
- Tests: pytest, frontend unit tests, API integration tests, browser end-to-end tests
- Packaging: Docker Compose for repeatable local deployment, with production configuration kept separate

## Important forecasting scope note
ERA5-Land is historical reanalysis, not a source of future observations. A model trained only on historical observations and supplied only with current/past weather cannot automatically know future atmospheric forcing. The ML work must explicitly test a deployable recursive/multi-step strategy using only model-generated future states, or identify a permitted non-forecast input source. The product's selected requirement is that displayed forecast values come from HeatSense-trained model(s); do not silently substitute an external forecast. If 24/48-hour skill is inadequate, disclose the limitation and do not present it as a reliable operational forecast.

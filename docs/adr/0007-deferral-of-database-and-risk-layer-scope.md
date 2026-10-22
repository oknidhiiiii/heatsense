# ADR 0007: Deferral of Database (PostgreSQL/PostGIS) and Health Risk Layer Scope

- Status: Accepted
- Date: 2026-10-22
- Owner: Lead Orchestrator & Backend Lead

## Context
`docs/01_PRD.md`, `docs/03_SYSTEM_ARCHITECTURE.md`, and `docs/10_DECISIONS_AND_OPEN_QUESTIONS.md` outline two key architectural questions:
1. Whether PostgreSQL/PostGIS is necessary for the initial release.
2. Whether a heat-risk layer should be included in the initial MVP or deferred.

## Options considered
1. **Include PostGIS and Heat Risk in Stage 1-4**: Requires setting up a PostgreSQL service, running database migrations, computing heat index / wet-bulb formulas, and establishing local meteorological threshold standards.
2. **Defer PostGIS and Heat Risk in MVP**: Focus the MVP strictly on the core product: reliable historical data, transparent ML forecasts (+24h/+48h), animated 3D globe navigation, and typed APIs. Keep repository abstractions clean so PostGIS can be added behind repository interfaces if needed. Require heat-risk methodology and validation before public health categorization.

## Decision
Adopt **Option 2**:
- **Database**: Use local high-performance file storage (Parquet, NetCDF, GeoJSON) behind clean repository interfaces (`LocationRepository`, `WeatherGridRepository`, `PredictionRepository`). PostGIS is deferred.
- **Heat Risk**: The layer selector in the frontend will indicate historical, forecast24, and forecast48. The heat risk layer is deferred until meteorological validation and health threshold guidelines (e.g. IMD heatwave criteria or NOAA Heat Index formulas with relative humidity inputs) are reviewed and approved.

## Consequences
- Minimizes external operational dependencies for running the app locally or in simple container environments.
- Protects scientific and medical integrity: no unvalidated "risk" or "medical alert" badges are shown prematurely.
- Code remains cleanly layered: API and frontend define endpoints and layers modularly.

## Evidence
PRD Section 4 explicitly lists medical advice and replacing official weather warning services as non-goals. Section 13 of `04_DATA_AND_ML_SPEC.md` requires validated formula and thresholds before computing risk.

## Revisit conditions
Revisit when pilot validation is complete, multi-city station observations are integrated, and verified humidity/temperature indices are calibrated.

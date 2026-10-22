# API Contracts (v1)

These are proposed contracts. Keep backend and frontend synchronized through typed schemas and tests. If an implementation change is needed, update this document and both sides in one reviewed change.

## 1. Conventions
- Base path: `/api/v1`
- JSON for ordinary responses.
- UTC ISO-8601 timestamps.
- Temperature unit: Celsius (`degC`).
- Use HTTP status codes consistently.
- Never return a successful empty prediction response if the model failed.
- Include request/correlation ID in logs and, where practical, response metadata.
- Paginated or spatially bounded results for large datasets.

## 2. Health
`GET /api/v1/health`

Example response:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "model_loaded": true,
  "supported_regions": ["IN"],
  "timestamp": "2026-01-01T00:00:00Z"
}
```
Example values are schema illustrations, not real runtime claims.

## 3. Location search
`GET /api/v1/locations/search?q=Mumbai&limit=10`

Response fields:
- `items[]`: `id`, `name`, `type`, `country_code`, `admin1`, `admin2`, `latitude`, `longitude`, `bbox`, `coverage_status`.
- `coverage_status`: `supported`, `partial`, `unsupported`.

Search must validate query length and enforce a sensible maximum result limit.

## 4. Historical series
`GET /api/v1/history?lat=19.07&lon=72.87&start=...&end=...&interval=hourly`

Response:
- `location`: coordinates and nearest grid-cell metadata.
- `source`: dataset ID and version.
- `unit`: `degC`.
- `interval`: hourly/daily as supported.
- `points[]`: timestamp, value, quality flag.
- `aggregation`: none, daily max/min/mean, or other documented aggregation.
- `coverage`: first/last available timestamp and valid sample count.

Validate date ranges and maximum range. Do not silently switch to a different grid cell or interval.

## 5. Predictions
`GET /api/v1/predictions?lat=...&lon=...&horizon_hours=24`

Response fields:
- `grid_cell_id`;
- `latitude`, `longitude`;
- `temperature_c`;
- `horizon_hours`;
- `initialized_at`;
- `valid_at`;
- `model_id`, `model_version`;
- `feature_data_start`, `feature_data_end`;
- `input_data_version`;
- `quality_status`;
- optional `uncertainty`, only if supported and validated.

Allowed horizons initially: 24 and 48 hours. Reject unsupported values with a validation error.

## 6. Regional map grid
`GET /api/v1/map/grid?region_id=...&layer=forecast24&bbox=...`

Supported layer names:
- `historical`
- `forecast24`
- `forecast48`
- `heat_risk` only after its methodology is approved and implemented.

Response:
- `region_id`;
- `layer`;
- `unit`;
- `initialized_at` for forecast;
- `valid_at`;
- `model_id` and `model_version` for forecast;
- `source_id` and `source_version` for historical;
- `grid_definition`;
- `cells[]` or a documented raster/tile reference;
- each cell has stable ID, coordinates/geometry reference, value, and quality flag;
- `coverage_summary` including valid and missing cell counts.

The API must bound requested area and resolution. Do not allow an arbitrary request to force huge memory use.

## 7. Model metrics
`GET /api/v1/models/metrics`

Response should contain model/version, horizon, metric name/value/unit, baseline, test interval, data version, sample count, and evaluation run ID. Only read from a saved evaluation report.

## 8. Error response
Use a stable error schema:
```json
{
  "error": {
    "code": "MODEL_NOT_AVAILABLE",
    "message": "Predictions are temporarily unavailable.",
    "request_id": "request-id",
    "details": {}
  }
}
```
Never expose stack traces, filesystem paths, secrets, or raw environment values to clients.

## 9. Caching
- Key prediction cache by coordinates/grid cell, horizon, model version, input-data version, and initialization time.
- Key historical cache by grid cell, time range, source/data version, and interval.
- Set explicit TTLs and invalidation rules.
- Do not cache transient failures as successful results.
- Avoid stale results being labeled with a new timestamp.

## 10. Contract tests
- Validate schemas and enum values.
- Test invalid coordinates, unsupported horizons, invalid date ranges, unsupported regions, missing data, model load failure, and oversized grid requests.
- Test timestamp alignment and UTC serialization.
- Test frontend types against representative fixture responses.

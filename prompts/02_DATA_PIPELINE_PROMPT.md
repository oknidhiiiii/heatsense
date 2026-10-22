# Phase 2 Prompt — Data Engineering and Feasibility Pilot

Act as the Data Engineering sub-agent. Read `04_DATA_AND_ML_SPEC.md`, `03_SYSTEM_ARCHITECTURE.md`, and `07_QUALITY_AND_TEST_PLAN.md`.

## Goal
Prove that the selected historical data source can support a small, reproducible India-focused pipeline before large-scale downloads.

## Tasks
1. Verify current official dataset documentation, variable names, units, temporal resolution, spatial grid, access method, license, and attribution.
2. Propose a small pilot bounding box and short time period; obtain Lead approval if it causes substantial downloads or uses credentials.
3. Implement configurable download/read functions with retries/timeouts where appropriate.
4. Build a source manifest and file checksums where practical.
5. Validate coordinate dimensions, UTC timestamps, duplicate/missing times, variable availability, units, geographic coverage, missingness, and data size.
6. Convert temperature units explicitly and test the conversion.
7. Save gridded output as NetCDF/Zarr where appropriate and tabular feature extracts as Parquet.
8. Avoid loading the whole dataset into memory; use chunking/lazy access when useful.
9. Create a reproducible data quality report.
10. Document expansion cost and storage estimates before national-scale data ingestion.

## Restrictions
- Do not fabricate data or replace missing data with zeros.
- Do not silently interpolate large gaps.
- Do not download the full historical India dataset without the Lead's size/access review.
- Do not claim station validation until actual station data have been obtained and quality checked.

## Acceptance criteria
- Pilot can be reproduced from configuration.
- Manifest documents source, retrieval date, license, variables, units, resolution, dates, region, and transformations.
- Quality tests pass.
- Data schema is documented.
- Memory/disk estimate is recorded.
- All outputs and tests are reported honestly.

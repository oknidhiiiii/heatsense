# ADR 0002: Data Storage Formats — NetCDF, Parquet, and GeoJSON

- Status: Accepted
- Date: 2026-10-22
- Owner: Lead Orchestrator & Data Engineering Lead

## Context
HeatSense handles multi-dimensional gridded weather variables (time, latitude, longitude, variables), tabular feature matrices for ML training and inference, and geographic boundary polygons for India states and cities. We need storage formats that are open, standardized, fast, and avoid unnecessary server infrastructure like an RDBMS for the MVP.

## Options considered
1. **Raw CSV + SQLite**: Easy to inspect, but slow, inefficient for multi-dimensional spatio-temporal arrays, lacks metadata preservation, and has large disk overhead.
2. **NetCDF4 / Zarr for gridded fields + Apache Parquet for tabular features/predictions + GeoJSON for boundaries**: Standard scientific formats. NetCDF/Zarr provides native multi-dimensional indexing, CF-compliant metadata, coordinate arrays, and lazy chunked reads via xarray. Parquet provides columnar compression, high-performance serialization, and native schema preservation for pandas/scikit-learn/XGBoost. GeoJSON provides human-readable vector boundaries for administrative lookups.
3. **PostgreSQL with PostGIS**: Powerful spatial query capabilities, but introduces database provisioning, credentials, migration overhead, and extra operational complexity before query patterns are established.

## Decision
Adopt **Option 2**:
- Use **NetCDF4** (with `h5netcdf` / `xarray`) for storing gridded climate reanalysis datasets (`.nc`).
- Use **Apache Parquet** (`pyarrow` engine) for tabular feature pipelines, train/test splits, and precomputed prediction tables.
- Use **GeoJSON** for country, state, and city boundary polygons and centroid lookup catalogs.
- Store all dataset metadata, coordinate systems, variable units, and checksums in accompanying JSON manifests following `DATASET_MANIFEST_TEMPLATE.json`.

## Consequences
- No database daemon required to run local development or test suites.
- Direct compatibility with standard geospatial/scientific Python libraries (`xarray`, `pandas`, `geopandas`, `scikit-learn`).
- Highly reproducible: data artifacts can be versioned and checked with SHA-256 hashes.
- If spatial search or multi-tenant filtering needs exceed file-based speed in later phases, repository interfaces will decouple the data access layer for a PostGIS migration.

## Evidence
`xarray` + `h5netcdf` benchmark sub-second sliced reads on local SSDs for gigabyte-scale datasets. Parquet provides 70-85% compression ratios over CSV with zero-copy deserialization in PyArrow.

## Revisit conditions
Revisit if concurrent write concurrency or spatial geometry indexing across millions of arbitrary polygons requires spatial indexing (R-Tree / GiST).

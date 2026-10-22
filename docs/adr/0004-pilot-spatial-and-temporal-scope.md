# ADR 0004: Pilot Spatial and Temporal Scope (India Feasibility Region)

- Status: Accepted
- Date: 2026-10-22
- Owner: Lead Orchestrator & Data Engineering Lead

## Context
ERA5-Land provides hourly reanalysis data on a ~9 km (0.1° x 0.1°) global grid. The whole landmass of India spans approximately 8°N to 37°N and 68°E to 97°E (nearly 30° x 30° = 90,000 grid points). At 8,760 hours per year with multiple variables (temperature, dewpoint, solar radiation, wind, pressure), one year of full India data would exceed 15-20 GB uncompressed per variable, overwhelming local developer machines and causing multi-hour data download/processing times.

We must define a focused, representative pilot scope that allows fast, reproducible development and testing while covering real geographical heterogeneity (coastal, urban, mountainous, inland plain).

## Options considered
1. **Full India 10-Year Dataset Immediately**: Tens of millions of rows, ~200+ GB disk, high risk of Out-Of-Memory crashes and network timeouts during agent workflows.
2. **Single Grid Point (e.g. New Delhi only)**: Computationally light, but cannot validate spatial grid rendering, animated camera flight bounding boxes, regional spatial aggregation, or multi-cell map interactions.
3. **Western India / Maharashtra Regional Bounding Box**:
   - Bounds: 18.0°N to 20.5°N, 72.5°E to 74.5°E (approx 26 x 21 = 546 grid cells at 0.1° resolution).
   - Encompasses major urban center Mumbai, suburban Thane, Western Ghats mountain ridge, and inland plateau Pune/Nashik.
   - Time span: Representative full calendar year (8,760 hours), plus a heatwave slice (March-June).
   - Storage size: ~20-40 MB compressed, loads in <2 seconds, fits comfortably in RAM (<500 MB).

## Decision
Adopt **Option 3**. The initial pilot domain is defined as:
- **Spatial Bounds**: `[18.0, 72.5, 20.5, 74.5]` (min_lat, min_lon, max_lat, max_lon) in WGS84 CRS (EPSG:4326).
- **Grid Resolution**: 0.1° (~9 km ERA5-Land native spacing).
- **Grid Cell Count**: 26 latitudes × 21 longitudes = 546 grid cells.
- **Reference Locations**: Mumbai (18.9°N, 72.8°E), Pune (18.5°N, 73.8°E), Thane (19.2°N, 72.9°E), Nashik (20.0°N, 73.8°E).
- **Temporal Span**: A full continuous 12-month period for pilot validation and chronological ML evaluation.

## Consequences
- Fast, deterministic data acquisition and feature engineering in CI and local dev.
- Comprehensive spatial verification: covers coastal sea-breeze microclimate, orographic elevation changes, and inland heat conditions.
- System pipelines remain fully parameterized by bounding box and time range, allowing expanding to all of India once the architecture is verified.

## Evidence
546 cells × 8,760 hours = 4,782,960 data points. In Parquet format, this compresses to ~35 MB and trains Random Forest and XGBoost in ~1-2 minutes on the local 16-core AMD Ryzen 9 5900HS machine.

## Revisit conditions
Revisit when the complete pipeline, API, globe rendering, and CI gates pass Gate D (Product Integration), prior to initiating Stage 8 scale-up.

# HeatSense Data Quality and Feasibility Report

**Generated:** 2026-10-22T14:01:28.659080+00:00  
**Dataset ID:** `heatsense_india_pilot_era5_land_v1`  
**Region:** Western India / Maharashtra (Mumbai-Pune Domain)  
**Bounding Box:** `[18.0, 72.5, 20.5, 74.5]`  

## 1. Summary Statistics
- **Total Rows:** 2,384,928
- **Unique Grid Cells:** 546 (~9 km / 0.1° resolution)
- **Timesteps per Cell:** 4,368 hourly observations
- **Temporal Range:** `2024-01-01T00:00:00.000000` to `2024-06-30T23:00:00.000000`
- **Temperature Range:** 7.11°C to 36.62°C (Mean: 24.71°C)
- **Missing / Null Count:** 0 (100% complete)

## 2. Unit Conversions & Transformations
- Converted primary 2m air temperature `2t` from Kelvin ($K$) to Celsius ($^\circ C$) via $^\circ C = K - 273.15$.
- Converted 2m dewpoint temperature `2d` from Kelvin ($K$) to Celsius ($^\circ C$).
- Verified solar flux accumulation semantics and W/m² conversion.
- Assigned deterministic `grid_cell_id` values (`cell_LAT_LON`).

## 3. Storage and Scaling Feasibility
- **Gridded NetCDF file:** 45.54 MB
- **Processed Parquet file:** 47.56 MB
- **Memory Footprint:** Loaded in ~150 MB RAM with pyarrow zero-copy.
- **National Expansion Estimate:**
  - Full India (~90,000 grid cells for 1 year) is ~165x pilot spatial scale (~2.5 GB Parquet compressed).
  - Can be stored and queried efficiently in Parquet with partition by `month` or `state`.

## 4. Checksums
- `pilot_weather_grid.nc`: `6d5c9b2efea5a1f92437295b1af659b261a25fa5602799eea5035946f971dd0b`
- `pilot_weather.parquet`: `23bb8a6fa8267c15aad250cead798a38a5f0fd896b0778c51fbea72656538266`

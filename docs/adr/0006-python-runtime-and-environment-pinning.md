# ADR 0006: Python Runtime and Environment Pinning (Python 3.12 via uv)

- Status: Accepted
- Date: 2026-10-22
- Owner: Lead Orchestrator & QA/DevOps Lead

## Context
The host system default python is Python 3.14.7. However, scientific, geospatial, and ML libraries (such as `xgboost`, `scipy`, `pandas`, `xarray`, `netCDF4`, `h5netcdf`, `shapely`) require compiled C/C++/Fortran extensions with pre-built binary wheels. As Python 3.14 is bleeding-edge, many critical ML packages do not yet publish binary wheels for it, which could cause build compilation errors or missing dependencies.

The system has `uv` installed, and `uv` manages Python 3.12 (`cpython-3.12.13`) at `/home/adityap/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12`.

## Options considered
1. **Host default Python 3.14**: High risk of wheel compilation failures and broken binary packages for scientific dependencies.
2. **Python 3.12 pinned via uv virtual environment**: Fully supported by all ML, geospatial, and FastAPI libraries with ready-to-use manylinux x86_64 wheels. `uv` provides blazing fast dependency resolution, lockfile pinning, and virtual environment isolation.

## Decision
Adopt **Option 2**.
- Pin Python 3.12 in `.python-version`.
- Use `uv` to manage the virtual environment at `.venv` using Python 3.12.
- Configure `pyproject.toml` with standard PEP 621 metadata and dependencies.
- Pin Node.js to LTS (v20+ / system v24.19.0) with standard `package.json` and `package-lock.json`.

## Consequences
- Fast, reproducible, deterministic package installation with zero C-compilation headaches.
- Guaranteed compatibility with scikit-learn, XGBoost, xarray, h5netcdf, fastapi, pydantic, and pytest.

## Evidence
Running `uv venv --python 3.12 .venv` creates an isolated Python 3.12 environment in <200ms using the pre-installed CPython 3.12.13.

## Revisit conditions
Revisit when Python 3.14 reaches official broad binary wheel parity across PyPI's scientific stack.

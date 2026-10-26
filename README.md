# HeatSense: Geospatial Heat Intelligence Platform

HeatSense is an interactive geospatial heat intelligence and climate risk platform. It combines high-resolution historical atmospheric reanalysis from ECMWF Copernicus ERA5-Land with machine learning models (XGBoost and Random Forest) to monitor temperature trends and forecast thermal conditions at +24-hour and +48-hour horizons.

---

## Key Features

- **3D Geospatial Globe:** Photorealistic planetary navigation with smooth orbital camera flights to Indian cities and states, powered by CesiumJS and token-free Carto Dark Matter raster basemaps.
- **Continuous Thermal Mapping:** High-resolution 0.1 degree (~9 km native resolution) thermal grids rendered with scientific, perceptually uniform colormaps (Turbo and Magma).
- **Causal Machine Learning Forecasting:** Dedicated multi-horizon models predicting continuous temperatures at +24h (XGBoost) and +48h (Random Forest) strictly using historical observations up to initialization time without external weather forecast leakage.
- **Heatwave Hazard Classification:** Multi-model classification suite (Logistic Regression, KNN, Gaussian Naive Bayes, Decision Trees, Random Forests, and BaggingClassifier across 5, 10, 50, and 100 estimators) trained with balanced class weights to identify rare extreme heatwave alerts.
- **Sub-Millisecond Spatial Indexing:** Built-in SciPy cKDTree indexing mapping any coordinate to its nearest climate cell in under 0.2 milliseconds.
- **High-Throughput REST API:** Asynchronous FastAPI backend featuring Pydantic v2 validation, in-memory LRU/TTL caching, HTTP 304 ETag conditional caching, and dynamic Gzip compression.
- **Scientific Transparency:** Integrated model cards displaying held-out validation metrics (MAE, RMSE, R^2), baseline comparisons (persistence and climatology), and training provenance.

---

## System Architecture

```
[ Browser / Client ]
      |
      +---> CesiumJS 3D Globe (Interactive Grid Picking, Camera Flight)
      +---> Recharts (7-Day Historical & Future Forecast Trajectories)
      |
[ Reverse Proxy / Ingress ]
      |
      +---> Nginx (Microservices mode) OR Vite Dev Server (Proxying /api -> :8000)
      |
[ FastAPI Backend (:8000) ]
      |
      +---> /api/v1/health            (Service status & model readiness)
      +---> /api/v1/locations/search  (City & district spatial search)
      +---> /api/v1/map/grid          (Bounding-box GeoJSON thermal tiles)
      +---> /api/v1/weather/history   (Hourly historical climate records)
      +---> /api/v1/weather/predict   (Real-time +24h / +48h ML inference)
      +---> /api/v1/models/metrics    (Validation scores & model provenance)
      |
[ Data & Intelligence Layer ]
      |
      +---> SciPy cKDTree Spatial Index (O(log N) nearest cell lookups)
      +---> Serialized Model Artifacts (Joblib XGBoost & Random Forest)
      +---> ERA5-Land Climate Data (0.1 deg / 546 grid cells, 2.38M records)
      +---> GeoJSON State and City Boundaries (WGS84 EPSG:4326)
```

---

## Tech Stack

- **Frontend:** React 18, TypeScript, Vite, CesiumJS, Tailwind CSS, Recharts, Lucide Icons
- **Backend:** Python 3.12, FastAPI, Pydantic v2, Uvicorn, SciPy, Starlette
- **Machine Learning:** scikit-learn, XGBoost, pandas, NumPy, GeoPandas, PyArrow, Joblib
- **Deployment & Containers:** Docker, Docker Compose, Nginx Alpine

---

## Deployment and Quickstart

### Option 1: Docker Compose (Recommended for Full Stack)

Deploy both the backend and frontend microservices with Nginx reverse proxying in a single command:

```bash
# Clone the repository
git clone https://github.com/oknidhiiiii/heatsense.git
cd heatsense

# Copy environment variables
cp .env.example .env

# Build and start all services
docker-compose up --build
```

- **Frontend Application:** http://localhost:5173
- **Backend API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health

---

### Option 2: Unified Single Container Deployment

Build a unified production image that compiles the React frontend and serves both API and static UI from FastAPI on port 8000 (ideal for cloud platforms like Render, Railway, Fly.io, or Google Cloud Run):

```bash
# Build the unified container
docker build -t heatsense:latest .

# Run container
docker run -p 8000:8000 heatsense:latest
```

Access the full application and API directly at http://localhost:8000.

---

### Option 3: Local Development Setup

#### 1. Backend and ML Setup
```bash
# Create Python 3.12 virtual environment (using uv or venv)
uv venv --python 3.12 .venv
source .venv/bin/activate

# Install dependencies in editable mode
uv pip install -e .

# Configure environment
cp .env.example .env

# Start FastAPI development server
uvicorn heatsense_api.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
cd frontend
npm install

# Start Vite dev server (auto-proxies /api requests to localhost:8000)
npm run dev
```

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/health` | GET | System status, version (v0.1.0), and loaded model verification. |
| `/api/v1/locations/search?q={city}` | GET | Substring autocomplete for Indian cities and districts with coordinates. |
| `/api/v1/map/grid?bbox={min_lon,min_lat,max_lon,max_lat}` | GET | Returns GeoJSON FeatureCollection of climate grid polygons and temperatures. |
| `/api/v1/weather/history?latitude={lat}&longitude={lon}` | GET | Hourly time-series of temperature, dewpoint, solar radiation, and wind. |
| `/api/v1/weather/predict?latitude={lat}&longitude={lon}` | GET | Real-time +24h and +48h ML temperature inference with model provenance. |
| `/api/v1/models/metrics` | GET | Model card validation scores (MAE, RMSE, R^2) and baseline comparisons. |

---

## Environment Variables

Copy `.env.example` to `.env` to configure runtime options:

```bash
HEATSENSE_ENV=production
HEATSENSE_HOST=0.0.0.0
HEATSENSE_PORT=8000
HEATSENSE_LOG_LEVEL=info
HEATSENSE_CORS_ORIGINS=["*"]
```

---

## Scientific Principles

1. **Strictly Causal Predictions:** No lookahead bias. All features available at forecast initialization time $t$ use only historical observations ($t-k$) and calendar astronomical positions.
2. **Clear Provenance:** Historical observations, reanalysis estimates, and machine learning predictions are explicitly labeled in all API responses and UI panels.
3. **Reproducibility:** Machine learning artifacts and preprocessing transformers are versioned and stored with verifiable metadata manifests.

---

## License

This project is licensed under the MIT License.

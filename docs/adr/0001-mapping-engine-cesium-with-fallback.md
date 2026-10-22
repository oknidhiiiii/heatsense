# ADR 0001: Mapping Engine — CesiumJS Globe with Abstracted Adapter

- Status: Accepted
- Date: 2026-10-22
- Owner: Lead Orchestrator & Geospatial Lead

## Context
HeatSense requires a 3D globe visualization with smooth animated camera flights from space/country view down to state and city levels, rendering interactive gridded heat layers. CesiumJS is the candidate library. However, Cesium ion typically requires an API token for default terrain and proprietary imagery. We must support running completely locally without requiring a paid token, while allowing optional ion token injection via environment variables. Furthermore, the frontend must encapsulate map interactions inside an adapter boundary to avoid coupling UI components to Cesium specifics.

## Options considered
1. **Direct CesiumJS coupled to React components**: Fast to prototype, but leaks Cesium specifics into state management, makes unit testing difficult, and tightly binds to ion credentials.
2. **CesiumJS behind an Abstracted Map Adapter with Open Basemaps**: Use CesiumJS with standard WMS/TMS/OpenStreetMap or Natural Earth imagery provider when no Ion token is provided, while supporting Ion if `VITE_CESIUM_ION_TOKEN` is present. Wrap all camera flights and grid rendering behind a clean interface (`IMapAdapter`).
3. **MapLibre GL JS (2D only)**: Great 2D performance, but does not provide the 3D globe perspective and planetary flight experience mandated by PRD Section 1 & 6.

## Decision
Adopt **Option 2**. We use CesiumJS wrapped in a modular `IMapAdapter` interface. The implementation will:
- Check for `VITE_CESIUM_ION_TOKEN`. If absent, fallback gracefully to open imagery (e.g., OpenStreetMap / Carto / offline raster tiles) and WGS84 Ellipsoid terrain without throwing runtime crashes or blocking user navigation.
- Isolate camera flights, layer toggling, cell picking, and destroyed lifecycle cleanup inside a dedicated controller (`CesiumMapController`).
- Maintain an architecture compatible with a future 2D MapLibre fallback adapter if low-power client devices require it.

## Consequences
- Full 3D animated camera travel is achieved as required by PRD FR-01 and FR-04.
- Zero mandatory payment or registration for developers running the application locally.
- Map code is decoupled from page layout and UI state.
- Bundle size for CesiumJS is large (~3MB+), requiring Vite code-splitting and static asset copying for Cesium assets (Workers, Assets, Widgets).

## Evidence
CesiumJS 1.119+ supports `createWorldImageryAsync` with Ion credentials, or standard `UrlTemplateImageryProvider` / `OpenStreetMapImageryProvider` with Ellipsoid terrain without an Ion account.

## Revisit conditions
Revisit if client hardware performance on target low-end devices is inadequate, or if bundle/asset constraints mandate a lightweight 2D WebGL renderer.

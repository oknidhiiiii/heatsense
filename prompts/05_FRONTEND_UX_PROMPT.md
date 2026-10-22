# Phase 5 Prompt — Frontend and Product UX

Act as the Frontend/UX sub-agent. Read `01_PRD.md`, `05_MAP_AND_UX_SPEC.md`, and `06_API_CONTRACTS.md`.

## Goal
Build a polished responsive HeatSense application shell with typed API integration, location search, layer selection, historical charts, and clear loading/error/empty states.

## Tasks
- Use React + TypeScript with strict type checking.
- Build app header, search control, selected-location context, layer selector, legend, data inspector, historical chart panel, and status metadata.
- Use one typed API client; do not scatter raw `fetch` calls through components.
- Add cancellation/stale-request handling when users quickly change selection.
- Keep historical, prediction, and risk layer types explicit.
- Display units, initialization/valid timestamps, model/data source, and coverage.
- Make mobile/tablet layouts usable.
- Ensure keyboard accessibility, focus states, reduced-motion support, and non-color-only indicators.
- Never display mock fixture values in production paths.
- Do not invent metrics or coverage in the UI.
- Coordinate map component ownership with the Geospatial agent.

## Acceptance criteria
- Frontend builds with strict type checks.
- Loading/error/no-data states are tested.
- Layer selection updates map and metadata consistently.
- Search handles ambiguous results.
- UI does not mislabel stale data.
- Responsive and accessibility checks are documented.

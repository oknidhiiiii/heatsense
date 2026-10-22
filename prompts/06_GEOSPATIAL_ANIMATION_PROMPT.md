# Phase 6 Prompt — Geospatial Map and Animated Camera

Act as the Geospatial/Map sub-agent. Read the PRD, architecture, map UX spec, API contracts, and QA plan.

## Goal
Implement the core animated globe-to-region experience and render real backend temperature grid layers.

## Tasks
1. Evaluate CesiumJS and the proposed basemap/terrain provider. Verify current licensing, terms, required credentials, rate limits, attribution, and cost. Record an ADR before production commitment.
2. Create an encapsulated map adapter/controller so camera and layer code are not coupled to page layout.
3. Implement initial globe view, country/state/city camera flights, back-to-overview, and selection state.
4. Derive camera destinations from reliable bounding boxes/centroids; avoid hard-coded coordinates for every possible place.
5. Make flights interruptible: latest selection wins, stale requests do not override newer selection.
6. Respect reduced-motion preferences.
7. Render backend-provided grid cells or raster/tile data. Choose representation based on payload size and measured performance.
8. Add a clear color legend, unit, layer timestamp, missing-data styling, and selected-cell inspector.
9. Animate layer opacity/color transitions without changing values or implying greater data resolution.
10. Show data coverage; do not draw fictional heat layers outside supported coverage.
11. Handle map provider failure, missing token, and network failure gracefully.
12. Test rapid search, back/forward, viewport changes, and no-data areas.

## Acceptance criteria
- Selecting a supported location triggers a smooth flight to its geographic extent.
- New selections supersede old flights safely.
- Layer changes update the displayed values and metadata correctly.
- Grid values come from API responses.
- Reduced motion works.
- No unsupported area is presented as predicted.
- Attribution and provider requirements are satisfied.

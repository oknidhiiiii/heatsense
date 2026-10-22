# Map, Animated Navigation, and UX Specification

## 1. Experience goal
The map is the main interaction surface. Users should feel they are travelling from a broad geographic view into a selected region. Camera animation must be smooth, interruptible, accessible, and tied to actual data availability.

## 2. Mapping choice
Use CesiumJS as the initial candidate for a 3D globe and animated camera flight. Before committing, verify current package maintenance, licensing, basemap/terrain provider requirements, API key policies, attribution, and production cost. Keep a small adapter boundary so a 2D MapLibre alternative can be introduced without rewriting all data services.

Do not commit map tokens. If a provider needs a token, use environment configuration and document setup. Do not rely on an undocumented provider endpoint.

## 3. Camera behavior
- Initial view: stable globe framing that makes supported coverage discoverable.
- Country selection: smooth camera flight to a configured/derived bounding region.
- State selection: fly to state bounds with sensible padding.
- City selection: fly to city bounds or a configured view altitude.
- Back/overview: animate to previous extent or the global overview.
- New selection during an active flight: cancel or supersede the prior flight; state must end at the latest selection.
- Invalid/ambiguous selection: do not move camera until a supported result is chosen.
- Reduced motion: reduce duration or use a non-animated camera update.
- Do not zoom so close that the selected region disappears beyond the camera frustum.

## 4. Geographic search
Search result schema should include:
- stable ID;
- display name;
- entity type: country/state/city;
- parent administrative names;
- country code;
- centroid;
- bounding extent where available;
- data coverage status.

Use local boundary metadata or an approved geocoding provider. Respect provider rate limits and terms. Cache results appropriately. Clearly distinguish a geocoded location from a location that has weather coverage.

## 5. Layers
Required layer choices:
1. Historical temperature
2. Forecast +24h
3. Forecast +48h
4. Optional heat-risk layer only after methodology is approved

Controls must show selected layer, horizon, valid time, initialization time for forecasts, unit, and model/data provenance. Do not show a forecast layer when no corresponding model output exists.

## 6. Grid overlay
- Display actual grid-cell values from the backend.
- Choose an appropriate representation: per-cell polygons, point-based grid, raster tiles, or another measured approach.
- Avoid excessive client-side geometry. Apply region bounding and zoom-dependent limits.
- Keep values associated with stable cell IDs and coordinates.
- Handle no-data cells with transparent/hatched treatment and a legend entry.
- Use consistent color domain across layers when useful for comparison.
- Include a textual legend and avoid red/green-only status encoding.
- Click/hover interaction must work without obscuring basic map controls.
- If the map visually smooths/interpolates values, label it as a visualization method, not increased data resolution.

## 7. Grid-cell inspector
On click, show:
- temperature in °C;
- selected layer and forecast horizon;
- initialization and valid timestamps;
- coordinates/grid-cell ID;
- source dataset for historical values or model/version for predictions;
- quality/no-data flag;
- optional link to a local history chart.

## 8. Dashboard layout
Recommended desktop layout:
- top bar: HeatSense identity, search, selected location, settings;
- main region: large globe/map;
- compact layer control: Historical / +24h / +48h;
- legend pinned over map;
- side panel or bottom drawer: selected region, summary stats, time series, model metadata;
- status area: data timestamp, coverage, and loading/errors.

On smaller screens, place details in a drawer and preserve accessible map controls.

## 9. Motion quality
- Prefer camera transitions that last long enough to communicate movement but do not delay frequent use; tune through usability tests.
- Use subtle layer opacity transitions.
- Do not animate every grid cell independently if this causes performance problems.
- Respect `prefers-reduced-motion`.
- Keep controls responsive during data loading.
- Add a cancel/interrupt behavior for fast repeated searches.
- Test with low-end integrated graphics and typical laptop browsers.

## 10. Loading and error states
- Initial globe loading
- Location search loading
- Camera flight in progress
- Historical layer loading
- Prediction generation/loading
- Partial grid coverage
- No data for selected location/time
- API unavailable
- Model unavailable or incompatible artifact
- Unsupported region
- Provider token/configuration missing

Each state must be understandable and must not present stale values as fresh. If old data remain visible during a layer transition, label them as stale/loading until replacement is complete.

## 11. Accessibility
- Search and layer selectors usable by keyboard.
- Visible focus states.
- Text labels for all map controls.
- Reduced motion setting.
- Color scale includes labels and numeric range.
- Provide textual chart summaries and data inspector alternative to color-only information.
- Ensure panel contrast and responsive behavior.

# Quality, Verification, and Test Plan

## 1. Quality policy
A feature is not done because it renders or because an agent says it works. It is done when acceptance criteria are linked to tests, tests are run, failures are understood, and documentation is updated.

## 2. Test layers
### Unit tests
- Unit conversions and source-variable transformations.
- Timestamp alignment and target construction.
- Lag and rolling feature correctness.
- Leakage guards.
- Spatial clipping and cell identity.
- API schema validation.
- Color scale and legend formatting.
- Camera navigation state handling.
- Cache key correctness.
- Model artifact compatibility.

### Integration tests
- Small source fixture through preprocessing to processed output.
- Train and load a small model artifact.
- Inference using a known feature fixture.
- FastAPI endpoints with mocked repository/artifacts.
- Frontend API client against fixture responses.
- Map grid layer receives and displays backend values.
- Search selection triggers camera controller and updates selected-region state.

### End-to-end tests
- Launch application.
- Search a supported city.
- Verify camera navigation completes at the intended region.
- Toggle historical/+24h/+48h layers.
- Click grid cell and verify value metadata.
- Trigger no-data and API-error states.
- Test keyboard navigation and reduced-motion mode.

### Performance tests
- Large but bounded regional grid payload.
- Map layer switching and rapid selection changes.
- API cold model load and warm inference.
- Memory use for preprocessing chunks.
- Confirm app does not request the full country grid when only a city viewport is needed.

## 3. ML validation tests
- Chronological split assertion.
- No target timestamp is used as an input feature.
- Lag features never access future records.
- Train/validation/test time windows do not overlap incorrectly.
- Metrics computed against the correct horizon targets.
- Baseline metrics always included.
- Predictions are finite and units are correct.
- Model artifact metadata matches inference schema.
- Metrics are calculated only on held-out data for final reporting.
- Hot-period and regional slice reports exist.

## 4. Data quality checks
- Required variables and units present.
- Timestamps monotonic and unique.
- Coordinate arrays match expected grid.
- Missingness report produced.
- Source manifest present.
- No silent fill of missing data.
- Data range and value sanity checks are documented.
- Sample size and geographic coverage match configured expectations.

## 5. UI quality checks
- No console errors in normal flows.
- Camera animation is interruptible.
- Reduced-motion behavior works.
- Loading indicators do not imply data are already loaded.
- Stale layers are not misrepresented as fresh.
- Legends show units and valid time.
- Mobile layout remains usable.
- Keyboard focus remains visible.
- No-data and unsupported-region states are clear.

## 6. CI expectations
At minimum:
- Python formatting/lint/type checks appropriate to project.
- Python unit and integration tests.
- Frontend lint/type checks and unit tests.
- Build frontend.
- API contract tests.
- Secret scanning and dependency audit where available.
- Build container images if Docker is used.

Pin or lock dependencies. Avoid `latest` tags for reproducible production images.

## 7. Definition of release candidate
- All required tests pass or have an explicitly accepted waiver.
- No known critical/high security issue is unresolved.
- Forecast metrics and limitations are documented.
- Dataset attribution and map provider terms are documented.
- Deployment and rollback instructions are verified.
- A fresh environment can reproduce setup from README.
- Owner signs off before public deployment.

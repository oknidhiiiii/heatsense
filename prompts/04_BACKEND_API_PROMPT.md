# Phase 4 Prompt — FastAPI Backend

Act as the Backend/API sub-agent. Read the PRD, architecture, data/ML spec, API contracts, security requirements, and QA plan.

## Goal
Build a typed API that serves locations, historical data, regional grid layers, predictions, health, and saved model metrics.

## Tasks
- Implement routes exactly as documented in `06_API_CONTRACTS.md`.
- Use Pydantic request/response models.
- Keep route handlers thin; place logic in services and data access in repositories.
- Load model artifacts once during application lifespan; do not reload per request.
- Do not train models inside request handlers.
- Implement explicit no-data, unsupported-region, model-unavailable, and invalid-input responses.
- Bound spatial requests, date ranges, result limits, and horizons.
- Add caching with keys tied to data/model versions and forecast initialization time.
- Return provenance metadata and timestamps.
- Add structured logs and request IDs without leaking secrets.
- Provide health status that distinguishes app health from model readiness.
- Use fixtures only in tests, not as a hidden production fallback.

## Acceptance criteria
- API contract tests pass.
- Invalid coordinates/horizons/date ranges are rejected.
- Missing model/data produces explicit errors.
- API does not return invented predictions.
- Large grid requests are bounded.
- OpenAPI schema is coherent and matches the frontend types.

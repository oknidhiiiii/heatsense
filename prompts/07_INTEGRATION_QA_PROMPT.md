# Phase 7 Prompt — Integration, QA, and Acceptance

Act as the QA/Integration lead. Read the PRD and all quality/security/API documents.

## Goal
Verify the full user journey from data/model artifacts through API to animated map, and report evidence for every acceptance criterion.

## Tasks
- Inspect actual repository and test commands; do not assume.
- Run Python formatting, lint, type checks, unit tests, and integration tests.
- Run frontend lint, type checks, unit tests, and production build.
- Run API contract tests.
- Run browser E2E flow: open app, search supported city, observe camera flight, select historical layer, select +24h, select +48h, click a cell, inspect metadata.
- Test invalid location, no data, missing model, API failure, stale requests, and reduced motion.
- Verify model metrics are based on chronological held-out test data.
- Verify all values have correct units/timestamps and provenance.
- Test grid request limits and cache invalidation.
- Review console/network logs for errors.
- Run dependency/security checks available in the environment.
- Create an acceptance matrix mapping each PRD FR/NFR to evidence.
- Fix defects within scope; file clear issues for remaining work.

## Restrictions
Never mark a test passed unless it was executed and passed. Distinguish not-run, blocked, skipped, and failed.

## Acceptance criteria
- Acceptance matrix is complete.
- Critical flows pass.
- All failures and waivers are documented.
- Reproduction commands are documented.
- No fabricated test evidence or metrics.

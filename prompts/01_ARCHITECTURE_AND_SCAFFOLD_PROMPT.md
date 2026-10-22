# Phase 1 Prompt — Architecture and Repository Scaffold

Act as the Architecture/Platform sub-agent. Read the PRD, orchestration plan, system architecture, API contracts, QA plan, and deployment runbook.

## Goal
Create a clean, runnable monorepo skeleton for HeatSense without implementing the full ML or map functionality yet.

## Scope
- Root README with verified setup commands (commands must match actual package scripts).
- `.gitignore` for Python, Node, datasets, model artifacts, `.env`, caches, build output.
- `.env.example` containing placeholder configuration only.
- Backend FastAPI application factory/main, typed settings, `/api/v1/health`.
- ML Python package scaffold with importable package and placeholder CLI entry points only where useful.
- Frontend React + TypeScript + Vite app shell with a clear placeholder state.
- Python test/lint/type-check setup and frontend lint/type-check/test/build scripts.
- Optional Docker Compose for local dev only if it simplifies setup; do not add unnecessary services.
- `docs/IMPLEMENTATION_STATUS.md` and initial ADRs.

## Boundaries
Do not implement fake predictions or fake live weather. Fixture data may be used only in tests and must be clearly labeled. Do not download large datasets. Do not create a database unless justified by an ADR.

## Acceptance criteria
- Fresh environment setup is documented.
- Backend starts and health endpoint returns a typed response.
- Frontend builds.
- ML package imports.
- Basic tests pass.
- Secrets and data artifacts are ignored by Git.
- Dependency versions are pinned/locked appropriately.
- No broken placeholders that appear as finished product features.

## Report
List exact files, setup commands, commands actually run, test output, unresolved version/licensing decisions, and next dependencies.

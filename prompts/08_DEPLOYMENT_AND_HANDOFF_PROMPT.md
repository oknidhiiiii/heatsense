# Phase 8 Prompt — Deployment Hardening and Handoff

Act as the DevOps/Security sub-agent with the Lead's approval.

## Goal
Prepare a reproducible deployment and handoff without making unapproved public infrastructure changes.

## Tasks
- Review deployment target, costs, licenses, credentials, data/model sizes, and provider limits.
- Ensure `.env` and secrets are ignored and not embedded in images.
- Pin dependencies and container base images where practical.
- Build a local Docker Compose setup if it is part of the agreed design.
- Add health checks and non-root execution where feasible.
- Separate development and production settings.
- Configure CORS explicitly.
- Ensure logs do not leak tokens or environment variables.
- Verify API limits and model artifact paths.
- Document fresh install, data acquisition, training, tests, start, smoke test, and rollback.
- Run a clean-environment build and smoke test.
- Do not deploy publicly, alter DNS/firewall/reverse proxy, or incur costs without explicit owner authorization.

## Acceptance criteria
- Fresh setup instructions work.
- Build and smoke tests are actually run.
- Deployment variables are documented.
- Rollback path is documented.
- Data/model version used for release is recorded.
- Remaining manual actions and costs are clearly disclosed.

# Deployment Runbook

## 1. Local development target
The first target is a reproducible local environment. Do not choose paid infrastructure until the application has a working prototype and expected data size is known.

## 2. Prerequisites
- Supported Python version selected and pinned by the team.
- Node.js version selected and pinned.
- Git.
- Sufficient disk space for the chosen data sample.
- Access to the approved historical dataset provider.
- Optional Docker and Docker Compose.
- Map provider/terrain token only if the chosen provider requires one.

Record exact versions in project configuration after verifying compatibility.

## 3. Environment setup
- Create `.env` from `.env.example`.
- Set data directories and API base URL.
- Configure map provider credentials locally if needed.
- Never commit `.env`.
- Install backend and ML package dependencies using the selected lock/packaging approach.
- Install frontend dependencies from the lock file.

## 4. Initial setup sequence
1. Run static checks and unit tests before downloading data.
2. Run the small data pilot.
3. Inspect generated manifest and quality report.
4. Train baseline and candidate models.
5. Review horizon-specific held-out metrics and forecast strategy.
6. Start backend and test health endpoint.
7. Start frontend and test map/search using fixture data.
8. Integrate actual API data.
9. Run end-to-end tests.
10. Only then evaluate a staging deployment.

Exact commands should be added to README after the implementation selects package scripts and entry points. Do not invent commands before they exist.

## 5. Docker guidance
- Use separate development and production settings.
- Pin base images to supported versions/digests where practical.
- Run containers as non-root where feasible.
- Use health checks.
- Do not copy raw data or `.env` into images.
- Mount data/model artifacts explicitly.
- Keep frontend and API configuration separate.
- Avoid exposing internal service ports publicly when a reverse proxy is used.

## 6. Production readiness checklist
- HTTPS and domain configuration reviewed by owner.
- CORS configured.
- Secrets configured outside source control.
- API size/rate limits reviewed.
- Model artifact and data manifest deployed.
- Provider terms and attribution verified.
- Logs do not leak secrets.
- Health checks and monitoring configured.
- Backup/restore strategy decided for irreplaceable artifacts.
- Rollback procedure tested.
- Owner approves deployment and any paid resource.

## 7. Release/rollback
Release:
1. Tag source revision.
2. Record model artifact ID and data version.
3. Run migrations only if explicitly required and backed up.
4. Deploy to staging.
5. Run smoke tests.
6. Obtain owner approval.
7. Deploy production.
8. Verify health, data timestamps, and model loading.

Rollback:
1. Stop promotion or route traffic back to prior revision.
2. Restore prior compatible application and model artifacts.
3. Do not delete new artifacts until diagnosis is complete.
4. Record cause and corrective action.

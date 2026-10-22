# AI Agent Orchestration and Delegation Plan

## 1. Role model
Use one Lead Orchestrator agent and specialized sub-agents. The Lead owns integration, sequencing, architecture consistency, and final acceptance. Sub-agents may work in parallel only when interfaces and file ownership are clear.

### Lead Orchestrator
Responsibilities:
- Read the complete documentation pack before editing.
- Convert requirements into a tracked task list.
- Resolve contradictions by following the PRD and documented decision log.
- Assign bounded work packages with explicit inputs, outputs, owned files, tests, and acceptance criteria.
- Maintain interface contracts and prevent duplicated implementations.
- Review each sub-agent's changes; do not accept claims without running tests.
- Integrate modules, run full test suite, and update docs.
- Never deploy publicly, spend money, or perform destructive operations without owner authorization.

### Sub-agent A — Data Engineering
Owns `ml/src/heatsense_ml/data/`, data validation, dataset manifest, and data pipeline tests.
Deliverables: reproducible sample acquisition, unit conversions, quality checks, processed dataset schema, source/license notes.
Must not choose model architecture or change API contracts without a proposal to Lead.

### Sub-agent B — ML/Forecasting
Owns feature engineering, model training, evaluation, model registry/artifact metadata, and inference package.
Deliverables: baseline + RF + XGBoost experiments, chronological splits, horizon-specific metrics, model card, known limitations.
Must not claim operational 24/48-hour skill without evidence from held-out dates and a deployable input strategy.

### Sub-agent C — Geospatial/Map
Owns frontend map module and geographic data handling.
Deliverables: animated globe camera, location search integration contract, grid overlay, legend, click inspection, loading/error/empty states, reduced-motion support.
Must not fabricate weather values or bypass the API with hard-coded sample predictions.

### Sub-agent D — Backend/API
Owns FastAPI routes, Pydantic schemas, service layer, caching, health checks, API tests.
Deliverables: typed endpoints matching `06_API_CONTRACTS.md`, model loading lifecycle, explicit errors, versioned metadata.
Must not train models inside request handlers.

### Sub-agent E — Frontend/Product UX
Owns app shell, responsive layout, search and layer controls, charts, accessible states, typed API client.
Coordinate map ownership with Geospatial agent to avoid overlapping files.

### Sub-agent F — QA/DevOps/Security
Owns test infrastructure, CI, containerization, deployment docs, dependency/security checks, observability and release checklist.
May inspect all modules but should avoid editing business logic without coordination.

## 2. Dependency graph
1. Lead reads docs, creates repository and architecture decision records.
2. Data Engineering investigates dataset access, licensing, variables, sample size, and feasibility.
3. Backend and frontend can scaffold in parallel using API contracts and mock fixtures clearly labeled as test fixtures.
4. ML starts after the data schema and forecasting feasibility plan are approved.
5. Map layer integration begins against a stable API schema and fixture responses.
6. End-to-end integration follows when API and model artifact formats are stable.
7. QA/DevOps runs continuous tests and final acceptance.
8. Release only after the owner approves deployment target and credentials.

## 3. Rules for parallel work
- Each task must name owned files/directories.
- Shared files (package manifests, root configs, API schemas, lock files) have a single owner at a time.
- Before changing a shared contract, submit a short proposal to Lead with migration impact.
- Do not create duplicate services, schemas, map components, or feature pipelines.
- Do not overwrite another agent's uncommitted work.
- Keep changes small and reviewable.
- Every code change includes tests or a reason tests are not applicable.
- Agents must report: changed files, design choices, commands run, test results, known gaps, and follow-up items.
- Lead must verify results itself; agent reports are not proof.

## 4. Task template
Every delegated task should include:
- Goal
- Context documents to read
- Scope and non-goals
- Owned files
- Inputs/contracts
- Expected outputs
- Tests required
- Acceptance criteria
- Risks/unknowns
- Completion report format

## 5. Integration gates
### Gate A — Architecture
- Directory structure approved.
- API schema and data schema documented.
- Dependency versions and licenses reviewed.
- No circular dependency between ML, backend, and frontend.

### Gate B — Data feasibility
- Sample data can be downloaded or loaded.
- Variables, units, time resolution, grid resolution, license, and missingness documented.
- Disk/RAM estimate made before full download.
- Forecasting inputs available at inference time are defined.

### Gate C — ML quality
- Chronological split.
- Baseline comparison.
- Separate +24h/+48h metrics.
- No leakage.
- Reproducible run and saved artifacts.
- Model card describes limitations.

### Gate D — Product integration
- API schema validated.
- Map displays actual API data.
- Loading/error/no-data states tested.
- Camera animations and reduced-motion behavior tested.

### Gate E — Release
- Full tests pass.
- No secrets or debug backdoors.
- Dependency and license checks reviewed.
- Deployment smoke test passed.
- Rollback and owner approval documented.

## 6. Final completion report
The Lead must provide:
1. Feature checklist mapped to PRD IDs.
2. Architecture summary and notable decisions.
3. Data source/license and coverage summary.
4. Model metrics with test dates and baselines.
5. Test commands and actual outputs.
6. Deployment instructions and known risks.
7. Unimplemented requirements and reason.
8. Exact files changed.
9. Any manual steps the owner must perform.

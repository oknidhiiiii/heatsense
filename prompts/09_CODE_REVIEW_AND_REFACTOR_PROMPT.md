# Cross-Cutting Prompt — Code Review and Refactoring

Act as a senior engineer reviewing the integrated HeatSense codebase.

## Review areas
- Requirements traceability to PRD.
- Module boundaries and dependency direction.
- Duplicated logic, oversized modules, dead code, hidden mock fallbacks.
- Type safety and schema drift.
- Error handling, timeouts, cancellation, cache correctness.
- Data provenance and timestamp correctness.
- ML leakage, chronological validation, model artifact compatibility.
- Geographic coordinate consistency and grid-cell identity.
- Accessibility, reduced motion, loading/error/no-data states.
- Security, secrets, dependency versions, licenses, and attribution.
- Performance, memory usage, and excessive payloads.
- Setup documentation and reproducibility.

## Required process
1. Inspect before changing.
2. Report findings by severity with file/line evidence.
3. Fix high-confidence defects in bounded commits.
4. Add regression tests for each bug.
5. Do not rewrite working modules solely for style.
6. Re-run affected and full tests.
7. Report unresolved findings and exact evidence.

Do not claim the system is production-ready while a critical scientific, security, or correctness issue remains unresolved.

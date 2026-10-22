# Security, Privacy, and Reliability Requirements

## 1. Secrets and configuration
- Never commit API keys, tokens, passwords, or private credentials.
- Provide `.env.example` with placeholder names only.
- Add real `.env` files to `.gitignore`.
- Use deployment secret management for production.
- Do not print environment variables or tokens in logs.
- Treat map provider credentials according to provider's public-client restrictions.

## 2. API safety
- Validate all query parameters and request bodies.
- Enforce limits on coordinate ranges, date ranges, result count, and requested grid area.
- Use stable error messages; never return stack traces.
- Set timeouts for file/network operations.
- Apply rate limiting if public traffic or expensive endpoints justify it.
- CORS must list explicit production origins, not wildcard credentials.
- Add request IDs and structured logs.

## 3. Data integrity
- Record source versions and checksums where possible.
- Keep raw data immutable after acquisition.
- Write transformed output to new versioned paths.
- Validate model artifact checksum/metadata as appropriate.
- Reject mismatched feature schemas.
- Do not accept arbitrary user-provided model artifact paths.

## 4. Reliability
- API should start with a clear health status.
- If model artifact is missing, prediction endpoints should return a clear unavailable status rather than dummy values.
- A historical layer may remain usable when predictions are unavailable, but UI must label that state.
- Cache only versioned results.
- Avoid loading large data files on every request.
- Log data/model version and request ID for inference failures.
- Define memory and timeout limits for region queries.

## 5. Scientific integrity
- Do not fabricate values to fill visual gaps.
- Distinguish reanalysis, station observation, prediction, and derived risk.
- Show initialization and valid timestamps for forecasts.
- Do not imply a 9 km grid provides street-level precision.
- Do not make health claims without a documented methodology and suitable validation.
- Disclose forecast limitations when test results do not support reliable use.

## 6. Deployment safety
- Do not deploy publicly or modify existing DNS, firewall, reverse proxy, or production services without explicit owner approval.
- Do not run destructive cleanup commands.
- Use separate development/staging/production configuration.
- Back up important persistent data before migrations or replacement.
- Provide a rollback plan.
- Restrict debug endpoints and development server settings in production.

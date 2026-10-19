# Quotas, local observability and cost

**Trạng thái:** SSI numerical quotas and user-specific service fees are unknown; no live calls have been made. App distribution is planned as open-source and free, but that does not imply SSI data service is free.

SSI docs describe API limits per API and connection key and recommend streaming for realtime use rather than frequent polling; they do not provide one universal quota for the user's entitlement. Check the current [SSI General Information](https://guide.ssi.com.vn/ssi-products/general-information) and the user's service agreement before enabling calls. Record actual limits, reset windows, concurrency, expiry and contact/escalation instructions locally without storing secrets.

## Local operation signals

Keep a user-visible local run history for:

- Request/stream group, bounded requested range, result state, received time and safe source reference.
- Rate/quota responses, retry/backoff and stop reason.
- Parser/schema drift, checksum mismatch, revisions, gaps, stale/open bars and reconciliation status.
- Local storage size, publish/export outcome and recovery status.
- Paper simulator session, feed freshness, orders/fills simulated and any pause/gap events.

Logs must not contain credentials, auth tokens, full request URLs with secret parameters, personal transaction bodies or source content not permitted for retention. No telemetry upload by default. User can export support diagnostics after preview/redaction.

## Limits and safe behavior

Until account-specific quota is measured/documented, do not assume unlimited access. Use bounded pagination/concurrency, explicit ranges, request timeouts and bounded exponential backoff respecting provider guidance. Stop on auth/terms/policy denial, hard rate quota and repeated schema errors. Avoid aggressive polling or fallback to undocumented/private endpoints.

Hosted DB/storage/auth/egress, Model Lab worker budgets and project telemetry are deferred. Local no-fee software does not remove the user's own SSI service costs, data terms or Windows resource limits.

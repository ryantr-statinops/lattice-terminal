# Security và privacy

**Trạng thái:** local-first policy direction; password protection, storage encryption and SSI integration are not implemented.

- All config, SSI Data credentials, market data, portfolio and research output stay on the user's computer. No project-controlled upload or telemetry by default.
- FastConnect Data only. No FastConnect Trading, broker credentials, real order execution or custody.
- ConsumerID/ConsumerSecret must be isolated from browser bundles, localStorage, URLs, logs, crash reports, fixtures and commits. Select a Windows secret store/encrypted vault before enabling real credentials.
- Local password-only login is a product request; define account/profile boundary, strong password hashing, session lock, encryption-at-rest/key management, recovery/reset and Windows threat model. Password login alone does not encrypt files.
- Local API binds loopback only. Validate origins/CSRF as relevant, bound requests, and do not expose LAN listener by default. Localhost is not a trusted security boundary against other processes under the same Windows user.
- Source rights and entitlement separately govern access, local persistence, export, research/backtest, display and retention. Do not infer rights from public docs or user-supplied credentials.
- No secret or personal portfolio/raw CSV content in logs. Support diagnostics must redact and preview before export. Never add credentials or real user market data to fixtures/tests.
- Use synthetic fixtures for development until gates pass. Clearly label synthetic/partial/stale/unavailable state.
- News engine evaluates each source's metadata/full-text/image/translation/model/retention permissions separately before integration.
- Paper simulation remains local and cannot issue real orders. Any future broker execution requires a separate product/security/legal review and is out of current scope.

V1 release must include a documented local data path, export/delete/reset behavior, backup/recovery and a secret-handling review. Hosted account isolation/JWT/managed Auth are deferred, not a security solution to reuse by default.

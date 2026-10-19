# Security và privacy

**Trạng thái:** local-first security requirements; password protection, storage encryption and SSI integration are not implemented. Technology choices remain pending ADR/review.

- All config, SSI Data credentials, market data, portfolio and research output stay on the user's computer. No project-controlled upload or telemetry by default.
- FastConnect Data only. No FastConnect Trading, broker credentials, real order execution or custody.
- ConsumerID/ConsumerSecret must be isolated from browser bundles, localStorage, URLs, logs, crash reports, fixtures and commits. Select a Windows secret store/encrypted vault before enabling real credentials.
- Local password-only login is an accepted UX requirement. Profile boundaries, password verification, session lock, encryption/key management and recovery/reset remain pending; do not assume password-based vault unlock. Password login alone does not encrypt files. Minimize secret memory copies/lifetime without promising absolute RAM zeroization.
- Local API binds loopback only. Validate origins/CSRF as relevant, bound requests, and do not expose LAN listener by default. Localhost is not a trusted security boundary against other processes under the same Windows user.
- Source rights and entitlement separately govern access, local persistence, export, research/backtest, display and retention. Do not infer rights from public docs or user-supplied credentials.
- No secret or personal portfolio/raw CSV content in logs. Support diagnostics must redact and preview before export. Never add credentials or real user market data to fixtures/tests.
- Use synthetic fixtures for product development until approval. A bounded access test needs separate [probe authorization](../03-market-research/source-register.md#access-probes-and-operating-states), reviewed entitlement/terms, secure credentials, limits and redacted evidence; it does not authorize production serving or payload retention.
- News engine evaluates each source's metadata/full-text/image/translation/model/retention permissions separately before integration.
- Paper simulation remains local and cannot issue real orders. Any future broker execution requires a separate product/security/legal review and is out of current scope.

V1 release must include a documented local data path, export/delete/reset behavior, backup/recovery and a secret-handling review. Hosted account isolation/JWT/managed Auth are deferred, not a security solution to reuse by default.

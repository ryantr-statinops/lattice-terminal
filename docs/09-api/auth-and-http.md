# Local password and HTTP boundary

**Trạng thái:** product requests password-only login for the local app. Authentication protocol and local profile model are not designed. The earlier managed Auth/JWT/email contract is superseded for V1.

## Password-only local access

The app should not require email, OAuth, hosted identity or a remote account. Before implementation, decide whether password protects one local installation or multiple local profiles, whether it encrypts data or only locks the UI, how reset/recovery works, session timeout/lock behavior and how a password change re-encrypts stored secrets. Use established password hashing and Windows secret-storage/encryption facilities after a threat-model review; never log/store plaintext passwords or SSI secrets.

A local password lock does not protect files from a Windows account administrator or malicious process running as that user. Do not describe it as full-disk encryption. Local APIs bind to loopback, validate local origin/CSRF boundaries as relevant and avoid permissive CORS; localhost is not an authorization mechanism by itself.

## HTTP conventions to carry forward

- Version local API contracts; generate/update OpenAPI with implementation.
- Use JSON UTF-8, RFC3339 timestamps with explicit UTC/offset and decimal strings for financial quantities.
- Bound body size, pagination, timeouts and accepted range. Return explicit partial/stale/unavailable/source-policy states.
- Do not put ConsumerID/Secret or tokens in URL/query strings, headers returned to browser, error details or request logs.
- Use request IDs and safe error codes; redact provider payloads and personal portfolio data from logs.
- Keep a local request/session boundary; never accept client-supplied owner/account IDs as a way to access another profile.

Hosted JWT issuer/audience, managed account ownership, signed cloud downloads and email reset flows described in prior drafts are not V1 requirements. Revisit only if the product later adds remote hosting or sync.

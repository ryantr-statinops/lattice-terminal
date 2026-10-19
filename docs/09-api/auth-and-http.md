# Local password and HTTP boundary

**Trạng thái:** product requests password-only login for the local app. Authentication protocol and local profile model are not designed. The earlier managed Auth/JWT/email contract is superseded for V1.

## Password-only local access

The app should not require email, OAuth, hosted identity or a remote account. Pending decisions: installation/profile boundary, password verifier, session lifetime/lock, whether the password participates in encryption, secret storage, key management and reset/recovery. Only if a password-based encryption design is chosen must password changes define key rewrapping/re-encryption. No such mechanism is selected today. Review the Windows threat model and established facilities before implementation; never persist/log plaintext passwords or SSI secrets.

Memory handling must minimize secret copies/lifetime and define access after lock. Runtime garbage collection, OS and crash behavior limit guarantees; do not promise full RAM zeroization. Lock behavior for local live/paper sessions remains a separate pending policy.

A local password lock does not protect files from a Windows account administrator or malicious process running as that user. Do not describe it as full-disk encryption. Local APIs bind to loopback, validate local origin/CSRF boundaries as relevant and avoid permissive CORS; localhost is not an authorization mechanism by itself.

## HTTP conventions to carry forward

- Version local API contracts; generate/update OpenAPI with implementation.
- Use JSON UTF-8, RFC3339 timestamps with explicit UTC/offset and decimal strings for financial quantities.
- Bound body size, pagination, timeouts and accepted range. Return explicit partial/stale/unavailable/source-policy states.
- Do not put ConsumerID/Secret or tokens in URL/query strings, headers returned to browser, error details or request logs.
- Use request IDs and safe error codes; redact provider payloads and personal portfolio data from logs.
- Keep a local request/session boundary; never accept client-supplied owner/account IDs as a way to access another profile.

Hosted JWT issuer/audience, managed account ownership, signed cloud downloads and email reset flows described in prior drafts are not V1 requirements. Revisit only if the product later adds remote hosting or sync.

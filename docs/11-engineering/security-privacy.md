# Security & privacy

**Tóm tắt:** Code Python do người dùng viết được tin cậy và có quyền của Windows user. Process riêng giúp quản lý lỗi/cancel, không tạo sandbox bảo mật.


Argon2id, one profile, HttpOnly SameSite cookie, lock/session expiry; Host/Origin guard, loopback, internal bearer and restricted browser proxy. No telemetry/upload. Password does not encrypt application files.

SSI CLI uses the OS keyring (Windows Credential Manager, macOS Keychain, or Linux Secret Service when available). Set/status/delete neither authorize nor test SSI. Compose can export a temporary plaintext file for a read-only secret mount; the current app does not consume it and SSI source gates remain blocked. Stopped-service password reset preserves data and invalidates sessions. Trust boundary includes the host OS account and container process; localhost/keyrings do not defend against same-user malware.

Trusted Python is a separate supervised process, not a sandbox; it has filesystem/network rights. No guaranteed RAM zeroization. User logs/tables/artifacts may contain sensitive content. Only explicit allowlisted diagnostics omit user output, paths, tokens and credentials.

Backup ZIP includes private scripts/data/artifacts but excludes verifier/runtime sessions/control tokens/source policy/OS secrets/logs. **Not encrypted.** Restore validates path/checksum/schema/size into a new root; no auto-resume. Checksums detect corruption, not malicious backups whose manifest was rewritten; restore only trusted copies.

No broad wipe/secure erase endpoint. App/browser/OS secret/backups/exports have separate [boundaries](../04-data/storage-and-retention.md#storage-inventory-and-deletion-boundaries). Production remains gated on real source/rule work and broader security/recovery acceptance. [Progress](../13-rebuild/progress.md) records checks, not a no-vulnerabilities guarantee.

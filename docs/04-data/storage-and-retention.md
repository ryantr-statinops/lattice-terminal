# Storage, retention and deletion

**Tóm tắt:** Dữ liệu ứng dụng, browser, Credential Manager và bản sao ZIP/CSV có phạm vi xóa riêng. Mật khẩu không mã hóa toàn bộ dữ liệu; backup ZIP chưa mã hóa.


SQLite is Go-owned; Python owns Parquet. No shared writable DuckDB/remote database. Password does not encrypt all files; ZIP backup is unencrypted.

## Storage inventory and deletion boundaries

| Location | Contents | Cleanup boundary |
|---|---|---|
| Default `%LOCALAPPDATA%/KestrelTerminal` or `-data` root | SQLite/WAL/SHM, profile verifier, runtime state, optional source policy | Stop services first; one DB/source deletion is not full reset |
| `workspaces/` | saved research/backtest/strategy; `.trash` | UI file deletion moves to trash; folder delete requires empty |
| `code-snapshots/` | frozen entry/helpers/params/lock | No automatic purge |
| `market/snapshots/` | synthetic Parquet/manifests | Real source retention remains gated |
| `artifacts/` | private user tables/reports | Not redacted diagnostics |
| Browser origin storage | kestrel.theme/watchlist; buffers in memory | Separate origin cleanup; no credentials here |
| Windows Credential Manager | KestrelTerminal/SSI-FC-DATA | Explicit CLI delete; not provider revocation |
| User-selected ZIP/CSV/OS copies | backups/exports | User manages copies; no all-copy discovery/removal |
| Checkout caches/build/environments | development data, isolated smoke roots | Separate from user app data |

Settings reset, data deletion, credential removal and provider revocation differ. No automatic wipe/secure erase/all-RAM zeroization guarantee. Trusted user code can write outside managed locations.

## Backup and rights

[Offline backup](../12-operations/recovery-release.md) includes SQLite, workspaces/trash, code snapshots, market and artifacts. It excludes verifier/sessions/runtime tokens/source approvals/OS secrets/service logs. Scripts/artifacts can contain sensitive user content; ZIP is not encrypted. Restore requires a new root and local password; paper books start interrupted.

No SSI retention/export rights granted. Probe does not grant persistence. Rights-aware expiry/restriction/deletion must be implemented before production ingestion. News storage is independent.

# Recovery, backup and release

**Tóm tắt:** Dừng terminal trước khi backup; restore vào thư mục mới và dùng tài khoản hiện có trong `.env`. Jobs/Strategy/Paper không tự chạy lại.


## Compose start/stop and data location

Compose stores application data in the existing host directory selected by `KESTREL_DATA_DIR` and mounted at `/data`. `docker compose down` stops the services while preserving that directory. Do not use `down -v` as a normal stop operation. Back up the selected directory only while Kestrel is stopped; restore into a separate empty directory, then point `KESTREL_DATA_DIR` at that new root. Compose startup will treat active jobs/paper sessions as interrupted and will not resume them.

```sh
docker compose down
# Back up or restore the host directory using the maintenance procedure below.
docker compose up
```

## Offline maintenance

Stop the Compose stack or native service first. Maintenance reserves port 8080 and refuses if a terminal is active. Use the same `-data` root as the selected `KESTREL_DATA_DIR` when operating on a Compose data directory. The following Windows examples use the native CLI; macOS/Linux use the corresponding `kestrel` executable and host paths.

```powershell
# Existing backup parent, outside app data; output must not exist:
./.cache/bin/kestrel.exe -backup D:/Backups/kestrel.zip
# Destination must not exist; parent must exist:
./.cache/bin/kestrel.exe -restore D:/Backups/kestrel.zip -data D:/Research/KestrelRestored
./scripts/start.ps1 -DataDir D:/Research/KestrelRestored
# The repository .env account is used after restore; no session is restored.
./.cache/bin/kestrel.exe -reset-password
./.cache/bin/kestrel.exe -ssi-credentials delete
./.cache/bin/kestrel.exe -diagnostics
```

Backup uses SQLite VACUUM INTO, then checksums workspaces/trash, code snapshots, market snapshots and artifacts. Excludes .env, profile verifier/runtime sessions/control tokens/source policy/OS secrets/service logs. ZIP is **unencrypted** and may contain sensitive scripts/output. Restore only trusted copies.

Restore checks paths/Windows aliases/links/duplicate or case collisions/checksums/SQLite integrity/schema/size; stages beside a new destination and publishes after validation. Never overwrites an existing root. Bounds: 256 MiB/file, 2 GiB total, 50,000 files. Larger migrations aren't implemented.

## Interrupted state

Restart marks active jobs interrupted; restore marks all paper allocations interrupted with no controller. Never auto-resume. Inspect ledger/cursor/positions; Assets Reconcile acknowledges cancellation of open remainder, retains cash/positions/cursor and infers no missing fills. Reserved/unsettled inconsistencies block reconciliation and need investigation. Immediate synthetic settlement is not real-market recovery.

Editing .env and restarting changes the local account; it preserves application records but does not encrypt or decrypt data. Credential deletion doesn't revoke provider keys. Windows uses Credential Manager, macOS uses Keychain, and Linux uses Secret Service when an OS keyring service is available. Compose secret export creates a plaintext temporary host file with restricted permissions; a read-only container mount does not encrypt it, and cleanup is not secure erase. The app currently does not consume the mounted secret and SSI remains blocked. App reset/browser cleanup/data/OS secrets/backups/exports are separate [boundaries](../04-data/storage-and-retention.md#storage-inventory-and-deletion-boundaries). No secure erase or automatic whole-data wipe.

## Release gates

Fixture development build only. Local acceptance/clean setup aren't production approval. SSI transport/entitlement/rights/coverage, effective rules/actions/settlement and deeper operational recovery remain blocked. Remote CI needs a later authorized push. [Progress](../13-rebuild/progress.md).

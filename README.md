# Kestrel Terminal

Local-first Vietnamese equity research terminal · Docker Compose · MIT.

**2026-10-20: fixture development build, not production-ready.** SSI entitlement, rights, coverage and exchange rules remain unverified. No live calls or real-order routing.

## Run locally with Docker Compose

Install Docker Desktop with the Compose plugin on Windows or macOS, or Docker Engine plus the Compose plugin on Linux. Docker is required; startup builds the image and may need network access to download pinned dependencies. The running fixture application does not fetch market data.

1. Copy `.env.example` to `.env`.
2. Set `KESTREL_LOCAL_USERNAME` and `KESTREL_LOCAL_PASSWORD`. Use at least 6 bytes for the password. Single-quote values with spaces or special characters. The local password is plain text in this ignored, local-only file; never commit or share it. Changes apply on restart.
3. `KESTREL_DATA_DIR` defaults to `./data` in the repository. This folder contains `kestrel.sqlite`, workspaces and artifacts, and is ignored by Git. Explicit `-data` remains available for isolated testing.
4. On Linux/macOS, set `KESTREL_UID` and `KESTREL_GID` to the owner IDs of that directory (`id -u` and `id -g`). Docker Desktop users can keep the defaults.
5. From the repository directory:

```sh
docker compose up --build
```

Open `http://127.0.0.1:8080`. Enter the configured local account to unlock the session. The password does not encrypt the data directory. Only localhost port 8080 is published. Compose runs fixture-only by default.

Stop with `docker compose down`. The host data directory persists across stop/start. Do not use `down -v` as a routine stop command; it removes the development cache volumes (not the bind-mounted host data).

## Debug with three local terminals (optional)

Use this only when investigating a service. Stop Compose first because both modes use the same `.env` and `data/` directory. Install Go 1.27.2, Node.js 22.23.1/npm 10.9.8, Python 3.12 and uv 0.11.28, then install the pinned project dependencies once from the repository root:

```powershell
npm ci
uv sync --project services/engine --frozen
go -C services/gateway mod download
```

Set a private random `KESTREL_ENGINE_TOKEN` in `.env` once. If the sample left it blank, generate and store a local 256-bit token with PowerShell:

```powershell
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$token = [Convert]::ToHexString($bytes).ToLowerInvariant()
(Get-Content .env) -replace '^KESTREL_ENGINE_TOKEN=$', "KESTREL_ENGINE_TOKEN=$token" | Set-Content -Encoding utf8 .env
$rng.Dispose(); Remove-Variable token, bytes
```

Keep the token local; it is not sent to the browser or written to logs.

Start the processes in this order, each in its own terminal at the repository root:

```powershell
# Terminal 1 — Python engine, bound to 127.0.0.1:8081
uv run --project services/engine python -m kestrel_engine --standalone --root .

# Terminal 2 — Go gateway, bound to 127.0.0.1:8080
$env:KESTREL_ENGINE_URL = "http://127.0.0.1:8081"
go -C services/gateway run ./cmd/kestrel -root ../.. -dev

# Terminal 3 — Vite UI at 127.0.0.1:5173; API requests proxy to the gateway
npm run dev --workspace=@kestrel-terminal/web
```

Open `http://127.0.0.1:5173`. Stop Vite, gateway, and engine with Ctrl+C in each terminal. If startup fails, check that `.env` has valid local account fields and `KESTREL_ENGINE_TOKEN`, verify the previous process released its port, and start again in engine → gateway → Vite order. A token mismatch is reported as a configuration error without displaying either token.

### Web development mode

Use the Compose override for Vite hot reload. It runs Vite as a separate container and publishes both UI and gateway on loopback:

```sh
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

The development UI is at `http://127.0.0.1:5173`; the gateway is at `http://127.0.0.1:8080`. Changes to Go or Python require rebuilding/restarting the service. `docker compose down` stops either Compose mode.

### SSI secret plumbing — currently unavailable to the app

The cross-platform CLI can export an OS-keyring entry to a temporary host file, and Compose can mount it read-only. This only prepares transport plumbing: the application does not consume the mounted secret, SSI source gates remain blocked, and no live SSI request is enabled. Do not add credentials until a specific capability has passed its source/rights gate and the implementation is ready.

Set SSI credentials through the local CLI (`go -C services/gateway run ./cmd/kestrel -root ../.. -ssi-credentials set`; both values are prompted without echo). Then run `-prepare-ssi-compose-secret`, set the printed absolute path as `KESTREL_SSI_SECRET_FILE` in `.env`, and start with `docker compose -f compose.yaml -f compose.ssi.yaml up`. After Compose is down, run the matching `-clean-ssi-compose-secret` command. The temporary file is plaintext on the host; the container mount is read-only. Cleanup is not secure erase. If the machine stops unexpectedly, check and clean any leftover file before reuse.

### Encrypted provider vault in Compose

Initialize the local vault key once with `go -C services/gateway run ./cmd/kestrel -root ../.. -bootstrap-vault`. To run Compose with encrypted provider credentials, prepare a temporary key file with `-prepare-vault-compose-secret`, set its printed path as `KESTREL_VAULT_MASTER_KEY_FILE` in `.env`, then start with `docker compose -f compose.yaml -f compose.vault.yaml up`. On Linux, set `KESTREL_UID` and `KESTREL_GID` to the host user's `id -u` and `id -g` so the container can read the restricted file; Windows Docker Desktop can keep the defaults. The container reads the mounted key file; the key itself is never put in `.env` or the browser. After Compose is down, run `-clean-vault-compose-secret`. The host file contains the plaintext key, is created with restricted permissions, and cleanup is not secure erase. Ordinary application backups exclude both this file and the OS keyring entry; if the key is lost, encrypted provider credentials cannot be recovered.

## Implemented / Đã có

- React → Go gateway → authenticated Python, supervised child processes and local login.
- Synthetic daily Parquet snapshots, Quant indicators and 2D charts.
- Separate Research, Backtest and Strategies file-tree editors, immutable code snapshots, logs/artifacts/history; no file tabs.
- Detailed synthetic Train/Test replay and Manual/Strategy paper books. Fictional continuous LO rules are **not** verified Vietnam-market fills.
- Named VND funds, independent allocation budgets, decimal ledger, Portfolio and settled tracking CSV preview/import/export.
- Offline checksummed backup/restore, interrupted-book reconciliation, redacted diagnostic summary.

## Verify from a development checkout

Contributor checks:

```sh
npm run typecheck
npm run lint
npm run test:web
npm run test:dev-ai
npm run build
go -C services/gateway test ./...
uv run --project services/engine pytest -c services/engine/pyproject.toml test/engine
node scripts/check-docs.mjs
node scripts/contracts.mjs
uv run --project services/engine python scripts/export-engine-contracts.py --check
```

[Docs](docs/README.md) · [Progress / remaining gates](docs/13-rebuild/progress.md) · [Recovery](docs/12-operations/recovery-release.md).

History/tag `archive/pre-kestrel-rebuild-2026-10-19` is preserved. News is independent; AI/optimization, factor research, 3D surfaces, derivatives and ETFs are later work.

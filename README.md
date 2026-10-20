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

### Web development mode

Use the Compose override for Vite hot reload:

```sh
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

The development UI is at `http://127.0.0.1:5173`. Changes to Go or Python require rebuilding/restarting the service. `docker compose down` stops either mode.

### SSI secret plumbing — currently unavailable to the app

The cross-platform CLI can export an OS-keyring entry to a temporary host file, and Compose can mount it read-only. This only prepares transport plumbing: the application does not consume the mounted secret, SSI source gates remain blocked, and no live SSI request is enabled. Do not add credentials until a specific capability has passed its source/rights gate and the implementation is ready.

Set SSI credentials through the native CLI (`kestrel.exe -ssi-credentials set` on Windows or `kestrel -ssi-credentials set` on macOS/Linux; both values are prompted without echo). Then run `-prepare-ssi-compose-secret`, set the printed absolute path as `KESTREL_SSI_SECRET_FILE` in `.env`, and start with `docker compose -f compose.yaml -f compose.ssi.yaml up`. After Compose is down, run the matching `-clean-ssi-compose-secret` command. The temporary file is plaintext on the host; the container mount is read-only. Cleanup is not secure erase. If the machine stops unexpectedly, check and clean any leftover file before reuse.

## Implemented / Đã có

- React → Go gateway → authenticated Python, supervised child processes and local login.
- Synthetic daily Parquet snapshots, Quant indicators and 2D charts.
- Separate Research, Backtest and Strategies file-tree editors, immutable code snapshots, logs/artifacts/history; no file tabs.
- Detailed synthetic Train/Test replay and Manual/Strategy paper books. Fictional continuous LO rules are **not** verified Vietnam-market fills.
- Named VND funds, independent allocation budgets, decimal ledger, Portfolio and settled tracking CSV preview/import/export.
- Offline checksummed backup/restore, interrupted-book reconciliation, redacted diagnostic summary.

## Verify from a development checkout

Native toolchain checks remain available to contributors:

```sh
npm run typecheck
npm run lint
npm run test:web
npm run build
go -C services/gateway test ./...
uv run --project services/engine pytest
node scripts/check-docs.mjs
node scripts/contracts.mjs
uv run --project services/engine python scripts/export-engine-contracts.py --check
```

[Docs](docs/README.md) · [Progress / remaining gates](docs/13-rebuild/progress.md) · [Recovery](docs/12-operations/recovery-release.md).

History/tag `archive/pre-kestrel-rebuild-2026-10-19` is preserved. Changes are committed on `main`; no automatic push. Owner renames the remote later. News is independent; AI/optimization, factor research, 3D surfaces, derivatives and ETFs are later work.

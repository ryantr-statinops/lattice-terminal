# Kestrel Terminal

Local-first Vietnamese equity research terminal · Windows · MIT.

**2026-10-20: fixture development build, not production-ready.** SSI entitlement, rights, coverage and exchange rules remain unverified. No live calls or real-order routing.

## Start on Windows

Install Node **22.23.1** / npm **10.9.8**, Go **1.27.2**, uv **0.11.28** and Python **3.12** (uv can install Python). From the checkout:

```powershell
./scripts/setup.ps1
./scripts/start.ps1
# Open http://127.0.0.1:8080
# In another PowerShell:
./scripts/stop.ps1
```

Create a local password (6–1024 UTF-8 bytes) at first launch. It locks the session, not disk encryption. Development: `./scripts/dev.ps1`, UI on `http://127.0.0.1:5173`; use the same host throughout login.

Default data: `%LOCALAPPDATA%/KestrelTerminal`, separate from source. `start.ps1 -DataDir <path>` selects another root; use the same root for stop/maintenance. Stop before rebuilding the executable. Installation needs network; fixture runtime assets/services are local.

## Implemented / Đã có

- React → Go gateway → authenticated Python, supervised Windows processes and local login.
- Synthetic daily Parquet snapshots, Quant indicators and 2D charts.
- Separate Research, Backtest and Strategies file-tree editors, immutable code snapshots, logs/artifacts/history; no file tabs.
- Detailed synthetic Train/Test replay and Manual/Strategy paper books. Fictional continuous LO rules are **not** verified Vietnam-market fills.
- Named VND funds, independent allocation budgets, decimal ledger, Portfolio and settled tracking CSV preview/import/export.
- Offline checksummed backup/restore, interrupted-book reconciliation, redacted diagnostic summary.

## Verify

```powershell
npm run typecheck
npm run lint
npm run test:web
npm run build
go -C services/gateway test ./...
uv run --project services/engine pytest
node scripts/check-docs.mjs
node scripts/contracts.mjs
uv run --project services/engine python scripts/export-engine-contracts.py --check
uv run --project services/engine python scripts/smoke-windows.py
```

[Docs](docs/README.md) · [Progress / remaining gates](docs/13-rebuild/progress.md) · [Recovery](docs/12-operations/recovery-release.md).

History/tag `archive/pre-kestrel-rebuild-2026-10-19` is preserved. Direct commits on main, no automatic push. Owner renames remote later. News is independent; AI/optimization, factor research, 3D surfaces, derivatives and ETFs are later work.

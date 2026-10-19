# Kestrel Terminal

Local-first Vietnamese-market research terminal. MIT licensed; Windows clone-and-run. Rebuild implementation is in progress: see [approved design and milestones](docs/13-rebuild/README.md). The previous fixture prototype is preserved in Git tag `archive/pre-kestrel-rebuild-2026-10-19`.

## Current runtime

React UI, Go gateway and Python engine foundation. Every market capability is fixture-only. No SSI credentials, live provider calls, live-order routes or production approval are included. Backtest, Strategies, Assets and Portfolio are separate milestones; the milestone ledger records completed work and limitations.

## Development

Toolchain: Node 22.23.1/npm 10.9.8, Go 1.27.2, Python 3.12, uv 0.11.28.

```powershell
npm ci
npm run build
go -C services/gateway test ./...
uv sync --project services/engine --python 3.12
uv run --project services/engine pytest
```

The UI dev server binds 127.0.0.1:5173 and proxies /api to Go at 127.0.0.1:8080. Windows setup/launcher scripts are added in the next milestone. Real SSI entitlement, rights, coverage and detailed-data availability remain unverified.

Direct commits on main are authorized for this rebuild. No automatic push; the remote is retained until the owner renames it.

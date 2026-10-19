# Kestrel Terminal rebuild

Approved 2026-10-19. This document supersedes prototype implementation descriptions while the rebuild is in progress. Git history and tag `archive/pre-kestrel-rebuild-2026-10-19` preserve the previous implementation. Runtime code, contracts, fixtures, scripts and CI are rebuilt on `main`, one reviewed commit per milestone. No automatic push or remote rename.

## Product and boundaries

Windows clone-and-run, local-first, MIT. Stocks HOSE/HNX/UPCoM first. News is independent. Expansion: factor research, parameter surfaces/3D, derivatives, then ETFs. AI training and parameter optimization remain deferred.

React/TypeScript/Vite/Tailwind/React Router/TanStack Query UI; Go gateway owns auth, jobs, workspaces, SQLite and funds/ledger; Python FastAPI owns SSI, Parquet/DuckDB, analytics and workers. NumPy/pandas/TA-Lib for verified indicators. Monaco ESM and chart assets are local. Windows data root: `%LOCALAPPDATA%/KestrelTerminal`.

Backtest and Strategies have separate files, contracts and runs. Navigation is a sidebar file tree, editor in the center, results/logs on the right; no file tab strip. Research scripts have their own contract. Literal `KESTREL_KIND` is inspected with AST, never executed for discovery. Every run snapshots entrypoint/helper files, params, dataset and dependency versions.

Train/Test means non-overlapping research/evaluation periods, without automatic optimization. Code is trusted local Python with OS-user permissions, not sandboxed. UI lock or tab close does not stop services/jobs. Service restart never silently resumes paper trading.

Assets manages named VND funds and allocation budgets. Manual and Strategy paper sessions can run concurrently with independent allocation ledgers; allocations cannot exceed available fund capital. Backtest copies capital configuration and never changes fund balances. Tracked/imported trades and simulated fills remain distinct. Decimal financial accounting; weighted average cost basis.

One local password-locked profile, Argon2id verifier, HttpOnly session cookie. Password does not encrypt all files. SSI secrets use Windows Credential Manager and a CLI flow, not browser storage. Built-in networking is source-gated; arbitrary trusted scripts are not a network sandbox.

## Milestones and truthful status

All milestones begin pending; only verification recorded with the relevant implementation commit establishes completion.

1. Branding/specification/MIT.
2. Baseline/reset and buildable skeleton.
3. Windows launcher/supervision.
4. Login/secrets.
5. Persistence/jobs/artifacts.
6. Market contracts/synthetic fixtures.
7. Daily ingestion/snapshots.
8. Daily Market UI.
9. Verified basic Quant.
10. SSI evidence/capability gates.
11. Intraday/stream reconciliation.
12. Effective-dated rules/fill models.
13. Sidebar workspace editor.
14. Research worker/artifacts.
15. Separate detailed-data Backtest engine.
16. Backtest workspace/Train-Test.
17. Fund ledger/allocations.
18. Paper execution.
19. Strategies workspace/worker.
20. Assets/Manual paper.
21. Portfolio/CSV/reporting.
22. Recovery/release verification.

## External gates

SSI remains documented but untested, rights unconfirmed and unapproved. No live call or credential collection is authorized by this rebuild. A scoped probe needs separate authorization. Account-specific coverage, retention/export/research rights, quota and schemas must be verified before production use. Historical intraday OHLC alone does not establish trade/order-book coverage sufficient for detailed fills. Unsupported capabilities remain blocked; no daily-open fallback.

Rules are venue/instrument/effective-date specific and require evidence. Missing fees/tax, corporate actions, session states or data must not be silently invented. Synthetic rule packs only test mechanics and never approve real-market rules.

## Verification

Build/typecheck/UI, Go and Python tests; API drift and Markdown links; Windows clean startup/shutdown; secret boundaries; immutable run snapshots; causal data APIs; event idempotency; concurrent budget reservations; stale/gap blocking; atomic snapshots; crash/restart and backup/restore. Fixtures passing does not mean production readiness.

# Rebuild progress / Trạng thái — 2026-10-20

**Fixture development build; production NOT ready.** Hai phần cuối Portfolio và recovery/local acceptance đã được triển khai. Các capability SSI thật và mô phỏng thị trường thật còn thiếu cả evidence lẫn implementation; không coi đủ commit là đủ production.

Dockerfile, regular/dev/SSI Compose configurations, a multi-architecture CI build and Linux lifecycle smoke script are now present on `main`. They provide the intended local packaging path; container build and lifecycle acceptance still depend on the Docker-enabled CI runner and have not been run in this checkout.

## Git / Milestones

Directly on main, no push, original history and tag `archive/pre-kestrel-rebuild-2026-10-19` preserved. The 22-part commit sequence is retained. Final recovery commit is identified by its subject because embedding its own hash would change it.

1. `a79b1d4 docs: brand Kestrel Terminal and record rebuild decisions`
2. `226f856 chore: replace prototype with Kestrel runtime foundation`
3. `1fe47bf feat: supervise local services with Windows launcher`
4. `19b8c27 feat: protect local sessions and Windows SSI credentials`
5. `4b58adb feat: persist runs events and immutable workspace snapshots`
6. `12be5ea feat: define strict market contracts and synthetic equity fixtures`
7. `5cb6e22 feat: publish checksummed daily Parquet snapshots offline`
8. `47eaade feat: add authenticated daily market workspace`
9. `33f62f8 feat: add verified causal quant indicators and analytical charts`
10. `10b37c7 feat: enforce independent SSI probe and production gates`
11. `ef67387 feat: reconcile stream ordering freshness and shared subscriptions`
12. `b420b9a feat: gate effective venue rules and detailed quote fills`
13. `560f060 feat: add sidebar file workspaces with local Monaco editor`
14. `b9d64bb feat: execute immutable research programs in supervised workers`
15. `7a054b4 feat: build separate causal detailed-event backtest engine`
16. `c9943d0 feat: separate backtest workspace and freeze Train Test runs`
17. `b97ef41 feat: manage named funds and atomic allocation budgets`
18. `5753e05 feat: reserve paper orders and post idempotent simulated fills`
19. `a4bffdf feat: bind separate strategy workers to paper allocation leases`
20. `5d92ae1 feat: add Assets budgets and atomic manual paper replay`
21. `583f8c2 feat: value portfolios and import settled tracking trades atomically`
22. `feat: add offline recovery and verify fixture release boundaries` (this milestone).

## Checks recorded locally

- Part 21: Go store/API tests, frontend typecheck/lint/build passed; transaction-consistent Portfolio, no allocation double-counting, missing-price NAV/P&L, settled tracking CSV atomicity/idempotence/chronology/formula-safe IDs.
- Go regression: all packages passed. Includes finance concurrency/idempotence, frozen Train/Test/engine hash, Host/Origin/auth/session expiry, workspace path safety, snapshot immutability, restart, backup/restore/path/checksum/reconciliation tests.
- Python: **35 passed**, including independent indicator formulas, prefix causality for all 12 exposed indicators, strict UTC/decimal models, source gates, effective venue/board rules, workers and separate execution contracts. No warnings after Starlette upgrade.
- Web: **7 passed**, typecheck/lint/build passed. Component/API tests cover unavailable values, CSV preview invalidation, exact decimal display, separate templates and session lock handling.
- Windows integration smoke passed twice consecutively after the bounded wire-body consumption fix (no retry masking): auth/HTML/static routes, Windows alias-path rejection, Market/Quant, research/artifact registry, detailed Train/Test/report, wrong-kind rejection, Manual/Strategy/lock, order retries, CSV, >200 SSE replay events, Stop/restart/crash and child process cleanup, offline backup/restore/new profile.
- Browser spot check: Market candles and Backtest sidebar/Monaco render. Not a complete visual or accessibility regression suite; narrow editor viewport needs horizontal scrolling.
- Generated gateway response schemas / 38 routes and internal OpenAPI/market schemas checked. External request OpenAPI/TS SDK generation remains incomplete.
- Markdown relative paths/headings: **65 files passed**. Legacy prohibited market terms absent from docs. No real credentials or SSI calls used.
- npm audit (including dev dependencies): **0 advisories**. pip-audit 2.10.1: **no known vulnerabilities** among auditable installed Python packages; local editable project skipped. Patched Monaco's DOMPurify to 3.4.17 and Starlette to 1.9.0. These are point-in-time audit results, not a vulnerability-free guarantee.
- At the time of this review, clean Windows setup and smoke passed using the former setup script; the current supported procedure is Compose-first with optional direct terminal commands documented in the root README. Remote GitHub CI has not executed for unpushed commits.

## Delivered recovery boundaries

Offline ZIP uses SQLite VACUUM INTO plus managed workspaces/trash, code snapshots, market and artifacts. Checksums/path/device/case/schema/size validation; restore only into new root. Verifier/sessions/control tokens/source approvals/OS credentials/logs excluded. ZIP is unencrypted and may contain private user code/output. No automatic erase or all-copy deletion claim.

Interrupted allocations require explicit reconciliation; open remainder is cancelled, positions/cash/cursor retained, no inferred fills. Restore never auto-runs sessions. Password reset preserves data and does not decrypt all files. [Operations](../12-operations/recovery-release.md).

## Still missing / blocked before real-data V1

1. SSI account-specific entitlement, access, rights, field/history/quota and approval evidence. No probe is authorized by these commits.
2. SSI access and rights remain unverified. SourceGate-protected `SecuritiesDetails` (HOSE/HNX/UPCOM equities), `IndexList` (HOSE/HNX), `DailyOhlc` (HOSE equity), `IndexComponents` (observed HOSE membership snapshots) and `DailyIndex` (HOSE/HNX observations) paths authenticate through the local vault, paginate, normalize and publish immutable Parquet snapshots. Market reads provider datasets only under explicit venue-specific routing policies; index instruments appear in the provider catalogue. These paths are offline-tested only, and no account-backed call has been made. Daily bar/index publication timing, quantity/value units, currency, retention rights and simulation eligibility remain unverified. Other instrument classes/venues, historical constituent membership, durable page checkpoints, intraday data, streaming transport/reconnect/backfill and rights-approved retention still need implementation or evidence.
3. Approved detailed historical data plus venue/board/class/effective-date rule packs, calendars, costs, auctions/price limits and corporate actions.
4. Real settlement availability-time accounting/recovery. Current Go paper ledger supports **fictional immediate synthetic settlement only**, and rejects other settlement dates.
5. Production fill realism and globally shared exchange liquidity across allocations. Current allocations replay independent synthetic clocks and do not reconstruct queues or missing fills.
6. Stronger large-history memory/storage/retention policy, broader crash/fault injection and browser/a11y coverage. Lazy Monaco (~2.7 MB) and Plotly (~1.16 MB) produce bundle-size warnings.
7. Complete external request OpenAPI/generated consumers and richer statistical report comparison. Basic side-by-side Backtest metrics/provenance comparison is implemented.

## Accepted decisions, not open questions

One profile; password locks session, not disk encryption. Host OS keyring via CLI; Compose secret export is temporary plaintext plumbing and is not consumed by the current app. Go SQLite/Python Parquet ownership. Trusted unsandboxed workers. Separate Research/Backtest/Strategy contracts and sidebar files. UI lock/close doesn't stop jobs. VND/weighted-average funds and independent allocations. No real orders or cloud runtime.

News remains independent. Model Lab/AI training/optimization, factor research, 3D surfaces, derivatives and ETFs remain later work. Remote rename belongs to the owner. No automatic push.

## Handoff / Bàn giao

Tracked working tree is clean after the final commit. Build/test caches and the isolated local validation clone remain ignored under .cache. Test services are stopped; no user default profile/credentials were used. No push performed.

## Terminal UI redesign — 2026-10-20

Owner-approved terminal styling, offline monospace fonts, Appearance, shared controls/dialogs and workspace interaction polish are implemented locally on main. No push. See the [UI review report](../10-ui-ux/terminal-review.md) for the current frontend checks, screenshots and commit-by-commit review record. Earlier checks above are historical rebuild evidence, not results rerun for this UI change.

# Product rules / Quy tắc sản phẩm

The approved [rebuild](../13-rebuild/README.md) and [constraints](../CONSTRAINTS.md) govern implementation.

1. Keep data local; built-in browser networking is loopback; upstream source access is separately gated.
2. Preserve provenance, synthetic status, quality and unavailable output; do not invent zeros/fills.
3. Separate Research, Backtest and Strategy entrypoints/files/history; only data/math/indicator/report helpers are shared.
4. Freeze code/helpers/params/lock and selected data/rules per run; later edits do not mutate it.
5. UI visibility/lock does not own job lifetime. Stop, failure and service interruption differ.
6. VND funds/allocations use transactional decimal accounting; no double counting or implicit liquidation.
7. Tracking settled records and simulated fills remain separate.
8. Session password is not disk encryption; SSI secret uses Windows Credential Manager via CLI.
9. No live source calls without scoped authorization/evidence; no real-order routes.
10. News stays independent; Model Lab/optimization/3D/future classes stay deferred.
11. Rebuild commits are directly on main, one per milestone, no automatic push or remote rename.

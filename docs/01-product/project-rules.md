# Product rules / Quy tắc sản phẩm

The approved [rebuild](../13-rebuild/README.md) and [constraints](../CONSTRAINTS.md) govern implementation.

1. Keep data local; built-in browser networking is loopback; upstream source access is separately gated.
2. Preserve provenance, synthetic status, quality and unavailable output; do not invent zeros/fills.
3. Separate Research, Backtest and Strategy entrypoints/files/history; only data/math/indicator/report helpers are shared.
4. Freeze code/helpers/params/lock and selected data/rules per run; later edits do not mutate it.
5. UI visibility/lock does not own job lifetime. Stop, failure and service interruption differ.
6. VND funds/allocations use transactional decimal accounting; no double counting or implicit liquidation.
7. Tracking settled records and simulated fills remain separate.
8. Session password is not disk encryption; SSI credentials stay in the OS keyring and are never put in browser state, Git or logs. Compose's temporary secret-file export is plaintext plumbing only; it does not enable SSI access.
9. No live source calls without scoped authorization/evidence; broker access is read-only and there are no real-order routes.
10. Ingest all asset classes offered by selected providers; simulation stays unavailable until that class has approved data, effective rules and a fill model.
11. Broker account snapshots stay separate from local fund ledgers. News stays independent; Model Lab/optimization/3D remain deferred.
12. Local notifications include inbox, badge and toast; Telegram is optional and replay delivery defaults to the app only. Gmail is out of scope.
13. Each code change has one independently reviewable behavior and is made directly on main; no automatic push or remote rename.

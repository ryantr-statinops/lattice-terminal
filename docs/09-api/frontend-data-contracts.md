# Frontend data contracts

Generated [routes](../../contracts/gateway-routes.json), [Go response DTOs](../../contracts/gateway.schema.json), [market models](../../contracts/market.schema.json) and [internal OpenAPI](../../contracts/engine.openapi.json) replace removed prototype contracts.

Resources: managed workspaces; independent runs/states/SSE; checksummed artifact registry/download; funds/allocations/leases; manual paper; Portfolio/recorded settled CSV; interrupted-book reconciliation.

Literal KESTREL_KIND is inspected by AST. Backtest run(context) is separate from Strategy on_event(context,event), optional on_start/on_stop. Research has its own output context. Runs freeze source/helpers/params/uv.lock and reference selected data/rules. Params must be an object.

Money/price/quantity are decimal strings, time is UTC/offset ISO. Null is unavailable, not zero. Completed/failed/cancelled/interrupted differ. Reconcile cancels open remainder without inventing missing fills.

Gateway request DTOs and frontend TS types are maintained in code, not a fully generated SDK. Route/response drift checks do not prove complete semantic compatibility; integration tests and consumer review are required.

Engine source SHA-256 is frozen in each CodeSnapshot and verified by workers; changed engine source requires a new snapshot. Frozen Test also rejects an engine hash change. Reproducing an older run requires its matching Git/engine/dependency state.

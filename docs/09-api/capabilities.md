# Local capability contracts — planning

**Trạng thái:** no V1 local API schema is locked. The former `/workspaces`, hosted portfolio and Model Lab endpoint table was superseded by the local-first product direction.

Potential local capability groups (names illustrative, not approved routes):

| Capability | Expected responsibility | Gate |
|---|---|---|
| Health/runtime | Report local process version, status and safe config validation | Never reveal secret values |
| SSI data config | Validate local provider settings without returning ConsumerID/Secret | Entitlement and local secret storage must be implemented first |
| Instruments/reference | Serve entitlement-supported SSI instruments, market/board types and metadata | Endpoint coverage and field meanings verified |
| Historical market data | Query local snapshots with source, range, coverage, freshness and revisions | Rights, storage and quality gate |
| Live session | Start/stop permitted local stream and expose state/freshness/gaps | Stream entitlement and quota gate |
| Portfolio | Local portfolios, ledger and valuation | Currency/accounting/market rules decided |
| Backtest | Start/cancel/read a deterministic local simulation | Snapshot/strategy/fill assumptions versioned |
| Paper live | Simulated local orders/fills against permitted live feed | Must have no real-order route or trading credentials |

No news endpoints are part of first terminal MVP; the independent news engine will define its own integration contract before a later connection. Model Lab/datasets/experiments and hosted sharing remain deferred.

Each response with market state should include `as_of`, source/feed, last observed time, partial/stale flags and coverage/gap information where applicable. Exact fields, status enums, errors and OpenAPI remain to be designed alongside implementation.

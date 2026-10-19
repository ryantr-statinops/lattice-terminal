# SSI live lifecycle — local target

**Trạng thái:** target local architecture, chưa triển khai và chưa được access/rights gate. SSI official docs describe streaming groups `F`, `X`/`X-Quote`, `B`, `R`, `MI` and `OL`; see [SSI streaming documentation](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/du-lieu-streaming). It does not establish this user's entitlement, numeric quotas, replay behavior or local storage rights.

## Connection ownership

Local API/adapter process owns SSI connection and credentials. Browser connects only to a loopback endpoint with a narrow normalized contract; ConsumerID/ConsumerSecret never enter the browser. This boundary remains subject to verifying SSI's required auth/transport/connection model. Do not use the browser's direct upstream Binance WebSocket from the legacy prototype as a template for SSI.

Use SSI REST/reference/history for initial state and historical recovery; stream supports realtime display and paper simulation. Groups may include:

- `F` trading/session status.
- `X` summary and `X-Quote` quote/depth/trades/quotes.
- `B` realtime OHLCV; SSI docs say Value is currently 0.
- `R` foreign room/flows.
- `MI` index values/breadth/status.
- `OL` odd-lot trade updates.

The product should consume all feeds that prove useful and are entitled, but do not merge their distinct semantics. In particular keep odd-lot, derivative/bond and regular-board data distinct; `B` provisional values do not replace historical candles.

## States and reconciliation

Proposed local states: disabled → validating configuration → connecting → snapshot/reconcile → live → stale/reconnecting → suspended/closed. UI should identify source, market/session state, event time, local received time and data age. Open/provisional bar, last closed bar and paper fill are separate concepts.

On start/reconnect, obtain permitted REST snapshot/history, buffer incoming updates, reconcile overlap and only then publish a monotonic local view. Duplicate/out-of-order events must be idempotent or flagged. Disconnect gaps remain explicit until history recovers them. Never synthesize missing bars or treat quote updates as executed paper fills without a simulator rule.

The stream owner uses bounded subscriptions and retries based on the actual SSI entitlement/quota. Auth, quota, policy, market-closed and network failures are distinct. Stop on auth/terms errors; do not retry forever or proxy around a restriction. If the API cannot restore a gap, label affected data partial/unavailable.

## Lifecycle and privacy

Starting the local application opens the stream only when required by the visible feature or a configured local paper session. Closing/stopping the app closes local subscriptions and flushes only permitted local state. The process must not silently become a Windows background service in V1. No auto-upload, project telemetry or remote relay by default.

Password lock/logout behavior, whether local live sessions continue while UI is locked, and app-stop recovery need to be defined with the password/storage design. Localhost binding is not a substitute for access control.

## Acceptance gates

- SSI entitlement and rights are documented separately for the selected stream groups and REST reconciliation inputs.
- Integration tests cover unauthorized/config missing, quota errors, market closed, duplicate/delayed/out-of-order events, dropped connection, overlap corrections, partial recovery and application stop/restart.
- No secret appears in browser network requests, build assets, URLs, logs, fixtures or crash metadata.
- Paper fills are generated only by the simulator contract and are permanently labeled simulated; no route can send real orders.
- Local chart reports data source, market/session state, freshness, open/closed status and unresolved gaps.

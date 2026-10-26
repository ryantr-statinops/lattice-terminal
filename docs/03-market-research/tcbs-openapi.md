# TCBS OpenAPI capability research

**Review:** 2026-10-26. Official portal/documentation review only. No TCBS credential, endpoint request, account access or persisted provider payload was used.

## Product and market coverage

This dossier concerns the official [iFlash OpenAPI portal](https://developers.tcbs.com.vn/), which is distinct from the community TCBS data source currently registered in the app. Existing community adapter methods that call VNDIRECT do not count as TCBS OpenAPI coverage.

Official pages describe stocks on HOSE/HNX/UPCOM and derivatives. The documented OHLC endpoints also name `stock`, `coveredWarr`, `index` and `derivative` as symbol types. That proves documented endpoint input classes; it does not prove history, streaming, entitlements or every field are available for each class.

## Documented datasets

| Dataset | Official reference | Evidence and open scope |
|---|---|---|
| Intraday OHLCV | [`/nyx/v2/stock/bars`](https://developers.tcbs.com.vn/docs/v1.0.0/stock/bars/) | Minute/hour resolution, `to` Unix seconds and `countBack`; response bar timestamp is ISO-8601 UTC. Exact resolution limits, class coverage, corrections and retention require confirmation. |
| Long-term OHLCV | [`/nyx/v2/stock/bars-long-term`](https://developers.tcbs.com.vn/docs/v1.0.0/stock/bars-long-term/) | Daily/weekly/monthly, `to` and `countBack`; timestamp is ISO-8601 UTC. Adjustment/corporate-action history and max count remain open. |
| Price matching history | [`/nyx/v1/intraday/{ticker}/his/paging`](https://developers.tcbs.com.vn/docs/v1.0.0/stock/price-history/) | Paginated trade records with price, volume, action and time. Page retention and raw exchange timestamp semantics need verification. |
| Equity live board | Official WebSocket developer guide and TCBS technical specification. | Realtime stock market channels on the normal stream; requires authenticated session and heartbeat. Need map channel IDs/fields and venue coverage from the current versioned spec before coding. |
| Derivative live board | [Derivative WebSocket guide](https://developers.tcbs.com.vn/docs/v1.0.0/derivative/ws-price-board/) | Trades, bid/offer top levels and session summary; separate stream and channel IDs. Contract symbols are TCBS-specific and roll over. |
| Derivative contract catalogue | Referenced by the derivative guide as `GET /api/v1/derivatives/contracts`. | Mapping between TCBS active symbols and exchange contracts must be retained with effective dates. |
| Price history/supply-demand stream | [Ouranos WebSocket](https://developers.tcbs.com.vn/docs/v1.0.0/stock/ws-history/) | 1-minute price history and supply/demand; foreign-trading flow in 15-minute buckets. These are distinct datasets, not raw exchange ticks. |
| Account data | Portal markets account and portfolio management; individual read endpoints must be inventoried from the account/asset documentation. | Confirm exact read operations for accounts, cash, positions, transactions and order/fill history, plus per-account access. Omit transfer/trading writes. |

## Authentication and connection lifecycle

The portal documents API Key + OTP exchanged for a JWT through `/gaia/v1/oauth2/openapi/token`. JWT validity is up to 8 hours. The portal also documents API-key expiry information/extension calls. Store API key/token in the local secret boundary and implement reauthorization/refresh as documented; never ask for OTP as a recurring background credential.

The WebSocket guides require an authenticated text frame and endpoint-specific text heartbeats every two seconds. Stock and derivative channels/endpoints differ; derivative docs say one connection per token is the safe usage and the public docs do not publish a firm rate limit. Reconnect requires a valid refreshed token and renewed subscriptions. Do not share one parser or heartbeat assumption across both streams.

## Rights, costs and unknowns

The portal describes registration through TCInvest and API-key creation. Public docs recommend fewer than 10 REST requests/second and one WebSocket per token, while noting no hard REST limit. Confirm the account's actual quota, fees/plan, field access, history depth, retention, local storage/backtest rights and any rate exceptions before enabling ingestion.

## Adapter acceptance checklist

- Keep official `tcbs-openapi` and existing community `tcbs-community` as distinct provider IDs and evidence records.
- Split stock, covered warrant, index and derivative adapters wherever endpoint semantics/coverage differ.
- Split intraday bars, long-term bars, trade history, live board and aggregated supply/demand datasets.
- Normalize all timestamps from the documented UTC representations; retain source timezone/value in ingestion evidence.
- Store the TCBS derivative symbol mapping with its effective interval; never identify a future by symbol alone.
- Inventory account read methods individually and exclude transfer/order-write methods.

**Current state:** public API docs establish several documented datasets; no credentials, account entitlement, access test, rights confirmation, production approval or simulation coverage is established.

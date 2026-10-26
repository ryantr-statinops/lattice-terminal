# SSI FastConnect provider profile

**Status checked: 2026-10-27.** FastConnect Data is the market-data service. FastConnect Trading is a separate service with separate authentication and includes order-writing routes; this product uses no order-writing route. Public documentation establishes endpoint shape, not this installation's entitlement, retention, display, research, or backtest rights.

## Service and registration

FastConnect API registration currently requires an SSI trading account and registration through an SSI office or account executive. The registration guide says API credentials are created in iBoard, includes a consumer ID and secret, and requires registering a fixed IP for the FastConnect service. The public Data access-token endpoint accepts `consumerID` and `consumerSecret`; whether this deployment's credentials or network address are approved is unverified. See [service registration](https://guide.ssi.com.vn/ssi-products/service-registration) and [FastConnect Data API specs](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs).

## Public Data endpoint inventory

The documented REST base is `https://fc-data.ssi.com.vn/api/v2/Market`. Data calls use a bearer access token from `POST Market/AccessToken`. The published specs show these REST operations:

| Endpoint | Dataset | Documented fields and constraints | Repo status |
|---|---|---|---|
| `GET Securities` | Venue security list | `market` may be HOSE, HNX, UPCOM, or DER. `pageIndex` 1–10; `pageSize` 10, 20, 50, 100, or 1000. | Not wired into normalized catalogue path. |
| `GET SecuritiesDetails` | Instrument details | Same page bounds. Includes ISIN, symbol, security type and exchange; types listed are stock, covered warrant, futures, ETF, bond, open-end fund and mutual fund. Exchange values include HOSE, HNX, HNXBOND, UPCOM and DER. | Implemented separately for HOSE, HNX and UPCOM stocks (`ST`/`S`) through local ingestion; other classes/venues are not normalized. |
| `GET IndexList` | Index catalogue | Requires `exchange` (`HOSE` or `HNX`), pages 1–10 at up to 1000 rows. Returns `IndexCode`, `IndexName`, and `Exchange`. | Implemented separately for HOSE and HNX with explicit capability gates, normalized index instruments and immutable local catalogue snapshots. |
| `GET IndexComponents` | Index constituents | Requires `indexCode`, supports pages 1–10 at up to 1000 response rows, and nests `IndexComponent` entries under index rows with `Isin` and `StockSymbol` fields. The published example places a stock symbol such as `ACB` in `Isin`, so the field's identifier semantics are not reliable from the example alone. | Implemented for selected HOSE indices as a current observed snapshot through the local vault, SourceGate, immutable Parquet and explicit Market routing. Preserves `Isin` as a provider-reported identifier without claiming it is an ISIN; historical effective membership is unavailable. |
| `GET DailyOhlc` | Daily OHLCV/value | `symbol`, `fromDate`, `toDate`, `pageIndex` 1–10, and page sizes through 1000. Date format is `dd/mm/yyyy`. Response has `TradingDate`, `Time`, OHLC, volume and value; volume/value are described as normal matched totals. | Implemented for HOSE equities through explicit store/display SourceGate checks, a complete paginated read, normalized immutable snapshot and Market route. The current parser preserves OHLC/volume decimals; provider value is not persisted. Price currency/unit, adjustment policy, release time and historical depth still need confirmation. |
| `GET IntradayOhlc` | Intraday OHLCV | Same date and page limits; optional `resollution`, default 1 minute. | Documented, not implemented. Supported resolution values, history depth and timestamp timezone need confirmation. |
| `GET DailyIndex` | Daily index observations | `indexId`, `fromDate`, `toDate`, page indices 1–10, page sizes through 1000 and optional ascending order. Response includes index value, change/ratio, trade counts, matched/put-through/total volume and value, advances/declines, session and optional time; the official sample includes HNX30. | Implemented as separate HOSE and HNX daily-observation datasets, not candles. Provider time is retained without timezone inference; quantity/value units and value currency remain explicit unknowns. Publication timing, account access and rights remain pending. |
| `GET DailyStockPrice` | Daily security prices and activity | Date range and pagination; `market` may include HOSE, HNX, UPCOM, DER and BOND. Response includes `Closepriceadjusted` as well as unadjusted-looking price fields and activity measures. | Not implemented; adjusted and unadjusted semantics need validation against an entitled sample. |

For the documented paged operations above, the public spec describes page indices 1–10 and a maximum page size of 1000. It does not publish a request-rate quota, total history depth, correction/revision policy, data release schedule, or retention/deletion terms. Do not infer any of these from an HTTP response.

## Streaming, identity, and data semantics

The Data streaming guide lists message families for quotes (`X-QUOTE`), trades (`X-TRADE`), and OHLC updates (`B`), with date/time, symbols, exchange/session/status and price/quantity fields for relevant messages. The guide warns that subscribing to all symbols can produce high volume. Public material reviewed here does not establish stable sequence IDs, replay after reconnect, gap backfill, concurrent subscription limits, or timestamp timezone semantics. The streaming adapter therefore remains disabled.

`SecuritiesDetails` provides ISIN, symbol and listing/contract fields. The current parser uses ISIN when available and keeps SSI source identity; it normalizes HOSE, HNX and UPCOM stocks into separate venue capabilities. Alias lifecycle, ticker changes, instrument reuse, exact board mapping and data publication time require account-backed samples before extending the normalizer to other classes and venues.

The `DailyOhlc` example contains numeric strings such as `28600` and `23382100`, but the API schema does not state price currency or scale. The endpoint describes volume as normal matched volume and value as normal matched value. The separate daily price response includes a `Closepriceadjusted` field, but the docs do not fully define its adjustment basis or effective timing. The current adapter preserves provider-native OHLC and volume decimals, leaves currency/units/adjustment/revision unknown, treats `TradingDate` as a Vietnam-local daily period and records the local observation time as availability; it does not persist the response's value field. It excludes the current Vietnam date because publication timing is undocumented. Market only reads the snapshot when SSI is explicitly routed for HOSE daily candles and display rights are approved. The bars remain unavailable for simulation.

`IndexComponents` is stored as a point-in-time provider response observed by the local ingestion runtime. It carries no historical effective date, and the reported total symbol count remains separate from the number of distinct normalized rows. The sample's `Isin` value is kept in a neutral `provider_security_id` field because the public example does not establish that it contains an ISIN. Market displays the snapshot only when SSI is explicitly routed for HOSE index constituents and the exact display scope is approved. Constituent history and use in point-in-time backtests remain unavailable.

`DailyIndex` is preserved as a separate daily observation with field-level unit labels. The published schema does not define the scales for `IndexValue`, `Change`, or `RatioChange`; the adapter preserves these provider-native values and marks their scales unverified. Activity counts are counts. The provider does not document the quantity units, value currency, timezone for `Time`, revision policy, or publication schedule. The adapter keeps the time string as reported, records local observation time as availability, and excludes the current Vietnam date until release timing is verified. HOSE and HNX series are separate capabilities, each browsable only under its explicit SSI venue route and approved display scope; neither is enabled for simulation.

## Account operations and rights

FastConnect Trading is a separate product and token flow. Its docs list read operations including cash balance, stock positions, derivative positions and order history. The same product also exposes order placement, modification and cancellation; those write operations are excluded. Trading credentials, OTP requirements, account/subaccount coverage, transaction-history coverage, retention rights and access to individual read endpoints must be verified separately. See [FastConnect Trading API specs](https://guide.ssi.com.vn/ssi-products/fastconnect-trading/api-specs).

Public documentation does not confirm local retention, display, derived-data, export or backtest rights, commercial pricing, historical quotas, or the user's package entitlements. Obtain written entitlement and rights evidence before enabling data storage or serving it beyond an explicitly authorized scope. No SSI account call or paid service was used to prepare this profile.

## Capability state in this repository

- **Implemented, offline-testable:** normalize HOSE, HNX and UPCOM equity catalogues and synchronize each through its separate local Go vault → Python adapter → SourceGate → immutable Parquet snapshot → Market instrument catalogue capability. The same gated path supports separate SSI HOSE and HNX index catalogues and DailyIndex observations, SSI HOSE equity DailyOhlc and observed HOSE IndexComponents snapshots; Market reads data only under the corresponding implemented venue route and exact capability scope.
- **Waiting for account/access:** authentication against a real account, provider response validation from an entitled sample, fixed-IP approval and credential-specific capability test.
- **Waiting for rights:** local storage, display, derived data and research/backtest use. The app must keep the capability blocked until its exact scope is approved.
- **Not implemented:** intraday data, non-equity security normalization, streaming, durable page resume, historical replay/backfill, historical constituent membership and all FastConnect Trading account reads.
- **Production readiness:** not ready. Offline mocks prove parser and gate behavior only; they do not prove SSI access or permission.

## Evidence

- [SSI FastConnect Data API specs](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)
- [SSI FastConnect Data streaming](https://guide.ssi.com.vn/ssi-products/fastconnect-data/streaming-data)
- [SSI service registration](https://guide.ssi.com.vn/ssi-products/service-registration)
- [SSI FastConnect Trading API specs](https://guide.ssi.com.vn/ssi-products/fastconnect-trading/api-specs)
- [Repository SSI entitlement evidence](../13-rebuild/ssi-evidence.md)

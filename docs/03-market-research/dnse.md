# DNSE OpenAPI capability research

**Review:** 2026-10-26. Official documentation review only. No DNSE credential, endpoint request, account access or persisted provider payload was used.

## Products and documented capabilities

The [DNSE developer portal](https://developers.dnse.com.vn/) describes separate Trading API, Broker API and Market Data API products. Its [market-data catalogue](https://developers.dnse.com.vn/docs/dnse/market-data/) documents:

| Dataset | Documentation evidence | Scope still to verify |
|---|---|---|
| Historical OHLC | Open, high, low, close and volume for stocks, derivatives and market indices over selected intervals and date ranges. | Exact symbol classes, supported resolutions, maximum range/page size, timezone, adjusted/raw semantics, corrections and history depth. |
| Instrument details | Filtered list of basic securities information. | Exchanges/classes, stable identifiers, delisted history and update cadence. |
| Daily/security status | Reference/ceiling/floor values and trading status on a session day. | Per-venue semantics, timestamps and historical availability. |
| Latest trades | Most recent matched trade. | Whether timestamp/sequence are sufficient for durable event ordering. |
| Trade history | Matched trades over a selected board and period. | Retention, pagination, correction policy and board coverage. |
| Price-level trade statistics | Aggressor-side buying/selling volume by price during the session. | Exact aggregation window and whether history is retained. |
| Bid/ask snapshot and history | Current bid/ask plus depth history by board and time range. | Depth levels, event timestamps, pagination, retention and entitlement. |
| Foreign-investor data | Foreign investor activity. | Exact fields, room versus flow semantics and availability time. |
| Session/indicative price | Current session and indicative matching price. | Trading-session codes and auction-specific interpretation. |
| Index history | Historical index information. | Exact fields, intervals and whether the catalogue phrase refers to OHLC or price-level trade statistics. |
| Corporate actions | Upcoming/current corporate-action events. | Historical completeness, corrections and point-in-time availability. |
| Closing prices | In-session security closing price data. | Final versus provisional status and correction behavior. |
| Trading calendar | Trading dates for approximately one year from the current date. | Special sessions, historical calendars and exchange-specific coverage. |

The portal overview describes stocks, derivatives, indices, realtime market changes and order-book depth. It does not establish that every listed market dataset supports every asset class. Map each endpoint to its own capability after inspecting the endpoint specification.

## Authentication and account access

The [API platform guide](https://developers.dnse.com.vn/docs/guide/intro/api_platform/) says an API Key and API Secret are issued after OpenAPI registration. The secret signs most REST calls. The guide describes a second-factor mechanism for trading operations (Smart OTP or Email OTP); those write operations are excluded from this product.

The portal advertises realtime account asset/status/order information in the Trading API description. Exact read-only endpoints, permissions, pagination and retention must be confirmed from endpoint specifications and the user's account entitlement. Implement only a semantic allowlist of read operations; do not expose broker order/create/amend/cancel operations. API Key presence is configuration evidence only, not connectivity or entitlement evidence.

## Rights, price and limits

The public developer docs describe a developer-facing OpenAPI product but do not establish the user's data rights, personal access, local retention/backtest rights, fees, quotas, production limits, market-data history depth or account read permissions. Resolve these with DNSE before storage, display, live operation or paid usage. No probe is authorized by this review.

## Adapter acceptance checklist

- Keep stock, derivative and index OHLC as separate capability records.
- Inventory every remaining market-data dataset above as its own provider task when endpoint details are sufficient.
- Preserve original timestamp, board, price/volume units, source revision and publication/availability time.
- Test missing-depth sentinels and partial records without converting them to valid zero-price data.
- Add historical/live/account capabilities only after their exact rights and entitlement are established.
- Keep all trading write paths absent.

**Current state:** documented market-data catalogue; no credential configured, access test, rights confirmation, production approval or simulator coverage established.

# VPBankS NeoAPI capability research

**Review:** 2026-10-26. Official documentation review only. No account login, credential, endpoint request or stored provider payload was used.

## Access and environments

The [NeoAPI documentation](https://neoinvest.vpbanks.com.vn/neo-openapi/docs/overview) describes a partner API requiring a VPBankS account, NeoAPI registration, granted permissions and IP allowlisting. It documents separate UAT and production API hosts and a limit of 5 REST requests/second per client. Authentication returns a JWT that expires after 10,800 seconds (3 hours). The registered IP, exact account permission, environment availability and applicable limit must be confirmed before connection.

## Market datasets

| Dataset | Official evidence | Scope still to verify |
|---|---|---|
| Security list | [`GET /stock/stockList`](https://neoinvest.vpbanks.com.vn/neo-openapi/docs/market/stock-list) supports market codes HOSE, HNX, UPCOM, FU and ALL, with pagination. | Delisted/history coverage, code lifecycle and whether ALL mixes underlying classes. |
| Stock/index market data | Intro describes index, security list, price detail and derivative market endpoints. Market WebSocket lists `marketInfo`, `marketSession`, `marketVolume`, `stockInfo`. | Exact index/venue mappings, field freshness and whether REST offers historical series. No documented historical OHLC endpoint was confirmed in this review. |
| Equity market stream | Stock stream documentation includes three bid/ask levels, daily OHLC-like values, volume/value, session, foreign flow and market status. | Update sequence, replay/gap recovery, instrument subscription limit and retention. |
| Futures | Security list includes `FU`; futures details and positions are documented. Market stream overview says stock stream includes stock data, while full futures market-stream coverage requires endpoint-by-endpoint confirmation. | Active contract catalogue, rollover, history bars and live quote channels. |
| Covered warrant | Stock-detail schema includes covered-warrant attributes such as underlying, issuer, expiry and exercise data. | Confirm distinct endpoint semantics, complete catalogue and historical price/action coverage. |
| Bonds/funds/other classes | Account-list includes account flags for bond access; public market sections reviewed do not establish a general bond/fund market-data feed. | Treat as unsupported/pending until a documented market dataset and entitlement are found. |

NeoAPI describes equities and derivatives as orderable products, but this project only consumes market data and read-only account data. Bond access flags do not prove a bond data API.

## Read-only account capabilities

Documented GET operations include:

- [`GET /accounts/accountList`](https://neoinvest.vpbanks.com.vn/neo-openapi/docs/accounts/account-list): custody account and equity/derivative subaccounts.
- [`GET /accounts/availableTrade`](https://neoinvest.vpbanks.com.vn/neo-openapi/docs/accounts/available-trade): available buying power for a selected symbol and price; retain as broker-reported account context, not local fund cash.
- [`GET /portfolio/stocks`](https://neoinvest.vpbanks.com.vn/neo-openapi/docs/portfolio/stocks): total/tradable/blocked/receiving quantities, cost, market value and P&L.
- [`GET /portfolio/derivatives/positions`](https://neoinvest.vpbanks.com.vn/neo-openapi/docs/portfolio/derivatives-positions): open and closed futures positions and VM/IM fields.
- [`GET /trading/orderBook`](https://neoinvest.vpbanks.com.vn/neo-openapi/docs/trading/order-book) and [`GET /trading/orderHistory`](https://neoinvest.vpbanks.com.vn/neo-openapi/docs/trading/order-history): read-only current and historical order records.
- Trading WebSocket exposes `/asset/{account}` and `/account/{account}` channels and documents replay sequence inputs for reconnect. Confirm exact payload/access rights and implement sequence recovery before persisting account stream events.

The broad trading WebSocket also exposes order status events. Reading those events is allowed only to reflect broker state; the app must never call POST/PUT/DELETE trading endpoints. Do not request or persist MFA codes for this product.

## Data semantics and operating limits

The [common data types](https://neoinvest.vpbanks.com.vn/neo-openapi/docs/data-types) document timezone `Asia/Ho_Chi_Minh`, equity prices in VND, futures prices in index points, and nullable/omitted fields. Preserve timezone, units and null values. Do not apply trading tick/lot constraints as a universal market-data normalizer.

WebSocket stream endpoints are documented with `ws` in some pages and `wss` in other examples. Confirm secure production URL, certificate behavior and UAT differences from VPBankS before implementing any transport. Never silently downgrade to plaintext WebSocket.

## Rights and acceptance gates

Public documentation does not establish personal subscription rights, local caching/backtest rights, account-specific coverage, cost, historical market depth or stream limits. Confirm production permissions and rights for each dataset. No network probe was authorized or made by this review.

Adapter work must keep each market dataset separate, apply the 5 RPS limit, refresh the 3-hour token, preserve pagination and timezone, and use read-only operation allowlists. Missing history remains unsupported until a documented endpoint and entitlement exist.

**Current state:** documented market/account capability catalogue; credentials, IP authorization, dataset rights, access tests, persistence rights and simulator coverage remain unverified.

# HayInsights Open API

**Rà soát:** 26/10/2026. **Trạng thái:** public REST docs use `X-API-Key`; endpoint availability and quota are plan-gated. Suitable as an enrichment provider, especially for non-candle time series, but not a replacement broker feed. Access, dataset rights and production terms must be verified against the account plan and terms.

## Official catalogue

The [Open API docs](https://developer.hayinsights.com/) enumerate REST datasets for commodities/history, crypto market/on-chain/derivatives metrics, ETFs and funds (holdings, NAV growth, price history), FX, macroeconomic series/exchange rates, and real-estate statistics/GeoJSON. The [FAQ](https://hayinsights.com/en/about-us/faq) describes US, Japan and Vietnam market coverage, including macro, equities/indices, funds/ETFs, FX, bonds, crypto, commodities, real estate, derivatives, news sentiment and event calendar. FAQ notes that domain and per-minute quota depend on plan; API access with credits is associated with Pro, and it currently advertises a limited-time promotion. Recheck current price/terms at implementation time.

## Integration facts and boundaries

- API docs demonstrate HTTPS `api-v2.hayinsights.com/openapi/v1/...`, `X-API-Key` authentication, JSON envelopes, and explicit 400/401/403/429/500 errors. Example responses show metadata timestamps, currency and units such as `USD/ton`; treat examples as schema guidance, not licensed fixture payloads.
- 403 may mean feature is not in the plan; 429 indicates rate limit. Connector should map these to access/quota status rather than “connected”. Public evidence does not establish key expiry/rotation, exact quotas, pagination, historical depth, correction/revision behavior, SLA or sandbox.
- Several datasets are snapshots or analytical series, not executable prices. Determine cadence, timezone, release/publication timestamp, source, units, revisions and permitted point-in-time use for every endpoint.
- Funds/ETF NAV, macro releases, FX, bond yields, real-estate and crypto metrics need typed non-candle records. Do not normalize them to equity candles.
- Do not assume Vietnamese individual stocks, broker account/balance/positions, transaction history, orders, trade ticks, depth or live market streaming are available simply because broader market categories are listed.
- Public docs do not establish local persistence, display, derived data, backtest, redistribution or export rights. Confirm terms for the exact API plan before storage/use.

## Implementation disposition

Inventory each OpenAPI endpoint and capture docs/spec version, plan feature and representative permitted payload before creating a P-task. Initial status: **catalogued; credential and plan/rights required**. Prefer enrichment and reference series when contract supports it. Keep API key in Go-managed secret store and do not expose it to Strategy code. Gate unsupported domains independently; never promote the provider as a real-time broker feed without evidence.

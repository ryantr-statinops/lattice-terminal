# Ma trận coverage provider × dataset

**Rà soát:** 26/10/2026. Trạng thái là mức bằng chứng tài liệu công khai, không phải quyền truy cập thực tế.

| Provider | Catalogue/instruments | Historical prices | Live price/trade/quote | Corporate/financial/macro | Read-only account | Access & rights |
|---|---|---|---|---|---|---|
| SSI FastConnect | HOSE/HNX/UPCoM catalogue documented | OHLCV/intraday documented | REST/stream documented; topic-specific | Corporate actions documented | Account query documented separately from data token | Registration, credentials/OTP, fixed IP and rights need account/product confirmation. |
| DNSE | Market-data catalog documented | Stock/futures/index candle documented | Market APIs/stream docs need operation inventory | Corporate action and auxiliary market datasets documented in catalog | Broker API exists; exact read endpoints/rights to inventory | API key/secret; API access/OTP and quota by endpoint need account confirmation. |
| TCBS official OpenAPI | Equity/derivative instruments documented | Stock/covered warrant/index/derivative bars documented | Stock/derivative streams documented | Some market data; full auxiliary catalogue unresolved | Account operations not yet confirmed from endpoint docs | API key/OTP/JWT docs; terms/access require account. Keep distinct from community adapter. |
| VPBankS NeoAPI | Stock/universe docs; equity/derivative details | Historical dataset details need inventory | Market and trading streams documented | Limited reference/market details; full catalogue unresolved | Accounts, buying power, positions/order history docs | Account/IP whitelist, JWT and quota; production rights need approval. |
| VNDIRECT | DChart symbol behavior observed in repo, no official catalogue contract | DChart UDF daily/1m observed only | No official live capability confirmed | No confirmed dataset via public DChart | Open API organization channel mentioned; endpoint set private/unconfirmed | DataFeed package currently suspended; DChart use/storage rights unconfirmed. |
| FiinGroup | Reference data catalogued | Stock EOD, derivatives, bond/fund endpoints catalogued | Live/stream semantics not settled per endpoint | Broad corporate, financial, corporate action, fund NAV, bond, macro catalogue | Not evidenced as broker account API | Commercial access; quota, prices and data rights need contract. |
| Vietstock | Portal coverage exists; API inventory private | API or Sync Data advertised, exact history unknown | Unknown | Company, financials, bonds, ETF, futures, macro portal categories; feed coverage unconfirmed | Not evidenced | Vendor confirmation, current package/pricing and rights required. |
| FireAnt | REST OpenAPI catalogue; IDs/coverage per route | Historical/market routes need schema inventory | Streaming not confirmed by REST docs | Company/finance/fund/reference categories in spec | `accounts-read` scope documented | OAuth implicit currently documented; plan/rights/flow suitability need confirmation; exclude all write scopes. |
| HayInsights | Tickers/series vary by domain | Commodity, ETF and selected series history catalogued | Real-time broker-grade stream not established | Macro/FX/bond yield/fund/ETF/real estate/crypto and more catalogued | Not evidenced | API key; domain/quota plan gated; rights verify at account level. |
| WiGroup WiFeed | API feed advertised, inventory not public in reviewed page | Unknown | Unknown | Financial data API advertised, details unknown | Not evidenced | API key and commercial terms; docs, dataset matrix, rights and price required. |

## Ý nghĩa status và quyết định routing

- **Documented:** official docs/pages name the capability. Still requires schema, plan, account and rights checks before routing.
- **Observed:** behavior exists in repository or public portal but no API entitlement/contract has been verified; not eligible for production routing.
- **Unknown:** no sufficient evidence. Do not infer unsupported data.
- **Waiting:** implementation depends on credentials, plan, agreement or additional endpoint documentation.

Registry mục tiêu phải có trạng thái tách biệt `documented`, `implemented`, `access`, `rights`, `health`, theo provider × dataset × asset class × venue. Routing chọn provider chỉ khi coverage và entitlement phù hợp; snapshot của run giữ nguồn/revision đã chốt. Không fallback ngầm hoặc đổi provenance. Dữ liệu khác asset/semantic không được convert thành candle mặc định.

## Gap cần giải quyết bằng R15/P tasks

1. Lấy endpoint inventories và payload mẫu được phép cho provider/dataset chưa đủ schema.
2. Xác minh auth, token lifecycle, quotas, pagination, revisions, timezone/units, freshness và corporate action semantics theo endpoint.
3. Xác minh rights về local storage, display, backtest, derived data, export và backup.
4. Thiết kế adapter chuẩn và typed records; ingest đầy đủ dataset được phép dù chưa có simulator.
5. Gating mô phỏng theo rule/fill coverage; account read-only tách khỏi fund.
6. Chạy Strategy live/replay và đưa signal/paper/operations/risk events vào local inbox; Telegram private chat chỉ cho event policy đã bật.

Nguồn gốc bằng chứng: hồ sơ [SSI](vn-equities.md), [DNSE](dnse.md), [TCBS](tcbs-openapi.md), [VPBankS](vpbanks-neoapi.md), [VNDIRECT](vndirect.md), [FiinGroup](fiingroup.md), [Vietstock](vietstock-datafeed.md), [FireAnt](fireant-api.md), [HayInsights](hayinsights.md), [các ứng viên khác](other-vietnam-providers.md).

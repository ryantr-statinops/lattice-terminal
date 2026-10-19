# Source register và source gates

**Ngày review:** 2026-10-18 (historical Binance P03 follow-up plus SSI local-V1 initial review). Binance rows/decision records below preserve the previous crypto direction and are not the selected V1 provider. SSI FastConnect Data is the current provider direction, but its gate is still blocked. Repo hiện không chứa các P02 Binance evidence files được trỏ bên dưới, nên access-test claims chưa independently auditable. Không tạo provider account, dùng credentials hoặc ký agreement trong review. `false` nghĩa chưa đạt evidence, không nhất thiết source không hỗ trợ.

## Evidence flags độc lập

- `documented`: có primary URL mô tả capability; không chứng minh feed hoạt động.
- `access-tested`: có test record ở region/browser/runner cụ thể, response schema, thời gian và quota.
- `rights-confirmed`: có evidence cho **đúng use case**; phải tách store, ML train, public display và redistribution.
- `approved`: coordinator chấp nhận mục đích/field/retention cụ thể sau các gate cần thiết; không suy ra từ ba flag khác.

Một source có thể documented=true nhưng rights=false. Quyền price không bao gồm news. Cờ true phải có evidence URL/document/date/owner; không lưu credential hoặc account identifiers riêng vào register public.

P02 claim `BIN-SPOT-PUBLIC access-tested` được tài liệu cũ mô tả là 6 REST probes từ shell local (BTCUSDT/ETHUSDT, 15m/1h/1d, mỗi request 3 rows) và một BTCUSDT trade stream trong Chrome desktop. Các link dự kiến tới [REST probe](../../task/research-terminal-plan/evidence/p02-binance-rest-probe.json) và [browser feasibility](../../task/research-terminal-plan/p02-browser-feasibility.md) hiện không tồn tại trong checkout; do đó chưa xác minh lại response, region, schema hay thời gian. Claim chỉ là historical/unverified evidence, không dùng làm release gate. Không chứng minh REST CORS, hosting/region khác, lịch sử dài, archive, source rights hoặc production availability. Owner/evidence owner cần được xác nhận lại; ngày claim ban đầu 2026-10-16. `approved=false`.

| ID / provider + product | Lớp dữ liệu / access | documented | access-tested | rights-confirmed | approved | Store / ML / display / redistribute |
|---|---|---|---|---|---|---|
| BIN-SPOT-PUBLIC | Giá; public-only REST/WS, no key | true | historical claim; evidence file missing, re-test required | false | false | Tài liệu endpoint mô tả capability/schema; chưa tìm thấy grant cho persistent store, multi-user display, ML hoặc redistribution. Binance platform terms, geography và exact product entitlement vẫn cần owner/legal review |
| BIN-SPOT-ARCHIVE | Giá; download miễn phí có điều kiện | true | false | false | false | Vision Dataset Terms v1.0 (2026-08-26), SHA-256 `99c4921dbe023cd68c1a447775707d621453cc78aec6ac0bfe2e6c06a5114ee0`: CC BY-NC-SA 4.0 + giới hạn bổ sung; commercial utilization cần separate written enterprise license; không phù hợp MVP multi-user/public product nếu chưa có license/review |
| KRAKEN-OHLCVT | Giá; public archive | true | false | false | false | Chưa xác nhận từng mục đích |
| SEC-RELEASES | News regulator; public website | true | false | false | false | Review content/third-party fields và attribution |
| CFTC-RSS | News regulator; RSS | true | false | false | false | Review metadata/full text/derived ML riêng |
| ETH-BLOG | News project; public blog | true | false | false | false | Review license theo nội dung, image và processing |
| BTC-CORE | News project; release notices | true | false | false | false | Review notices/content; software license không đủ |
| COINDESK-RSS | News báo chí; RSS candidate | false | false | false | false | URL candidate chưa xác minh được bằng browsing; chưa có rights/history/free-prod evidence |
| SEC-EDGAR | US filings/fundamentals; public API | true | false | false | false | Review access policy, attribution, attached third-party content |
| ALPACA-PRICE | US prices; account/free/paid tiers | true | false | false | false | Entitlements, feed, storage/training/display cần review |
| ALPACA-NEWS | US news; account/provider tiers | true | false | false | false | News rights tách price; vendor approval chưa có |
| OANDA-PRICE | FX prices; account/token-gated | true | false | false | false | Broker terms và commercial redisplay chưa xác nhận |
| DUKASCOPY-HISTORY | FX historical export; free tool theo docs | true | false | false | false | Automated access/store/train/display cần review; không blanket license |
| CFTC-COT | Futures positioning; public reports | true | false | false | false | Release lag, calendar và field-specific rights cần review |
| ECB-RATES | FX reference daily; public | true | false | false | false | Review attribution/ML/cache; không intraday feed |
| FED-RSS | Macro news; public RSS | true | false | false | false | Review field-specific rights |
| ECB-RSS | Macro news; public RSS | true | false | false | false | Review field-specific rights |
| BLS-API | Macro actual; public API registration/quota cần test | true | false | false | false | Review source direct và revision/vintage coverage |
| BEA-API | Macro actual; API account/key cần xác minh | true | false | false | false | Review direct-source purposes/quota |
| FRED | Macro aggregation; public/API key | true | false | false | false | ML và API cache bị hạn chế theo terms; không eligible hiện tại |
| SSI-FC-DATA-REST | VN market/reference/history; SSI FastConnect Data REST, ConsumerID/ConsumerSecret | true | false | false | false | Official docs list token, securities/details, index list/components, daily/intraday OHLC, daily index and daily stock snapshot. Account entitlement, fees/quota/history-depth test and local cache/research/display terms unconfirmed |
| SSI-FC-DATA-STREAM | VN realtime; SSI FastConnect Data streaming by connection key | true | false | false | false | Docs describe F, X/X-Quote, B, R, MI, OL. Not access-tested; subscription limits, local retention/replay/reconciliation rights and account-specific coverage unconfirmed |
| DNSE-DATA | VN prices; account/entitlement cần xác minh | true | false | false | false | Chưa xác minh phí/store/train/display |
| CAFEF-RSS | VN news; public RSS | true | false | false | false | Metadata/full text/ML/display chưa xác nhận |
| VIETSTOCK-RSS | VN news; official RSS directory | true | false | false | false | Feed access/history/store/ML/display chưa xác nhận |
| VNECONOMY-RSS | VN news; candidate URL browsing lỗi | false | false | false | false | Chưa xác minh capability hoặc quyền |
| HNX-DISCLOSURES | VN disclosures; public website | true | false | false | false | Third-party attachments và redistribution chưa rõ |
| VNSTOCK-SDK | VN data tooling; upstream tùy provider | true | false | false | false | License code không cấp quyền upstream data |

## Evidence URLs và quyết định tiếp theo

| Source | Evidence chính thức | Việc còn phải làm |
|---|---|---|
| Binance public | [Market data only](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) | Region/CORS/CSP, rate/stream limits, terms |
| Binance archive | [Archive docs](https://github.com/binance/binance-public-data), [dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md) | Checksum, timestamp units, rights scope |
| Kraken | [OHLCVT](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data) | Coverage/license per use |
| SEC / CFTC | [SEC releases](https://www.sec.gov/newsroom/press-releases), [CFTC RSS](https://www.cftc.gov/RSS/index.htm) | Source adapter and policy review |
| Project news | [Ethereum](https://blog.ethereum.org/), [Bitcoin Core](https://bitcoincore.org/en/releases/) | Stable interface, terms and fields |
| CoinDesk | [RSS candidate](https://www.coindesk.com/arc/outboundfeeds/rss/) | Browser research trả lỗi; cần xác minh URL/documentation rồi access test và permission |
| EDGAR | [API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Fair access and historical mapping |
| Alpaca | [Price](https://docs.alpaca.markets/us/docs/about-market-data-api), [news](https://docs.alpaca.markets/us/docs/historical-news-data) | Current plan plus redistribution agreement |
| OANDA | [Pricing](https://developer.oanda.com/rest-live-v20/pricing-ep/) | Token entitlement and history tests |
| Dukascopy / COT | [Historical export](https://www.dukascopy.com/swiss/english/marketwatch/historical/), [COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) | Source rights, release availability và adapter access tests |
| ECB | [Rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html), [RSS](https://www.ecb.europa.eu/home/html/rss.en.html) | Terms and timestamp/vintage mapping |
| Fed / BLS / BEA | [Fed RSS](https://www.federalreserve.gov/feeds/feeds.htm), [BLS](https://www.bls.gov/bls/api_features.htm), [BEA](https://apps.bea.gov/api/) | Direct source policy/revisions |
| FRED | [Legal terms](https://fred.stlouisfed.org/legal/) | Keep excluded from ML/cache pending suitable permission |
| SSI FastConnect Data | [REST API list](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/danh-sach-cac-api), [streaming](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/du-lieu-streaming), [registration](https://guide.ssi.com.vn/ssi-products/service-registration), [general information](https://guide.ssi.com.vn/ssi-products/general-information) | Confirm user entitlement/fees, each product's quota/coverage/history, service term/fixed-IP requirement, and local access/cache/retention/export/research/display/deletion terms; only then perform bounded schema/quality tests |
| DNSE | [Market data](https://developers.dnse.com.vn/docs/dnse/market-data/) | Account, quota, store/train/display; outside selected V1 provider direction |
| CafeF / HNX | [RSS](https://cafef.vn/index.rss), [disclosures](https://www.hnx.vn/en-gb/thong-tin-cong-bo-up-hnx.html) | Terms, news archive, adapter |
| Vietstock / VnEconomy | [Vietstock RSS](https://vietstock.vn/rss), [VnEconomy candidate](https://vneconomy.vn/rss.htm) | VnEconomy browsing lỗi; xác minh URL rồi review rights từng nguồn |
| Vnstock | [License](https://www.vnstocks.com/onboard/giay-phep-su-dung) | Verify each upstream data provider |

## Approval record phải có

Binance Vision: xem P03 follow-up record bên dưới. License không phải MIT cho dataset; mục đích thương mại/multi-user và artifacts public phải qua scope review theo [báo cáo Crypto](crypto.md#dataset-terms-ảnh-hưởng-scope). Dùng source miễn phí không đồng nghĩa được host dịch vụ retail; riêng API/live cần terms review riêng, không suy ngược từ archive.

Source ID, purpose, allowed fields, permitted audience, geography, allowed transformations/ML, storage and deletion policy, attribution, current quota evidence, owner, review/expiry date, terms hash và disable procedure. Không nhúng secret vào URLs hoặc sample payload.

Chưa khóa numeric quota hay retention khi chưa có evidence. Giá miễn phí ở personal tier không phải budget production. Khi terms thay đổi: disable use bị ảnh hưởng, đánh dấu snapshots restricted, review derivative artifacts và không silently chuyển nguồn.

## SSI FastConnect Data — local V1 initial review (2026-10-18)

- **Product decision:** SSI FastConnect Data là provider direction đầu tiên; dùng tối đa REST/reference/stream capabilities phù hợp. FastConnect Trading không thuộc scope. App hướng open-source/free, clone-and-run local trên Windows; credentials, market records, portfolio and derived research remain on the user's machine.
- **Responsible reviewer:** product owner / local operator (identity not recorded in public docs). **Provider/source owner:** SSI. **Review date:** 2026-10-18. **Evidence type:** official documentation only; no account credentials supplied and no access test performed.
- **Official capability evidence:** [API list](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/danh-sach-cac-api), [streaming data](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/du-lieu-streaming), [service registration](https://guide.ssi.com.vn/ssi-products/service-registration), [general information](https://guide.ssi.com.vn/ssi-products/general-information).
- **Status:** `SSI-FC-DATA-REST documented=true / access-tested=false / rights-confirmed=false / approved=false`; `SSI-FC-DATA-STREAM documented=true / access-tested=false / rights-confirmed=false / approved=false`.
- **Known facts:** docs list nine REST APIs (AccessToken, Securities, SecuritiesDetails, IndexComponents, IndexList, DailyOhlc, IntradayOhlc, DailyIndex, DailyStockPrice), describe stream groups F/X/X-Quote/B/R/MI/OL, state API limits are per API and connection key without a universal numeric quota, and describe one-year service registration/renewal. Docs mention HOSE/HNX/UPCOM/DER/BOND but do not prove coverage or entitlement is uniform across API/feed types.
- **Unknown:** user's service plan, exact endpoint/instrument access, price, history depth and intraday retention, numeric quota/concurrency, fixed-IP requirement, token lifecycle, local storage/export rights, allowed research/backtest/derived use, attribution, deletion, and whether terms permit single-user local open-source use in the user's geography.
- **Gate decision:** BLOCKED for network calls and persistence of real market payload until the local operator has reviewed actual service terms/entitlement and recorded allowed purpose, fields, geography, local retention/deletion, export/display, research/backtest, attribution, quota, terms version/hash, expiry/review date and disable procedure. This records missing evidence; it does not claim SSI has denied access or use.
- **Safe preparation allowed:** synthetic fixtures, parser/normalizer design, local secret-management design and test harnesses that cannot contact SSI. Never request or commit ConsumerID/ConsumerSecret. An access test must be authorized, bounded, redact credentials and avoid persisting real payload unless retention permission is confirmed.

## Historical P03 Binance decision record — 2026-10-18

**Quyết định: BLOCKED / not approved** cho MVP multi-account retail workspace, public display, research/ML, persistent historical storage, archive redistribution hoặc public demo. Không tải, cache hay persist market payload thật trong ứng dụng/CI cho đến khi có approval record đầy đủ. Quyết định này không khẳng định Binance từ chối quyền; evidence hiện có không đủ để xác nhận quyền.

| Use case | Access capability | Rights confirmed | Decision / evidence needed |
|---|---|---|---|
| Public REST/WS access | Docs mô tả market-data-only endpoint; historical P02 probe không audit được từ checkout | false | Chỉ cho phép metadata/terms review và ephemeral connectivity test nếu phù hợp terms; cần re-test có ngày, vùng, endpoint, schema và quota |
| Persist historical candles / raw archive | Archive docs và terms URL được ghi trong register; terms chưa được lưu/hash hoặc legal-fit review | false | Block; cần terms snapshot/hash, allowed fields, retention/deletion, derived snapshots và agreement nếu use case thương mại cần |
| Multi-user/private display | Không có entitlement evidence trong repo | false | Block; xác nhận audience, territories, attribution, caching/redisplay và account/user limits |
| Research/ML and derived artifacts | Chưa có grant xác nhận | false | Block; xác nhận training/backtest, derived metrics/artifacts và quyền chia sẻ/publication |
| Redistribution/public demo | Chưa có grant xác nhận | false | Block; không phân phối raw/derived market data hay snapshot public |

**Owner:** product/source-rights owner chưa được chỉ định trong repo (engineering record: Ryan Tran). **Geography:** chưa chốt. **Terms version/hash, retention, quota, review expiry, disable procedure:** pending evidence. `BIN-SPOT-PUBLIC` và `BIN-SPOT-ARCHIVE` giữ `rights-confirmed=false`, `approved=false`. Gate chỉ được mở bằng review mới có evidence URL/document, version/hash, date, owner, region, allowed purposes/fields/audience, retention/deletion, attribution và operational disable rule.

## Historical P03 Binance follow-up decision record — 2026-10-18

**Quyết định: tiếp tục BLOCKED / not approved** cho scope sản phẩm hiện được docs mô tả (multi-account retail workspace, public/multi-user display, research/ML, persistent historical storage và public demo). Không truy cập endpoint để tải candles, không cache/persist Binance market payload, và không phát hành snapshot thật. Đây là quyết định về thiếu quyền được chứng minh cho scope này, không phải kết luận pháp lý chung về mọi cách dùng Binance data.

### Evidence reviewed

- [Binance Vision Dataset Terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md), version 1.0, last updated 2026-08-26; nội dung UTF-8 tải từ raw official repository ngày 2026-10-18 có SHA-256 `99c4921dbe023cd68c1a447775707d621453cc78aec6ac0bfe2e6c06a5114ee0`.
- [Binance Public Data README](https://github.com/binance/binance-public-data/blob/master/README.md) mô tả archive klines, timestamp precision chuyển sang microseconds từ 2025-01-01 và checksum files. Đây là evidence kỹ thuật, không phải grant bổ sung.
- [Binance Spot REST API documentation](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md) mô tả API endpoints và behavior. Tài liệu kỹ thuật được truy cập không tự xác nhận quyền lưu trữ hoặc redisplay; REST/WS không được cấp quyền suy diễn từ Vision dataset license.
- P02 REST/stream probe được ghi nhận trong tài liệu cũ nhưng evidence file không có trong checkout, nên access claim chưa được tái xác minh. Không thực hiện live probe trong rights review này.

### Scope decision by source and purpose

| Source | Purpose | Evidence/assessment | Decision |
|---|---|---|---|
| BIN-SPOT-ARCHIVE | Download/access | Terms grant access subject to Vision Dataset Terms; README documents downloadable archives/checksums. | Chỉ documented; không dùng quyền truy cập như quyền sản phẩm. Offline synthetic fixtures được phép cho engineering. |
| BIN-SPOT-ARCHIVE | Personal non-production historical research/backtest | Terms §4.1 liệt kê purely personal non-production backtesting và một số use case phi thương mại. Project hiện mô tả multi-account retail workspace, không phải personal-only scope. | Không áp dụng grant này cho project hiện tại; cần thu hẹp scope chính thức hoặc written license phù hợp. |
| BIN-SPOT-ARCHIVE | Persistent storage/hosting, multi-user/public display, commercial product | Terms §3.4 loại commercial utilization khỏi license và yêu cầu separate written enterprise data license; §§4.3–4.5 hạn chế hosting/commercial exploitation và điều kiện redistributed derivatives. Chưa có project-specific grant. | BLOCKED. Không tải/cache/persist/serve real archive data hay derivatives. |
| BIN-SPOT-ARCHIVE | Research/ML and derived charts/models | Terms §§2.4, 4 govern derived data including charts/models; permitted research is bounded by §4.1, while multi-user/product fit is unresolved. | BLOCKED cho shared/product ML, charts và artifacts; cần license/clarification ghi rõ use case. |
| BIN-SPOT-PUBLIC (REST/WS) | Public endpoint access/schema | API/market-data-only docs mô tả endpoints và no-key capability; historical probe evidence missing. | `documented=true`, `access-tested` chưa xác minh lại; chỉ synthetic/local development. |
| BIN-SPOT-PUBLIC (REST/WS) | Persistent storage, reconciliation snapshots, multi-user display, ML/derived use, redistribution | REST API documentation không phải project-specific data license; chưa có rights grant/entitlement trong repo. Archive terms không được tự động áp sang hoặc dùng để cấp quyền cho API. | BLOCKED độc lập với archive; cần review Binance platform/API terms và xác nhận bằng văn bản cho scope chính xác. |

### Unresolved approval fields

Product/source-rights owner và người có thẩm quyền nhận license chưa được chỉ định; geography/territories, vận hành cá nhân hay qua pháp nhân, monetization/commercial status, audience, fields/transformations, retention/deletion, attribution, quota, terms expiry và disable procedure chưa có bằng chứng. Không thể đánh dấu `rights-confirmed` hoặc `approved` chỉ dựa trên trang docs hay public endpoint.

**Điều kiện mở gate:** (1) source/product owner xác nhận product/entity, territories, audience và từng purpose; (2) với Vision, cung cấp written enterprise data license nếu scope thương mại/hosted hoặc có văn bản giải thích grant áp dụng cho scope thực tế; (3) với REST/WS, có review/authorization riêng bao phủ storage, display, ML và derivatives; (4) ghi fields, retention/deletion, attribution, quota, terms version/hash, review expiry và disable procedure. Sau đó legal/source owner cập nhật approval record; engineering chỉ bật downloader cho các nguồn/purpose được duyệt.

**Engineering state:** rights gate vẫn BLOCKED. Không có network downloader; không có Binance market data thật được tải hay lưu trong review này. Fixture-only offline tests tiếp tục được phép.

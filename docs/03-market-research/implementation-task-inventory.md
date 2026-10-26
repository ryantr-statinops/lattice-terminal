# Inventory task theo capability/dataset

**R15 — rà soát:** 26/10/2026. Đây là cổng chuyển nghiên cứu sang backlog triển khai. Mỗi hàng `P-*` là một đơn vị capability; khi cần, tiếp tục tách mỗi asset class/venue hoặc semantics thành task/commit riêng. “Chờ” là reason code hợp lệ, không phải capability đã tích hợp.

## Trạng thái nghiên cứu

- `DOCS`: endpoint/capability có trong tài liệu công khai; phải lấy schema/version, xác nhận quyền và access trước code production.
- `OBSERVED`: repository đang gọi nhưng chưa có tài liệu/rights đủ; chưa được bật.
- `WAIT_ACCOUNT`: cần tài khoản/sandbox/credential và endpoint inventory.
- `WAIT_RIGHTS`: cần hợp đồng/gói/quyền lưu/hiển thị/backtest.
- `NO_EVIDENCE`: chưa tìm thấy API phù hợp; giữ task khảo sát riêng và không adapter hóa portal/web scrape.
- `EXCLUDED`: ngoài phạm vi sản phẩm (broker order write, Gmail, automated execution).

## P-task: provider × operation × dataset

### SSI FastConnect

| Task | Dataset/operation | Bằng chứng/trạng thái |
|---|---|---|
| P-ssi-auth-market | Market-data token | DOCS / WAIT_ACCOUNT; AccessToken probe có mock test offline; chưa kiểm tra credential thật, IP allowlist hoặc quyền dữ liệu |
| P-ssi-instrument-equity-hose | HOSE stock catalogue | DOCS / WAIT_ACCOUNT; local catalogue path is offline-tested; access and rights remain unverified |
| P-ssi-instrument-equity-hnx | HNX stock catalogue | DOCS / WAIT_ACCOUNT; local catalogue path is offline-tested; access and rights remain unverified |
| P-ssi-instrument-equity-upcom | UPCOM stock catalogue | DOCS / WAIT_ACCOUNT; local catalogue path is offline-tested; access and rights remain unverified |
| P-ssi-instrument-covered-warrant-hose | HOSE covered-warrant catalogue | DOCS / WAIT_ACCOUNT; local path is offline-tested and contract fields are preserved as provider metadata; confirm this class/venue pairing from an entitled sample, access and rights remain unverified |
| P-ssi-instrument-other-classes | Remaining ETFs, funds, bonds and derivatives by venue/class | DOCS / WAIT_ACCOUNT; each class/venue remains a separate parser and task |
| P-ssi-equity-daily-bars | Equity EOD/OHLCV | DOCS / WAIT_ACCOUNT; rights/adjustment cần xác minh |
| P-ssi-equity-intraday-bars | Equity interval riêng từng resolution | DOCS / WAIT_ACCOUNT; mỗi resolution semantic khác là task riêng |
| P-ssi-indices | HOSE/HNX index catalogue | DOCS / WAIT_ACCOUNT; HOSE/HNX IndexList adapters are offline-tested; account access remains pending |
| P-ssi-index-constituents-hose | HOSE observed constituent snapshots | DOCS / WAIT_ACCOUNT; full local snapshot path is offline-tested; provider identifier semantics, historical effective dates, account access and rights remain unverified |
| P-ssi-daily-index-hose | HOSE daily index observations | DOCS / WAIT_ACCOUNT; full local series path is offline-tested; field units, currency, publication timing, account access and rights remain unverified |
| P-ssi-daily-index-hnx | HNX daily index observations | DOCS / WAIT_ACCOUNT; full local series path is offline-tested; field units, currency, publication timing, account access and rights remain unverified |
| P-ssi-corporate-actions | Rights/events | DOCS / WAIT_ACCOUNT |
| P-ssi-trade-stream | Trade event stream | DOCS / WAIT_ACCOUNT; reconnect/sequence cần inventory |
| P-ssi-quote-stream | Quote/market topics | DOCS / WAIT_ACCOUNT |
| P-ssi-account-cash | Cash/balance read | Trading auth riêng; WAIT_ACCOUNT |
| P-ssi-account-positions | Positions read | Trading auth; WAIT_ACCOUNT |
| P-ssi-account-transactions | Transaction history read | WAIT_ACCOUNT; endpoint/retention xác minh |
| P-ssi-account-orders | Order/fill history read | WAIT_ACCOUNT; chỉ GET/read, không write |

### DNSE

| Task | Dataset/operation | Bằng chứng/trạng thái |
|---|---|---|
| P-dnse-auth-market | Market API auth | DOCS / WAIT_ACCOUNT |
| P-dnse-instrument-equity | Equity catalogue | DOCS / WAIT_ACCOUNT |
| P-dnse-instrument-derivative | Futures contracts/catalogue | DOCS / WAIT_ACCOUNT; tách asset class |
| P-dnse-instrument-index | Indices | DOCS / WAIT_ACCOUNT |
| P-dnse-equity-daily-bars | Equity history | DOCS / WAIT_ACCOUNT |
| P-dnse-equity-intraday-bars | Intraday bars | DOCS / WAIT_ACCOUNT |
| P-dnse-trades | Trade history/prints | DOCS / WAIT_ACCOUNT |
| P-dnse-quotes | Quote/depth datasets, each separate | DOCS / WAIT_ACCOUNT |
| P-dnse-corporate-actions | Corporate actions | DOCS / WAIT_ACCOUNT |
| P-dnse-live-market-events | Stream subscription/event type, one per type | DOCS / WAIT_ACCOUNT |
| P-dnse-account-cash | Cash/balance | Broker API; WAIT_ACCOUNT, read-only allowlist |
| P-dnse-account-positions | Positions | WAIT_ACCOUNT |
| P-dnse-account-transactions | Transactions | WAIT_ACCOUNT |
| P-dnse-account-orders | Order/fill history | WAIT_ACCOUNT; read-only |

### TCBS official OpenAPI (community source remains a distinct provider)

| Task | Dataset/operation | Bằng chứng/trạng thái |
|---|---|---|
| P-tcbs-openapi-auth | Official OpenAPI auth/token | DOCS / WAIT_ACCOUNT |
| P-tcbs-instrument-equity | HOSE/HNX/UPCoM stock catalogue | DOCS / WAIT_ACCOUNT |
| P-tcbs-instrument-covered-warrant | Covered warrant catalogue | DOCS / WAIT_ACCOUNT |
| P-tcbs-instrument-index | Index catalogue | DOCS / WAIT_ACCOUNT |
| P-tcbs-instrument-derivative | Derivative contract catalogue | DOCS / WAIT_ACCOUNT |
| P-tcbs-bars-equity-daily | Equity daily bars | DOCS / WAIT_ACCOUNT |
| P-tcbs-bars-equity-intraday | Equity intraday bars per resolution | DOCS / WAIT_ACCOUNT |
| P-tcbs-bars-warrant | Warrant bars | DOCS / WAIT_ACCOUNT |
| P-tcbs-bars-index | Index bars | DOCS / WAIT_ACCOUNT |
| P-tcbs-bars-derivative | Derivative bars | DOCS / WAIT_ACCOUNT |
| P-tcbs-trade-history | Trade/price history | DOCS / WAIT_ACCOUNT |
| P-tcbs-stream-stock | Stock stream event | DOCS / WAIT_ACCOUNT |
| P-tcbs-stream-derivative | Derivative stream event | DOCS / WAIT_ACCOUNT |
| P-tcbs-account-* | Cash, positions, transactions, order/fill read | NO_EVIDENCE in public endpoint inventory; investigate each operation; no write routes |
| P-tcbs-community-quarantine | Identify/preserve old source identity and prevent hidden OpenAPI substitution | OBSERVED; independent F03 removes silent VNDIRECT fallback |

### VPBankS NeoAPI

| Task | Dataset/operation | Bằng chứng/trạng thái |
|---|---|---|
| P-vpbanks-auth | OAuth/JWT and environment | DOCS / WAIT_ACCOUNT / IP whitelist |
| P-vpbanks-instrument-equity | Stock list and detail | DOCS / WAIT_ACCOUNT |
| P-vpbanks-instrument-covered-warrant | Warrant detail/catalogue | DOCS / WAIT_ACCOUNT |
| P-vpbanks-instrument-derivative | Futures catalogue/detail | DOCS / WAIT_ACCOUNT |
| P-vpbanks-equity-daily | Equity history (endpoint inventory required) | WAIT_ACCOUNT / schema unknown |
| P-vpbanks-quotes | Quote/orderbook read | DOCS / WAIT_ACCOUNT |
| P-vpbanks-market-stream | Each market event/channel separately | DOCS / WAIT_ACCOUNT |
| P-vpbanks-account-list | Accounts | DOCS / WAIT_ACCOUNT |
| P-vpbanks-account-balance | Buying power/cash | DOCS / WAIT_ACCOUNT |
| P-vpbanks-account-equity-positions | Equity positions | DOCS / WAIT_ACCOUNT |
| P-vpbanks-account-derivative-positions | Derivative positions | DOCS / WAIT_ACCOUNT |
| P-vpbanks-account-transactions | Transactions | NO_EVIDENCE; investigate endpoint |
| P-vpbanks-account-order-history | Order/fill history | DOCS / WAIT_ACCOUNT |

### VNDIRECT

| Task | Dataset/operation | Trạng thái |
|---|---|---|
| P-vndirect-public-dchart-review | Daily and 1m UDF route/rights | OBSERVED + WAIT_RIGHTS; no production ingestion until written rights/API contract |
| P-vndirect-official-datafeed | Catalogue/dataset API | WAIT_ACCOUNT; public service currently reports suspended |
| P-vndirect-openapi-onboarding | Organization Open API documents | WAIT_ACCOUNT / WAIT_RIGHTS |
| P-vndirect-account-* | Cash, positions, transactions, order/fill read | NO_EVIDENCE until official endpoint documents provided |
| P-vndirect-other-datasets | Trades/quotes/depth/corporate/finance | NO_EVIDENCE in public DChart docs; do not scrape |

### Commercial and financial-data providers

| Provider/task family | One task per dataset/operation | Trạng thái |
|---|---|---|
| FiinGroup | Stock EOD by venue; adjusted price/action; index; covered warrant trading/info/foreign; derivative trading/basic/price; fund info/portfolio/NAV/financials; bond reference/coupon/collateral/issuance/events/payment/YTM; government bond trades/yield/auction; proprietary transactions; consensus. Split every named dataset and venue where semantics differ. | DOCS / WAIT_ACCOUNT / WAIT_RIGHTS; copy endpoint list from official API inventory and create one `P-fiingroup-*` row per endpoint-version. |
| Vietstock | API catalogue; Sync Data delivery; market prices by interval; company/reference; statements; events; holders/insiders; derivatives; covered warrants; ETFs; bonds; macro series. | WAIT_ACCOUNT / WAIT_RIGHTS; each remains separate; catalogue coverage unconfirmed. |
| FireAnt | REST market instruments/price endpoint per schema; company; finance; funds/FMarket; account list; cash/balance; positions; transactions; order history. | DOCS / WAIT_ACCOUNT / WAIT_RIGHTS; exact route/scope inventory first. Exclude every write scope/route (`orders-write`, account-write, company-write, finance-write, posts-write). |
| HayInsights | Commodity snapshot/history; crypto overview/on-chain/derivatives; ETF list/info/holdings/NAV/price history; FX series/table; macro each series family; bonds/yields; real estate each endpoint; news/sentiment/calendar; equity/index only where exact API is documented. | DOCS / plan-gated WAIT_ACCOUNT / WAIT_RIGHTS; one route/dataset per P-task; products without endpoint remain NO_EVIDENCE. |
| WiGroup WiFeed | Catalogue, auth, price/reference/financial/action/macro/bond dataset only as listed by vendor docs. | WAIT_ACCOUNT / WAIT_RIGHTS; no endpoint-level evidence yet. |

## Generic D/U/A/M/N/T/O tasks

### Data and API foundation

`D01` provider-specific request limits; `D02` bounded retry/backoff; `D03` persisted ingestion jobs; `D04` resumable cursors; `D05` rights-aware raw archive; `D06` invalid-record quarantine; `D07` revision/dedup policy; `D08` atomic Parquet publish; `D09` persistent snapshot registry; `D10` retention; `D11` instrument catalogue; `D12` shared live subscriptions; `D13` reconcile live events; `D14` gap backfill; `D15` restart recovery; `D16` job UI. Every item is a one-outcome commit.

### Read-only accounts

`A01` read-operation allowlist; `A02` account/subaccount schema; `A03` timestamped snapshot contract; `A04` sync job/checkpoint; `A05` immutable snapshots; `A06` account selector UI; `A07` balances; `A08` positions; `A09` transactions; `A10` order/fill history; `A11` stale/partial state. Provider API operation itself stays in P-task; no broker snapshot posts to fund ledger.

### Product consumers

`U01` Market instrument catalogue; `U02` routed Market snapshots; `U03` Quant routed dataset; `U04` filter by asset class; `U05` correct currency/units; `U06` non-candle explorer; `U07` provenance; `U08` gaps/staleness/partial quality; `U09` analytics-vs-simulation support. Each is a separate commit.

### Simulation / fund

`M01` effective-dated rule registry; `M02` coverage-aware fill-model registry; `M03` calendars; `M04` fee/tax schedule; `M05–M09` settlement securities, settlement cash, available cash, available quantity, shared liquidity; `M10` supported corporate actions; `M11` data snapshots; `M12` coverage block; `M13` complete provenance; `M14` Strategy live input; `M15` signal-only mode; `M16` live manual paper; `M17` replay clock; `M18` atomic event+cursor; `M19` fresh pinned fund marks; `M20` UI coverage gates. Market rules themselves are split per `venue×asset×rule`; fill models per `venue×asset×session×model`. First model only LO continuous and must cap fills to observed liquidity.

### Signal, app notification and Telegram

`N01` signal contract; `N02` `context.signal`; `N03` signal/run persistence; `N04` notification store; `N05` Strategy signal notification; `N06–N10` each separate paper-order lifecycle event (accepted/partial/filled/cancelled/rejected); `N11–N14` separate strategy/feed stale/feed disconnect/account-sync alerts; `N15` loss/drawdown threshold; `N16` position threshold; `N17` paged inbox; `N18` read state; `N19` reconnecting stream; `N20` event-ID dedupe; `N21` signal logical-key cooldown; `N22` live/replay/backtest policy; `N23` channel/category preferences; `N24` inbox UI; `N25` unread badge; `N26` toast; `N27` preference UI. Telegram tasks `T01–T14` remain separate as specified in product plan: secret config, getMe, private pairing, user-initiated test, transactional outbox, sendMessage transport, retry_after, deterministic failure, unknown timeout, expiry, delivery UI, manual retry, disconnect, local-only channel error.

### Operations

`O01` capability health; `O02` quota/ingest errors; `O03` account snapshot backup allowlist; `O04` notification backup allowlist; `O05` restore never restarts Strategy; `O06` restore never sends old outbox; `O07` provider setup; `O08` Telegram setup; `O09` operations recovery guide; `O10` acceptance matrix. Secrets/master key/tokens excluded from standard backup.

## Commit policy and acceptance state

The implementation commit must narrow each generic item further if it contains more than one user-observable outcome or provider/dataset. Two providers, venues, event types, resolutions or dataset semantics never share a commit. Keep dependent unfinished capabilities disabled and `main` buildable. Mark one capability ready only after credential→provider→normalize/store→consumer, failure handling, rights and appropriate verification are demonstrated. No automatic order execution; no Gmail; no push.

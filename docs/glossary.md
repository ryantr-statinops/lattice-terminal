# Glossary — Research Terminal

**Trạng thái:** definitions for local-first Vietnam research product; some capabilities are not implemented.

| Term | Standard definition |
|---|---|
| Asset | Economic asset/security category; distinct from a trading instrument or ticker |
| Instrument | Tradable/listed product identified by venue, board/market type, instrument class, native symbol and lifecycle |
| Venue / board | Exchange and board/market label such as HOSE, HNX, UPCOM; DER/BOND require distinct product semantics |
| Candle / OHLC | Time-bucketed open/high/low/close and volume/value with source, interval, session/time fields and closed/provisional state |
| Quote / live price | Provider observation for display/simulation with source and event/receive times; not proof of executable fill |
| Paper order/fill | Local simulated order/fill record; never submitted to a broker |
| Backtest | Deterministic historical replay against a versioned snapshot, assumptions and simulator version |
| Article / event | Source article/evidence and a related interpreted event; retains revisions and confidence |
| `published_at` | Source-declared publication time; may be missing or wrong |
| `first_seen_at` | First time the local engine observed an item; not backdated during backfill |
| `available_at` | Conservative time at which the data could have been known under documented evidence/policy |
| `updated_at` | Correction/update time; does not overwrite prior availability history |
| Dataset snapshot | Versioned local data set with manifest, source revisions, coverage and rights reference |
| SSI FastConnect Data | SSI market-data product; separate from FastConnect Trading |
| Phiên ATO (At-The-Opening) | Phiên khớp lệnh định kỳ xác định giá mở cửa (09:00 - 09:15 trên HOSE) |
| Phiên ATC (At-The-Closing) | Phiên khớp lệnh định kỳ xác định giá đóng cửa (14:30 - 14:45 trên HOSE, HNX) |
| Khớp lệnh liên tục | Phiên giao dịch so khớp lệnh mua/bán ngay khi lệnh được nhập vào hệ thống |
| Khớp lệnh thỏa thuận | Giao dịch khối lượng lớn thỏa thuận trực tiếp giữa các bên (Put-Through) |
| Giá Trần / Sàn / Tham chiếu | Giá trần (Ceiling - tím), Sàn (Floor - xanh lơ), Tham chiếu (Reference - vàng) |
| Biên độ giá (Price Band) | Biên độ dao động tối đa trong ngày: HOSE ±7%, HNX ±10%, UPCOM ±15% |
| Bước giá (Tick Size) | Khoảng cách giá tối thiểu giữa các mức đặt lệnh (ví dụ HOSE: 10đ, 50đ, 100đ) |
| Lô giao dịch (Lot Size) | Khối lượng tối thiểu đặt lệnh: Lô chẵn 100 cổ phiếu; Lô lẻ 1-99 cổ phiếu |
| Chu kỳ thanh toán T+2 | Với instrument thuộc quy chế VSD có hiệu lực 2022-08-29, thanh toán và phân bổ trước 13:00 T+2 để có thể giao dịch phiên chiều; xem [settlement evidence và phạm vi](07-portfolio/vn-market-rules.md#4-thanh-toán-t2-và-thời-điểm-tài-sản-khả-dụng) |
| Khối ngoại (Foreign Flow) | Dữ liệu khối lượng và giá trị mua/bán của nhà đầu tư nước ngoài |
| Local profile | User-owned data/config boundary on one installation; profile count and password protection are pending design |
| Portfolio | Local ledger plus backtest/paper simulation state; not an SSI/broker account |
| Model Lab | Later experiment/model runtime, outside first MVP |
| News engine | Workstream độc lập cho nguồn quốc tế và Việt Nam; tích hợp sau khi source/integration gates sẵn sàng |

## Invariants

- No venue/board/asset-class mixing without explicit normalization rules; tickers alone are not identities.
- Store instants in UTC; UI defaults to Asia/Ho_Chi_Minh with timezone shown.
- Preserve provider timestamp/value and source availability separately from local receive time.
- Missing/unsupported/stale/partial data is not zero and must not be forward-filled into a fictitious bar.
- A live quote does not prove a backtest price or paper fill; paper output is always labeled simulated.
- Credentials and all user data remain local in V1; localhost is not a security boundary or encryption.
- Source flags `documented`, `access-tested`, `rights-confirmed` and `approved` require distinct evidence.
- No FastConnect Trading credentials or real order routes in V1.

# Danh mục rule thị trường cần xác minh trước mô phỏng

**Rà soát:** 26/10/2026. Đây là checklist evidence, không phải rule pack đã được bật. Nguồn rule phải là văn bản/endpoint có hiệu lực tại thời điểm áp dụng; trang FAQ hoặc quy chế cũ chỉ là đầu mối cần đối chiếu.

## Phạm vi simulator đầu tiên

Mục tiêu đã chốt là cổ phiếu lệnh LO trong phiên khớp lệnh liên tục; fill chỉ dựa trên liquidity quan sát được, cho phép partial fill. Không mô phỏng auction, bond, derivatives hay asset class khác cho tới khi có rule và fill model riêng. Không suy ra thanh khoản nếu feed thiếu.

## Checklist theo rule family

| Rule family | Cần xác minh và version hóa | Evidence / ghi chú |
|---|---|---|
| Venue, board, session calendar | HOSE/HNX/UPCoM từng phiên sáng/chiều, nghỉ trưa, ngày nghỉ, ngày giao dịch đặc biệt, session open/continuous/close và thời gian hiệu lực. | [HNX FAQ](https://upcom.hnx.vn/vi-vn/hoi-dap.html) phân biệt HNX listed continuous + closing auction và UPCoM session; kiểm tra quy chế hiệu lực hiện nay. |
| Allowed order types | LO behavior/cancel, validity, market order semantics if simulator later supports it, order validity at session boundaries. | [HOSE published rule PDF](https://staticfile.hsx.vn/Uploads/LocalFiles/993f05f252bb4bf0a755bcd51440f90f/20210704_Quy%20ch%E1%BA%BF%20giao%20dịch.pdf) là tài liệu cũ; lấy văn bản hiện hành trước khi code. |
| Price limits/reference | Reference price, ceiling/floor, ex-right adjustment, special suspension/resumption sessions, rounding at bounds. | HNX FAQ reports ±10% for listed equity and UPCoM rules elsewhere; verify latest official effective rule independently by venue/product. |
| Tick size and price scale | Tick ladder by price/venue, rounding and rejection when order is off tick. | Không thấy đủ hiện hành/venue-wide evidence ở lượt này; yêu cầu exchange/broker docs. |
| Lot size and quantity | Board lot, odd lot, minimum/maximum order, lot changes, odd-lot session and order type rules. | Xác minh theo venue, board, instrument và ngày hiệu lực; không lấy constant từ một provider. |
| Price-time priority and matching | Queue priority, price priority, time priority, opening/closing auction allocation, crossing/locked conditions. | Simulator LO continuous phase cần matching assumptions công khai; không giả lập vị trí queue nếu feed không có order book/queue. |
| Fill evidence/liquidity | Trade prints, top-of-book/depth, timestamp ordering, venue aggregation, available volume, partial fill, price improvement, gap/stale feed. | Fill model phải nêu feed resolution và conservative participation/capacity assumptions. Bar OHLCV không chứng minh vị trí queue. |
| Settlement | T+n availability of sale proceeds/securities, pending receivables/payables, cash reservation, withdrawable vs buying power. | [VSD historic annual report](https://vsd.vn/CMSImage/CKFinderUpload/bc%20kh%20sxkd%202018.pdf) mentions T+2 implementation historically; verify current effective settlement cycle, intraday cutoffs and edge cases from VSDC/current rules. |
| Fees and taxes | Broker commission, exchange clearing/settlement fees, tax by instrument/side, VAT or other charges, fee minimums and effective dates. | No assumption from one broker. Version by provider/account/market and effective interval. |
| Corporate actions | Ex-date/record date, cash dividend, stock dividend/split, rights issue, bonus shares, fractional treatment, adjusted price convention. | Require normalized events and publication timestamps; reconcile provider price adjustment against raw prices to avoid double adjustment. |
| Halt/restriction lifecycle | Suspension, warning/restricted trading, limit-up/down behavior, resumed sessions, delisting and instrument transitions. | Need official status/event feed and effective timestamps. If absent, mark simulation unsupported for affected window. |
| Instrument lifecycle | Listing, first trade, symbol changes, merger, expiry, delisting and permanent identifier. | Price history symbol alias alone is insufficient for point-in-time universe reconstruction. |
| Currency and valuation | Native currency, contract multiplier, face value, price/volume units, FX source/timing and reporting currency conversion. | Fund remains VND; foreign-denominated datasets are unsupported for simulation until valuation model is defined. |
| Reproducibility/causality | Point-in-time publication/availability, revision IDs, delayed data, future leakage, exact dataset snapshots. | Every run pins data revisions, rule pack, fill model, fee schedule, code and assumptions. |

## Rule packs and release gates

Create separate packs by `venue × asset class × rule × effective interval`. HOSE, HNX and UPCoM require separate evidence/commits even when rules appear similar. Preserve old packs for historical runs rather than rewriting them. A pack remains draft/disabled until primary current rules and deterministic tests support it.

Before enabling any simulation capability, require: (1) official current source/version; (2) interpretation reviewed against actual provider feed semantics; (3) edge cases and effective dates represented; (4) unit tests with documented expected results; (5) clear unsupported-data guard; and (6) report provenance. Auction, bonds, futures, covered warrants and all other classes stay disabled until their individual rule and fill coverage is complete.

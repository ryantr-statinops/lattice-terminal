# Next steps

## Trạng thái hiện tại

Research Terminal là prototype news-first bằng tiếng Việt, định hướng BTC/ETH. Frontend React/Vite, FastAPI fixture API, Go gateway và OpenAPI contract đang có.

- Market, chart, candles và watchlist dùng dữ liệu tổng hợp trong `data/fixtures/`.
- News có asset filters/provenance nhưng chưa kết nối news source hoặc ingestion.
- Portfolio hỗ trợ nhập tay/CSV, validation, localStorage và P&L trên giá fixture; chưa có auth hoặc lưu server.
- Binance WebSocket là opt-in, theo symbol/interval đang chọn và chỉ hiển thị kết nối; chart/portfolio chưa nhận dữ liệu stream.
- Model Lab là form cùng chỉ số mock gắn `simulated`; chưa chạy training/backtest.
- API đọc fixture; chưa có database, managed auth hay business persistence.

## Trạng thái gate (2026-10-18)

P03 follow-up ngày 2026-10-18 đã rà lại Binance Vision Dataset Terms v1.0 (2026-08-26) và tách review Binance REST/WS. Cả `BIN-SPOT-PUBLIC` lẫn `BIN-SPOT-ARCHIVE` vẫn BLOCKED/not approved cho product scope multi-account retail, public/multi-user display, persistent storage và shared research/ML. Vision terms yêu cầu written enterprise data license cho commercial utilization; REST docs chỉ chứng minh capability/schema, không xác nhận storage/display rights. P02 access evidence được trỏ trong tài liệu không có trong checkout hiện tại. Xem [decision record](../docs/03-market-research/source-register.md#p03-follow-up-decision-record--2026-10-18) và [candle contract](../docs/06-market-data/historical-ingestion.md).

**Next action:** source/product owner cần xác nhận product/entity, commercial status, audience và territories; cung cấp written license/authorization riêng cho Vision archive và REST/WS bao phủ exact purposes, fields, retention/deletion, attribution và quota. Khôi phục hoặc lặp lại access probes có thể tái kiểm chứng sau khi phù hợp policy. Cho tới khi source owner/legal review cập nhật gate thành approved, không chạy historical backfill, lưu market payload thật hoặc phát hành snapshot. Fixture-only checks vẫn được phép.

Historical market-data offline foundation hiện đã có Go parser cho archive CSV/ZIP và REST kline JSON, candle validation/reconciliation, coverage report, cùng snapshot CSV/manifest chỉ nhận synthetic fixtures. Chưa có downloader/network adapter, backfill thật, API/UI serving hay WebSocket integration. Sau khi rights approval đạt, bước tiếp theo là triển khai transport/backfill theo source-specific approval rồi kiểm tra coverage trước serving.

## Các bước tiếp theo sau khi gate được giải quyết

1. **Source rights và data contract:** lập source register cho market/news, kiểm tra quyền truy cập, lưu trữ, hiển thị, dẫn link và dùng cho research theo khu vực triển khai; chốt freshness, provenance và correction policy trước khi lấy dữ liệu thật.
2. **Historical market data:** sau khi rights gate đạt, tích hợp một nguồn BTC/ETH, backfill candles 15m/1h/1d, kiểm tra gaps/duplicates/late bars và lưu snapshot có version; giữ fixture làm test dataset.
3. **News ingestion:** chỉ thêm adapter cho nguồn đã qua rights gate; xử lý dedupe/revisions, publication/first-seen timestamps, instrument mapping và source-limited states.
4. **Private workspace:** chọn managed auth và persistence trước khi lưu portfolio/experiments phía server; định nghĩa ownership/isolation, export/delete và migration từ local-only data.
5. **Live market stream:** sau khi source rights xác nhận, nối stream với candle store/chart, merge REST backfill và WebSocket updates, xử lý reconnect/gaps/open-vs-closed bars.
6. **Model Lab runtime:** chạy feasibility spike cho browser worker/runtime, rồi triển khai baseline có walk-forward validation, costs và reproducible artifacts; bỏ số mock khi có kết quả thực tính.
7. **Release readiness:** dependency/source-rights/security review, accessibility contrast test, operational recovery/quotas, browser E2E và production data claims.

## Quy trình phát hành thay đổi

Mỗi thay đổi được kiểm tra, commit và push thành mục nhỏ. `main` được bảo vệ và chỉ nhận thay đổi qua PR với hai required status checks; không push trực tiếp hoặc force-push. Rollback bằng `git revert <commit>` sau khi xác định ảnh hưởng contract/dữ liệu.

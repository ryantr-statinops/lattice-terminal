# Prototype evaluation and hardening report

**Trạng thái:** cập nhật 2026-10-17 sau hardening prototype. Đây là bằng chứng cho code fixture, không phải production readiness.

## Sản phẩm đang chạy

- Market hiển thị BTC/ETH, bảng nến và candlestick chart từ synthetic fixtures. Watchlist lưu local.
- News hiển thị fixture articles, provenance timestamps và lọc theo instrument.
- Portfolio nhập tay/CSV, kiểm tra dữ liệu, lưu localStorage và tính P&L theo nến fixture đã đóng. Thiếu giá thì ẩn tổng định giá/P&L.
- Binance WebSocket chỉ kết nối khi người dùng bật; kiểm tra lifecycle/health và không đưa stream vào chart hoặc portfolio.
- Model Lab form gọi mock adapter. Kết quả luôn `simulated`/`mock`; cấu hình không tham gia tính chỉ số.
- FastAPI, Go Gateway và OpenAPI hoạt động quanh fixture; portfolio API vẫn trả mảng rỗng.

## Data rights và credentials

- Không có dữ liệu market/news thật trong fixtures; mọi fixture ghi `source_id=fixture-only` và `is_synthetic=true`.
- Binance stream có thể được bật trực tiếp trong trang Market. Trước ingestion/phát hành production cần xác minh quyền theo source, địa bàn, lưu trữ, hiển thị và mục đích sử dụng.
- Environment boundary check chỉ cho phép `VITE_API_BASE_URL` ở frontend. Known-marker scan trên lịch sử chưa push tại thời điểm hardening không tìm thấy private key/AWS/GitHub/OpenAI token pattern; đây không thay thế managed secret scanner.
- Không có auth/account hoặc exchange trading keys.

## Kiểm chứng

- Frontend: 51 Vitest tests pass; lint, typecheck và Vite production build pass local.
- Tooling: fixture validator, environment-boundary check và 2 Node tooling tests pass.
- API/OpenAPI và Go gateway/ingestion tests cùng fixture ingestion pass trong các required GitHub Actions jobs. Local không có Go và không thể tải Python runtime do network/DNS bị hạn chế.
- `npm install` báo 0 vulnerabilities trong npm audit tại thời điểm cài test dependencies. Cần chạy lại dependency audit trước release.
- Chart, portfolio và CSV có screen-reader table captions. Contrast ratios chưa được đo bằng axe/Lighthouse; browser UI smoke check được ghi lại khi hoàn tất phát hành này.

## Hành vi và giới hạn

| Khu vực | Có trong prototype | Chưa có |
|---|---|---|
| Market | Fixture candles/chart, watchlist, opt-in stream status, source timestamp | Real history, backfill, stream-to-chart merge, production source approval |
| News | Fixture cards, instrument filters, published/first-seen times | News adapters, dedupe/revisions, source-rights approval |
| Portfolio | Local holdings, CSV validation, fixture valuation, partial totals | Auth, server persistence, transaction ledger, live valuation |
| Model Lab | Config form, explicitly mocked result | Web Worker/Pyodide, actual model training/backtest, reproducible artifact |
| Operations | Local API/Gateway fixture path, CI gates | Deployment, auth isolation, production monitoring/recovery |

## Readiness

Prototype hardening gates cover frontend regression tests, FastAPI/OpenAPI drift, research inspection and Go fixture services. Source-rights approval, contrast measurement, auth/persistence and production monitoring remain open. Use [next steps](../../task/next-plan.md) to sequence real-data work after rights and data contracts are reviewed.

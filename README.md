# Research Terminal

Research workspace tiếng Việt, ưu tiên đọc tin và đối chiếu BTC/ETH cho retail trader. Bản hiện tại là prototype dùng dữ liệu fixture synthetic; không dùng để ra quyết định giao dịch.

## Trạng thái hiện tại

- Market: BTC/ETH, bảng nến, chart, interval và watchlist đều dùng fixture.
- News: lọc tin fixture theo tài sản; chưa có nguồn tin hoặc ingestion thật.
- Portfolio: nhập holdings thủ công/CSV, lưu trên thiết bị bằng localStorage và tính P&L từ giá fixture.
- Stream: kết nối Binance WebSocket chỉ khi người dùng bật; chỉ hiển thị tình trạng kết nối, chưa cập nhật chart hoặc portfolio.
- Model Lab: form và kết quả mock để minh họa giao diện; chưa có training/backtest runtime.
- API: FastAPI đọc fixture, Go gateway và OpenAPI contract. Chưa có database, auth/account hay lưu portfolio phía server.

Không yêu cầu exchange trading keys. Quyền sử dụng nguồn market/news phải được xác minh trước khi triển khai ingestion hoặc phát hành dữ liệu thật.

## Chạy fixture local

Yêu cầu Node 22.23.1/npm 10.9.8, Go 1.27.2, Python 3.11–3.13 và uv 0.11.28. JavaScript dependencies nằm trong `package-lock.json`, API dependencies trong `services/api/uv.lock`.

```powershell
npm ci
npm run dev
```

Mở http://127.0.0.1:5173/terminal/news. Các route gồm `/terminal/market`, `/terminal/news`, `/terminal/portfolio`, `/terminal/model-lab` và `/terminal/account`. Để chạy API/gateway, xem [hướng dẫn API](services/api/README.md) và [hướng dẫn gateway](services/gateway/README.md).

Frontend gọi `/api` qua Vite proxy đến gateway port 8080; gateway mặc định chuyển tiếp đến API port 8000. Fixture synthetic nằm trong [data/fixtures](data/fixtures/README.md).

## Kiểm tra

```powershell
npm run security:env-boundaries
npm run fixtures:check
npm run test:tooling
npm run test:web
npm run lint
npm run typecheck
npm run build
```

API, OpenAPI drift, research và Go checks chạy trong GitHub Actions. Repo bảo vệ `main` và yêu cầu thay đổi đi qua pull request.

## Tài liệu

- [Documentation index](docs/README.md) và [glossary](docs/glossary.md).
- [Vision & scope](docs/01-product/vision-and-scope.md).
- [Next steps](task/next-plan.md).

# Go ingestion

Trạng thái: CLI news fixture và historical market-data pipeline offline. Không có network client, scheduler hoặc nguồn live. Historical loader chỉ chấp nhận local inputs có `.fixture.json` synthetic marker khớp SHA-256; snapshot publisher hard-block mọi input không phải fixture và luôn ghi `rights_eligible=false`.

Yêu cầu Go 1.27.2. Từ repository root:

```powershell
go -C services/ingestion run ./cmd/ingest
go -C services/ingestion run ./cmd/ingest -fixture ../../data/fixtures/news.json
go -C services/ingestion test ./...
```

Đường dẫn fixture được tính từ thư mục `services/ingestion` khi dùng `go -C`. File phải có `schema_version="1"`, `is_synthetic=true`, `source_id="fixture-only"`, mảng `articles` và ID bài viết không trùng. JSON không hợp lệ hoặc nguồn khác bị từ chối với exit code 1.

Stdout thành công: `mode=fixture-only source=fixture-only articles=N synthetic=true`, với N là số bài trong fixture. Không xuất nội dung bài hoặc credentials. Chưa có dữ liệu thị trường thật; source approval và ingestion live thuộc giai đoạn sau.

## Historical market data — offline fixture mode

Lệnh đọc archive CSV/ZIP và REST kline JSON từ local disk, chuẩn hóa/reconcile candle rồi ghi snapshot CSV + manifest JSON. Không có flag để gọi Binance/network. Tất cả input phải có sibling `<file>.fixture.json` khai báo `schema_version=1`, `is_synthetic=true`, `source_id=fixture-only` và SHA-256 chính xác. ZIP cần thêm `<file>.CHECKSUM`; CSV fixture được hash qua marker. Không gắn marker fixture cho market data thật.

Từ repository root, ví dụ chạy với synthetic fixture:

```powershell
go -C services/ingestion run ./cmd/marketdata `
  --symbol BTCUSDT `
  --interval 15m `
  --start 2024-12-31T23:45:00Z `
  --end 2025-01-01T00:00:00Z `
  --archive-input internal/marketdata/testdata/synthetic-archive-2024.csv `
  --archive-timestamp-unit millisecond
```

`--start` inclusive và `--end` exclusive; cả hai phải UTC `Z`, millisecond precision và căn theo interval. `--archive-timestamp-unit` bắt buộc để không suy đoán đơn vị. REST fixture dùng `--rest-input` và timestamp milliseconds. Kết quả mặc định ở `../../.cache/market-snapshots/`, đã được `.gitignore` loại khỏi Git. Snapshot ID xác định từ instrument, range, adapter version và input hashes; replay cùng inputs là idempotent. Conflict giữa revisions chặn publish; gaps được ghi trong quality report và không được lấp.

Binance Vision/REST network adapter chưa được triển khai. Source register vẫn block rights cho persistent storage/display/research; chỉ synthetic fixtures được dùng trong giai đoạn này.

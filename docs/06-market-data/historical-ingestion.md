# Historical ingestion

**Trạng thái:** contract P03 chốt cho implementation; source rights gate chưa đạt. Không tải/lưu market payload thật cho đến khi policy được approved theo [source register](../03-market-research/source-register.md).

Go ingestion tải Binance bulk archive cho lịch sử và public REST cho phần gần hiện tại/reconcile. REST/archives là nguồn canonical cho research snapshots; giá WebSocket trong browser không tự thành warehouse history. Lịch ingestion độc lập đăng nhập và lifecycle tab.

## Adapter và identity

Instrument bắt buộc venue=Binance, market_type=spot, base=BTC/ETH, quote=USDT và native_symbol. Tập interval mục tiêu 15m/1h/1d. Không dùng perpetual candle/funding/OI trong cùng table identity như spot; derivatives deferred.

Adapter giữ request range, source URL, retrieved_at, response schema version, original timestamp unit và checksum. [Archive documentation](https://github.com/binance/binance-public-data) ghi Spot timestamps từ 2025-01-01 dùng microseconds; parser chọn unit theo evidence/product version và fixture quanh transition. REST/WS units kiểm tra theo endpoint options, không áp unit của archive sang mọi response.

## Chuẩn normalized candle

- Identity tự nhiên là `venue=binance`, `market_type=spot`, `native_symbol`, `interval`, `open_time_utc`; chỉ `BTCUSDT`/`ETHUSDT` và `15m`/`1h`/`1d` thuộc MVP. Không gộp derivative hoặc venue khác.
- `open_time_utc` và `close_time_utc` chuẩn hóa thành UTC millisecond precision; giữ riêng `source_timestamp_unit` (`millisecond`/`microsecond`) và giá trị timestamp gốc trong raw-object metadata. Không suy đoán unit theo độ lớn ngoài parser rule có version/evidence.
- Giá OHLCV dùng decimal-safe representation ở boundary chuẩn hóa; `is_closed` được tính theo interval và thời gian quan sát, không chỉ tin payload. Open candle có thể tồn tại dạng provisional, nhưng snapshot research chỉ nhận closed bars.
- Provenance tối thiểu: `source_id`, `source_object_id`/request reference an toàn, `ingestion_run_id`, `adapter_version`, `schema_version`, `retrieved_at`, `available_at`, raw content hash và source response/version metadata. Không lưu credentials hoặc query secrets trong URL.
- Revision identity gồm natural key + revision/content hash; cùng key/cùng payload idempotent, cùng key/khác payload tạo revision mới kèm observed/available time. Snapshot cũ không mutate.
- Coverage gaps được biểu diễn rõ theo instrument/interval/range. Không forward-fill OHLCV, zero-fill volume, trộn venue hoặc phát hành snapshot nếu source eligibility/schema gate thất bại.
- Manifest bất biến tối thiểu: schema version, snapshot ID/version, creation time, source/grant policy reference, instrument/interval/range, row count, source/revision IDs, content hashes, original/normalized timestamp policy, closed-bar policy, gaps/rejections/duplicates/corrections counts, availability policy, adapter version và quality result. Manifest không khẳng định rights approval; rights gate phải pass riêng.

## Rights gate bắt buộc

Current source register đánh dấu `BIN-SPOT-PUBLIC` và `BIN-SPOT-ARCHIVE` chưa rights-confirmed/approved; referenced P02 access evidence is missing from the current checkout. Vì vậy implementation chỉ được chạy synthetic fixtures cho đến khi owner ghi approval evidence đủ cho exact purpose/audience/geography/fields/retention. No live download, persistent raw cache, normalized real-data snapshot, or publication is permitted before that gate passes. A transient access smoke test is not approval and must not be described as production ingestion.

## Quy trình

1. Policy/access gate và kiểm tra source coverage/instrument metadata.
2. Enumerate expected files/ranges, download có bounded concurrency theo evidence quota.
3. Verify checksum; failed object vào quarantine và retry có giới hạn.
4. Parse decimals/times, kiểm OHLCV, key uniqueness và bar closure.
5. Reconcile daily/monthly overlap và REST overlap cùng venue; khác payload tạo revision.
6. Publish normalized coverage report và immutable snapshot manifest khi quality gates pass.

Checkpoint theo file/range và content hash, không chỉ “last timestamp”. Archives có thể được sửa; revalidation tạo revision, không ghi đè snapshot cũ. Không hứa archive lịch sử có latency evidence; [availability policy](../04-data/lifecycle-and-quality.md) phân biệt bar-research assumption và observed feed.

Missing range là gap được ghi nhận. Không vá bằng venue khác, không zero-fill volume hoặc forward-fill để giả nến. Dữ liệu thiếu ảnh hưởng feature windows và evaluation coverage. Dùng nến đóng cho features; cutoff decision time và trade execution phải theo Model Lab contract.

## Vận hành và acceptance

Quota/interval/retention chốt bằng P03 tests, headers và current provider docs. 429/backoff có jitter; auth/region/terms error dừng và alert. Không bypass restriction bằng proxy. Tests: checksum sai, partial zip, replay, REST pagination overlap, out-of-order, corrected file, timestamp unit, candle còn mở, symbol mismatch và coverage gap. Price precision/quote currency phải giữ đúng; USDT không là USD.

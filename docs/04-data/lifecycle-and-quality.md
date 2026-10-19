# Availability, snapshots và chất lượng

**Trạng thái:** quy tắc mục tiêu, chưa có data quality report thực tế.

## Raw → normalized → serving

Raw object bất biến theo hash lưu evidence hợp lệ; parser tạo normalized revisions; serving chọn revision theo policy và mục đích. Replay cùng object+adapter version phải idempotent. Không ghi đè raw khi provider sửa file; lưu hash mới và liên kết supersedes.

Target lineage: source → ingestion run → permitted evidence → normalized revision → snapshot → research/simulation input. Raw payload retention requires explicit rights. Parser failure vào quarantine theo retention policy, không thay giá trị bằng zero. Production snapshot publish chỉ khi schema, source eligibility và quality gate pass; probe outputs không tự thành product snapshots.

## Availability-time joins

Feature tại decision time T chỉ lấy revision với available_at ≤ T, đồng thời input candle đã đóng. Với news mới thu: first_seen_at là evidence hệ thống biết được; published_at không đủ để backdate availability. Corrections chỉ ảnh hưởng decision times sau khi revision được quan sát/khả dụng.

Bulk price history có thể phục vụ bar research với policy ghi rõ giả định availability-after-close; không tuyên bố tái hiện feed latency quá khứ. News backfill mặc định chỉ retrospective analysis, không đưa vào historical predictive backtest nếu thiếu timestamp evidence thích hợp. Snapshot ghi `availability_policy` và `research_mode` để phân biệt simulated bar availability với observed news availability.

## Checks và xử lý

| Kiểm tra | Hành vi |
|---|---|
| Timestamp/unit sai; năm ngoài phạm vi | Quarantine, không auto nhân/chia khi thiếu adapter evidence |
| OHLC invalid, volume âm | Reject/quarantine, giữ raw hash để điều tra |
| Duplicate natural key cùng payload | Idempotent dedup |
| Duplicate key khác payload | New revision và anomaly record |
| Missing candles | Coverage gap; backfill cùng venue, không forward-fill OHLCV để tạo giao dịch giả |
| Open candle | UI được label provisional; exclude features mặc định |
| News thiếu published time | Giữ null; dùng first_seen availability và nhãn thiếu |
| Article sửa/rút | Revision/tombstone; giữ lineage nếu policy cho phép |
| Stale quote | Timestamp/status rõ, không định giá như live |
| Backfill sau outage | Reconcile overlap, không append mù |

Report theo source/instrument/timeframe/range: counts, gaps, duplicates, rejected rows, latest closed bar, ingestion lag và correction count. Numeric thresholds cần baseline và source evidence; chưa quảng cáo latency/completeness.

Market/simulator acceptance fixtures cần timestamp/unit mismatch, out-of-order, replay, corrections/checksum và snapshot rollback theo adapter contract đã chọn; không kế thừa timestamp-transition assumptions từ prototype. News engine độc lập cần published-before-first-seen, late correction và uncertain mapping scenarios trước tích hợp. Model Lab split design deferred; portfolio replay vẫn phải tuân thủ availability/no-lookahead contract.

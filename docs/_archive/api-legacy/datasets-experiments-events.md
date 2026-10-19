# Dataset, experiment và event contracts — deferred

**Trạng thái:** retained from the prior hosted/Model Lab direction. Model Lab runtime and hosted experiment APIs are outside V1; do not use these contracts as current implementation requirements. Portfolio backtesting has its own local contract in [Portfolio](../07-portfolio/README.md).


## Snapshot và delivery

Manifest immutable gồm `schema_version`, `dataset_id`, `snapshot_version`, instrument/interval/range, source revisions, hashes, row count, gaps, bar-closure policy, `available_at_policy`, rights/grant version và feature eligibility. User chỉ tải các field có quyền; tài liệu nguồn không đồng nghĩa approval. Dataset market chung có thể cache theo grant; private result/portfolio không dùng public cache.

News manifest phân biệt `published_at`, `first_seen_at`, `updated_at`, availability của từng version và extraction version. Backfilled news thiếu evidence availability được đánh dấu không đủ điều kiện historical causal evaluation. CSV/Parquet/JSON dataset phải có schema, bytes và integrity hash; format cụ thể được spike P02 khóa theo browser runtime.

## Experiment và kết quả browser

Config chứa snapshot/version, instrument/timeframe, feature set/version, target/horizon, evaluation preset/splits/gap, model/params, seed, fee/slippage assumptions và runtime version. Server validate allowlist, ownership, quotas và source eligibility; không nhận Python source, shell, pickle hay executable model.

Result gồm config hash, run ID, runtime/package versions, start/end time, sample counts, split metrics, baseline metrics, backtest summary, warnings và artifact references. Tất cả output được server gán `computation_origin=client-computed`, `verification_status=unverified`; `verified=true` hoặc status từ client không tạo badge hoặc thay quyền public. Server kiểm schema/version/bytes/range và ownership, không tuyên bố đã xác minh phép tính. Non-finite values phải biểu diễn missing với reason, không serialize NaN/Infinity.

Artifacts v1 là JSON có schema allowlist (coefficients, transforms, metrics, chart series), không deserialize pickle hoặc thực thi expression. Signed URLs ngắn hạn vẫn enforce owner và không thay object key tùy ý. Quota runtime/dataset/features/artifacts được chốt từ P02 feasibility; browser bắt đầu run chỉ sau khi config lưu thành công.

Config có trạng thái `draft`; run dùng `running`, `succeeded`, `failed`, `cancelled`, `interrupted`, thống nhất [Model Lab lifecycle](../08-model-lab/experiment-lifecycle.md). Status và browser heartbeat chỉ là thông báo từ client, không có ý nghĩa chứng thực phép tính; `succeeded` chỉ có final payload hợp lệ, vẫn unverified. Hết lease không coi đang train server: hiển thị heartbeat stale/unknown rồi reconcile. Đóng tab/logout làm run interrupted; không có lời hứa resume training. Config có thể mở lại và chạy run mới, không ghi đè run trước. Progress/cancel xử lý tại Worker, API chỉ đồng bộ status/result.

## Events và observability

Event envelope mục tiêu: `event_id`, `type`, `schema_version`, `occurred_at`, `ingested_at`, `request_id`, payload tối thiểu. Source market/news thêm `source_event_at`, `first_seen_at` hoặc `available_at` theo domain, không gộp thành một timestamp. Ingestion revisions có dedup key; consumer xử lý retry idempotently.

User events chỉ cần account/workspace IDs nội bộ, capability và outcome; không ghi token/email, raw CSV, toàn portfolio, headline/content bị hạn chế hoặc experiment dataset vào telemetry. Audit mutations lưu actor/resource/revision/action và safe metadata, retention theo operations. Không tạo global ranking từ private/client-computed results.

## Nghiệm thu

Hash mismatch; grant revoked/expired download; future/leaky news không eligible; artifact lạ/version sai/quá lớn; result giả verified flag; result khác owner; crash Worker/đóng tab/retry upload; cùng run sync hai lần; missing metrics; pagination riêng tư; sửa client status không tạo server-computed evidence.

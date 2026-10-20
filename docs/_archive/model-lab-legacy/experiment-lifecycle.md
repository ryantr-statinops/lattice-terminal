# Experiment lifecycle, ownership và artifacts

> Historical/deferred design, not current runtime. Former code was replaced; see [rebuild status](../../13-rebuild/progress.md).


**Trạng thái:** archived proposal của thiết kế hosted/Model Lab cũ; không phải yêu cầu V1 hoặc contract đã triển khai. Chỉ giữ làm hồ sơ tham khảo; current product scope thuộc [Model Lab boundary](../../08-model-lab/README.md).

## Trạng thái

| State | Ý nghĩa |
|---|---|
| `draft` | Cấu hình đã lưu, chưa có run hoàn tất |
| `running` | Worker tab hiện tại đang chạy; client-reported |
| `succeeded` | Có final payload hợp lệ; computation vẫn unverified |
| `failed` | Runtime/data/model lỗi; giữ stage/error an toàn |
| `cancelled` | Người dùng yêu cầu hủy, worker đã dừng |
| `interrupted` | Reload/tab đóng/session kết thúc hoặc mất runtime; không có final result |

Experiment config và run là hai identity khác nhau; rerun tạo run mới, không ghi đè provenance lần trước. Lưu config thành công trước khi bắt đầu. API không tạo training queue. Sau reload, local run không có worker active được đánh dấu interrupted; server `running` quá hạn chỉ hiển thị mất heartbeat/client status unknown rồi reconcile, không bịa kết quả. Timeout/staleness của historical proposal này chưa được đo/chốt và không áp dụng cho V1.

## Manifest tối thiểu

Config giữ owner/workspace, instrument/timeframe, research mode, feature/target/horizon, model/preset, split, seed, fee/slippage, vốn và dataset snapshot reference. Run giữ dataset hash/row range, source revisions, availability policy, feature/target/pipeline/runtime/package versions, browser/device class, timestamps, dropped rows, metrics và warnings.

Kết quả đánh dấu `computation_origin=client-computed`, `verification_status=unverified`. Server validate schema, size, finite numbers, references và ownership; không xác thực phép tính chỉ vì payload hợp lệ. Public report chỉ từ workspace demo được chọn và review, không tự publish kết quả account. Mọi summary ghi result provenance.

Artifacts JSON theo schema allowlist: coefficients/intercept, feature order, scaler parameters, class labels, metrics, equity/trade series và manifest. Chặn non-finite values, kích thước quá lớn và unknown executable fields. Không nhận pickle, user Python hoặc executable model. Reference fixture kiểm định pipeline là quy trình của dự án, không phải dịch vụ thực thi code người dùng.

## Local cache và server sync

IndexedDB keys namespace bằng account/workspace, snapshot/run ID; user data không dùng shared cache không định danh. Dataset snapshot công khai có thể cache riêng nếu quyền cho phép, nhưng result/config/portfolio không dùng cùng namespace public. Logout/account switch dừng worker, purge private IndexedDB/buffers, xóa pending upload và chặn stale callbacks; server-saved config/results vẫn thuộc account cũ.

Server nhận cấu hình và kết quả khi người dùng lưu/đồng bộ; training arrays/working tensors ở browser, không tự upload. UI thông báo chính xác metadata/result nào được gửi; source data dùng chung vẫn đến từ server theo quyền source. Auth token không ghi vào experiment manifest hoặc logs.

Offline có thể đọc local result theo session/cache policy; chưa authenticated không khôi phục private cache sau logout. Sync retry dùng run ID/idempotency để không tạo bản sao; không ghi account từ client làm authority. API lấy principal rồi kiểm tra workspace owner trên mọi read/write; xem [API index](../../09-api/README.md).

## Nghiệm thu

Hai account không đọc/sửa được config/results của nhau, kể cả sửa IDs trực tiếp. Test logout khi worker đang chạy, upload response muộn, cache account cũ, reload, quota IndexedDB, malformed artifacts và sync retry. Config đã lưu có thể rerun từ đầu; checkpoint/resume và server recomputation đều deferred.

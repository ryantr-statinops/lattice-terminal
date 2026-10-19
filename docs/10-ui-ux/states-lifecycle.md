# Trạng thái và lifecycle V1

**Trạng thái:** UX/service requirements, chưa triển khai đầy đủ. SSI connection thuộc target local service; tab browser không phải lifecycle owner của toàn bộ ứng dụng.

| Tình huống | Hành vi/decision boundary |
|---|---|
| Sai mật khẩu | Không cấp phiên; không hiển thị secret. Password-to-encryption design vẫn pending |
| UI lock | Ngăn UI truy cập dữ liệu nhạy cảm theo thiết kế session. Local stream/paper có tiếp tục hay pause còn pending; không hứa vault unlock hoặc full RAM zeroization |
| Tab ẩn/heartbeat UI mất | Browser có thể throttle/freeze rendering. Không suy ra local service đã dừng hoặc tự chốt pause paper. Subscription/render policy và stale timers cần thiết kế riêng |
| Tab hoạt động trở lại | Xác minh session và hỏi local service về trạng thái/freshness/gaps trước khi hiển thị là live; không coi UI reconnect là upstream reconnect |
| Người dùng stop stream/paper | Target có explicit stop action; order acceptance/ledger checkpoint và kết thúc phiên cần contract simulator. Mọi kết quả vẫn simulated |
| App/local service stop hoặc crash | Đóng subscription khi orderly shutdown; khi restart đánh dấu interrupted/unknown cho đến khi feed/ledger reconcile. Không suy diễn unseen fills |
| Feed disconnect/quota/auth error | Phân loại lỗi; bounded retry cho transient failure, dừng theo auth/policy/quota rules. Giữ history hợp lệ và nhãn stale/partial |
| Session đóng/halt hoặc market state không rõ | Không mô phỏng fill như đang có executable liquidity; policy chặn/pause lệnh phải được chốt trong market/simulator contract |
| Bar thiếu/trùng/provisional | Hiển thị quality state; không dùng như bar hoàn chỉnh trong backtest |
| Backtest loading/running/cancel/error | Nêu snapshot/version và assumptions. Cancel, durable run status và interrupted recovery cần thiết kế; không giả định browser worker hoặc resume capability |
| Valuation stale/partial | Ghi nguồn, thời điểm và phần thiếu; không trình bày tổng chưa đủ giá như valuation hoàn chỉnh |
| Local write/export/restore lỗi | Báo scope và last consistent state; không báo thành công hoặc thay bản tốt bằng partial write |
| Reset/delete | Preview scope theo storage inventory; không đồng nghĩa lock, password reset hay secure erase |
| Synthetic fixtures | Nhãn xuyên suốt; không trình bày là dữ liệu SSI thật hoặc current market |

## Pending policy và phạm vi

Tab visibility, UI lock, idle timeout, lifetime của local paper session và backtest cancellation vẫn là design decisions. Không kế thừa timer/worker/sync assumptions của prototype làm V1 requirement. Local-service ownership và explicit app-stop recovery phải được giữ riêng khỏi browser rendering.

News integration chưa thuộc terminal MVP; news engine có lifecycle riêng. Model Lab/runtime/training và hosted result sync ngoài scope; không có training/download/sync UX requirement trong bảng V1 này.

## Acceptance scenarios trước implementation release

Rà wrong-password/lock, hidden/resumed tab khi local service vẫn chạy, upstream failure độc lập UI failure, explicit stop, app crash/restart, stale/partial data, interrupted backtest/paper và failed local write. Mỗi scenario phải dựa trên policy đã được quyết định, không biến pending behavior thành kiểm thử đã pass.

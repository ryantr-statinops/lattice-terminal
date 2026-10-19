# User journeys

**Trạng thái:** hành trình mục tiêu cho V1; prototype hiện tại vẫn dùng fixtures/mocks và chưa hỗ trợ các luồng hoàn chỉnh dưới đây.

## Clone and start locally

Người dùng clone repository trên Windows, làm theo hướng dẫn cài đặt, khởi chạy web/API local và mở `localhost`. First-run giải thích đường dẫn dữ liệu và giới hạn bảo mật. Luồng nhập SSI credentials chỉ được triển khai sau khi local secret storage được thiết kế; credentials không đi vào source, browser, URL hay log. Launcher một lệnh và recovery còn là quyết định mở.

## Configure SSI and inspect market data

Người dùng cấu hình SSI FastConnect Data trên local service. Ứng dụng báo trạng thái cấu hình và capability được xác nhận mà không hiển thị secret. Chỉ sau khi source gate mở cho đúng endpoint/feed, người dùng mới xem instruments, dữ liệu lịch sử/tham chiếu và chất lượng dữ liệu. Mọi màn hình nêu nguồn, thời điểm, coverage, session, provisional/closed và stale/partial/unavailable state. Không tự dùng nguồn thay thế.

## Backtest a portfolio

Người dùng chọn portfolio local, universe, snapshot được phép, khoảng ngày, chiến lược và giả định vốn/chi phí/khớp lệnh. Preview nêu coverage và gaps; kết quả lưu phiên bản snapshot, cấu hình và simulator để có thể tái lập. Quy tắc kế toán và thị trường còn phải chốt trước khi hành trình có thể triển khai.

## Paper live session

Người dùng bắt đầu phiên paper dùng feed SSI được cấp quyền. Local simulator đối chiếu feed với history rồi mô phỏng lệnh/fill. Mất kết nối, dữ liệu stale/gap, ngoài giờ hoặc restart phải chuyển sang trạng thái pause/unknown theo policy đã định nghĩa. Mọi kết quả là simulated; không có lệnh nào gửi tới broker.

## News engine độc lập

Engine tin tức quốc tế và Việt Nam được xây và vận hành như workstream riêng, với source inventory, quyền xử lý, provenance, correction và retention policy. Chỉ tích hợp vào terminal qua contract được review sau; news fixture hiện tại không phải năng lực sản phẩm. Model Lab nằm ngoài MVP đầu tiên; mock hiện tại không phải năng lực sản phẩm.

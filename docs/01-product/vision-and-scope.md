# Vision và phạm vi

**Trạng thái:** định hướng sản phẩm được chốt ngày 2026-10-18; đây là mục tiêu, không phải mô tả tính năng đã triển khai.

Research Terminal là bộ công cụ nghiên cứu mã nguồn mở, miễn phí, chạy trên máy người dùng. V1 hướng tới nhà đầu tư tự nghiên cứu thị trường Việt Nam, khởi chạy từ repository trên Windows và truy cập giao diện qua `localhost`. Sản phẩm hỗ trợ xem dữ liệu được cấp quyền, quản lý sổ cái nghiên cứu, backtest và paper trading. Không cam kết lợi nhuận và không gửi lệnh thật.

## Người dùng và quyền sở hữu

- Người dùng tự cài đặt và tự đăng ký/cấu hình dịch vụ SSI FastConnect Data nếu có entitlement phù hợp.
- Cấu hình, credentials, dữ liệu, portfolio và kết quả nghiên cứu thuộc người vận hành và được lưu trên máy của họ.
- Đăng nhập mật khẩu cục bộ là yêu cầu UX; mô hình profile, lưu secret, mã hóa dữ liệu, khóa phiên và khôi phục còn phải thiết kế.
- Giao diện dự kiến dùng tiếng Việt và hiển thị giờ `Asia/Ho_Chi_Minh`; thời gian nội bộ chuẩn hóa UTC.

## Phạm vi V1 dự kiến

- Chạy local trên Windows, không yêu cầu backend hosted, tài khoản cloud, đồng bộ nhiều thiết bị hoặc dịch vụ database từ xa.
- Tích hợp SSI FastConnect **Data** qua local service, chỉ bật các REST/feed phù hợp sau khi kiểm tra entitlement, điều khoản, quota, coverage, schema và quyền xử lý/lưu trữ.
- Xem instruments, dữ liệu tham chiếu/lịch sử và trạng thái chất lượng dữ liệu trong phạm vi được cấp.
- Portfolio nghiên cứu có backtest lịch sử và paper live simulation. Không dùng FastConnect Trading, broker credentials hay order route thật.
- News engine cho nguồn quốc tế và Việt Nam là workstream độc lập; tích hợp sau khi có source policy và contract riêng.
- Model Lab không thuộc MVP đầu tiên.

## Ngoài phạm vi

- Đặt lệnh thật, custody, margin, leverage, short hoặc tự động giao dịch.
- Hosted/multi-user service, cloud sync, chia sẻ portfolio và public market-data redisplay.
- Tích hợp news engine vào terminal trước khi engine và rights gates sẵn sàng.
- Runtime huấn luyện Model Lab và arbitrary user code.
- Installer/desktop shell; V1 bắt đầu bằng clone và chạy từ source.

## Trạng thái code hiện tại

Repository hiện là prototype fixture với React/Vite, Go Gateway, FastAPI và CLI. Market/news/portfolio đang dùng fixtures hoặc browser-local state; kết nối streaming trong UI là prototype; Model Lab trả kết quả mock. Chưa có tích hợp SSI, local secret store, auth, kho dữ liệu người dùng bền vững, backtest engine hay paper-trading engine. Các mô tả này ghi nhận trạng thái code, không mở rộng phạm vi sản phẩm.

Khi entitlement, rights hoặc chất lượng dữ liệu chưa được xác nhận, capability tương ứng phải ở trạng thái blocked/unavailable hoặc fixture-only. Không dùng fallback nguồn không được duyệt và không trình bày fixture như thị trường thật.

## Quyết định còn mở

Theo dõi quyết định và dependency tại [roadmap](../../task/next-plan.md): entitlement/điều khoản SSI; instrument classes và market coverage; fields/feed cần cho V1; lưu trữ/mã hóa/khôi phục; quy tắc tiền tệ, phí, thuế và mô phỏng; cách khởi chạy local services; phạm vi backtest và paper session.

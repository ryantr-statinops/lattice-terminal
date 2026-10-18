# Vision và phạm vi

**Trạng thái:** hướng sản phẩm được chốt ngày 2026-10-18; chi tiết vận hành, nguồn và các contract dưới đây vẫn cần hoàn thiện trước implementation.

Research Terminal là bộ hạ tầng nghiên cứu mã nguồn mở, miễn phí, chạy hoàn toàn trên máy người dùng. V1 dành cho người dùng Việt Nam tự clone repository và chạy web app trên `localhost`; chưa đóng gói thành desktop app hay vận hành dịch vụ hosted. Sản phẩm giúp người dùng khảo sát thị trường, xây và kiểm tra giả thuyết, backtest và paper trade; không hứa lợi nhuận hay thực hiện lệnh thật.

## Người dùng và cài đặt

- Người dùng đầu tiên là product owner; hướng tới người dùng Việt Nam tự nghiên cứu.
- Người dùng tự cài đặt, cấu hình và cấp quyền với SSI FastConnect Data. Ứng dụng dùng cấu hình của chính người chạy và giữ cấu hình, credentials, dữ liệu, portfolio và kết quả trên máy đó.
- Có màn hình đăng nhập chỉ bằng mật khẩu theo yêu cầu sản phẩm. Model account, mã hóa dữ liệu, reset/recovery và xử lý mất mật khẩu vẫn cần quyết định; không có email/OAuth hoặc dịch vụ auth hosted trong hướng V1.
- Hướng ban đầu là thị trường Việt Nam và tận dụng các năng lực SSI FC Data phù hợp, trong giới hạn entitlement và quyền được xác nhận cho từng endpoint/dataset.

## MVP đầu tiên

- Chạy từ source clone trên Windows, mở tại localhost. Chưa cần installer, public hosting, cloud account, database service hoặc scheduler hosted.
- Market data lấy qua SSI FastConnect Data: REST/historical, reference data và streaming được khảo sát để dùng tối đa trong phạm vi được cấp. Exact instrument classes, endpoint coverage, history depth, entitlement, quota và permitted local retention phải được xác minh trước khi bật từng nguồn.
- News engine là một workstream riêng do dự án tự xây cho nguồn quốc tế và Việt Nam. Nó sẽ được tích hợp vào Research Terminal sau; không chặn market/portfolio MVP đầu tiên.
- Portfolio có backtesting và paper live trading. Paper live dùng market feed để mô phỏng, không gửi lệnh, không dùng FastConnect Trading và không giữ trading credentials.
- Model Lab là sản phẩm/workstream sau, ngoài MVP đầu tiên.
- UI tiếng Việt, thời gian chuẩn UTC và hiển thị mặc định theo Asia/Ho_Chi_Minh.

## Không thuộc MVP đầu tiên

- Real-order execution, broker trading API, custody, margin, leverage, short hoặc tự động đặt lệnh.
- Hosted/multi-user service, đồng bộ đám mây, chia sẻ portfolio, public data redisplay hoặc thu phí.
- News ingestion tích hợp vào terminal trước khi engine riêng và source gates sẵn sàng.
- Model Lab runtime, arbitrary Python hoặc server-side training.
- Installer/desktop shell. V1 chạy trực tiếp từ repository theo hướng dẫn.

## Code hiện tại và hướng chuyển đổi

Codebase hiện là prototype fixture React/Vite + Go Gateway + FastAPI. Market/news/portfolio dùng synthetic fixtures hoặc local browser state; Model Lab là mock; Binance WebSocket chỉ là kết nối thử nghiệm. Chưa có SSI integration, local secret/config management, password login, persisted local user workspace, backtesting engine hay paper-trading engine. Binance contracts/fixtures là legacy prototype material, không phải quyết định provider cho MVP này.

Khi một capability chưa có quyền, entitlement hoặc data quality evidence, app phải hiển thị unavailable/partial rõ ràng; không tự chuyển sang source khác hoặc giả dữ liệu.

## Decisions còn mở

Xem roadmap tại [task/next-plan](../../task/next-plan.md). Các quyết định cần user duyệt tiếp gồm: SSI service/entitlement thực tế; HOSE/HNX/UPCOM và có bao gồm phái sinh/trái phiếu hay không; dữ liệu nào trong stream cần cho V1; persistence/encryption và password recovery; portfolio currency, fees, taxes và market rules; cách chạy các local services; phạm vi backtesting và paper live.

# Quy Định & Bất Biến Kỹ Thuật (Constraints & Invariants)

**Trạng thái:** Chuẩn mực bất biến cốt lõi (Core Invariants) cho toàn bộ kiến trúc và triển khai của **Research Terminal** (Local Bloomberg Terminal cho TTCK Việt Nam). Mọi module, adapter, service và giao diện người dùng phải tuân thủ nghiêm ngặt các điều khoản trong tài liệu này.

---

## 1. Bất Biến Vận Hành & Sở Hữu (Local-First & Ownership)

1. **Cục Bộ 100% (Local-only Execution):**
   - Ứng dụng chạy hoàn toàn trên máy trạm cá nhân của người dùng (mục tiêu chính: Windows 10/11) tại địa chỉ loopback nội bộ (`127.0.0.1` / `localhost`).
   - Không triển khai backend tập trung, không máy chủ đám mây trung gian, không dịch vụ web đa người dùng (no multi-tenancy).
2. **Không Telemetry, Không Phân Tích Từ Xa (Zero Telemetry):**
   - Không gửi bất kỳ dữ liệu hành vi, chỉ số hiệu năng, lịch sử xem mã, hay log lỗi ra bất kỳ máy chủ nào do dự án quản lý.
   - Kết nối mạng duy nhất được phép khởi tạo từ ứng dụng là kết nối trực tiếp từ máy người dùng đến các endpoint dịch vụ dữ liệu chính thức do người dùng cấu hình (cụ thể: SSI FastConnect Data API & Streaming Hub).
3. **Chủ Quyền Dữ Liệu Thuộc Về Người Dùng (Data Sovereignty):**
   - Cấu hình, dữ liệu thị trường được phép lưu, portfolio và kết quả nghiên cứu nằm trên máy người dùng; đường dẫn, backup, export, delete và recovery phải được định nghĩa trước release.
   - Xóa thư mục source hoặc một database không chứng minh toàn bộ dữ liệu đã bị xóa. Application data, browser storage, OS secret store, logs và backups/exports có lifecycle riêng theo [storage inventory](04-data/storage-and-retention.md#storage-inventory-and-deletion-boundaries). Dự án không tự upload; các bản sao người dùng tạo nằm ngoài phạm vi xóa tự động chưa được thiết kế.

---

## 2. Bất Biến Nguồn Dữ Liệu & Bản Quyền (Market Data & Rights)

1. **SSI FastConnect Data Là Nguồn Dữ Liệu Mục Tiêu Duy Nhất Cho V1:**
   - SSI FastConnect Data là provider direction cho V1; entitlement, coverage, điều khoản và quyền lưu trữ theo tài khoản chưa được xác nhận.
   - Người dùng tự đăng ký và sử dụng cặp định danh truy cập cá nhân: `ConsumerID` và `ConsumerSecret`.
2. **Chỉ Đọc Dữ Liệu — Tuyệt Đối Không Gửi Lệnh Thật (Read-Only Data Only):**
   - Chỉ sử dụng SSI FastConnect Data (Market Data API).
   - **Tuyệt đối không tích hợp SSI FastConnect Trading** hay bất kỳ API đặt lệnh thật nào của công ty chứng khoán. Ứng dụng không có khả năng và không bao giờ yêu cầu private key / mã PIN / mã OTP đặt lệnh thật của người dùng.
3. **Quy Tắc Source Gate (Acceptance Gate):**
   - Mọi nguồn dữ liệu phải vượt qua 4 điều kiện trước khi được kích hoạt trực tiếp trong code production:
     `documented`, `access-tested`, `rights-confirmed`, `approved` là evidence flags độc lập; production capability cần đủ evidence phù hợp và approval cho đúng purpose.
   - Default là fixture-only khi chưa được duyệt. Access probe có giới hạn cần authorization riêng theo [probe policy](03-market-research/source-register.md#access-probes-and-operating-states); không cấp quyền production hoặc lưu payload. Không hardcode credential hay bypass gate.
4. **Ghi Nhận Bản Quyền Nguồn Minh Bạch (Explicit Attribution):**
   - Mọi dữ liệu hiển thị trên giao diện hoặc lưu trong cơ sở dữ liệu local đều phải gắn nhãn nguồn gốc xuất xứ (`SSI-FC-DATA` hoặc `SYNTHETIC-FIXTURE`) kèm timestamp chính xác. Không che giấu nguồn gốc hoặc mạo danh dữ liệu.

---

## 3. Bất Biến Bảo Mật & Quản Lý Thông Tin Nhạy Cảm (Security & Secrets)

1. **Không Lưu Credential Trong Trình Duyệt Web (No Web Storage for Secrets):**
   - Không lưu `ConsumerSecret`, plaintext local password hoặc token dài hạn trong browser storage, frontend bundle, URL, log, fixture hay Git. Thuật ngữ local password không hàm ý đã chọn master-key/vault design.
   - `ConsumerSecret` thuộc local service boundary; chỉ nhận credentials thật sau khi thiết kế lưu trữ/bảo vệ được review và scope sử dụng được cho phép.
2. **Local Secret Storage:**
   - Phải chọn và review Windows secret store/encrypted vault trước khi nhập credentials thật; implementation technology chưa được chốt.
   - Không lưu plaintext credential trong file cấu hình, browser hoặc Git repository.
3. **Xác Thực Cục Bộ (Local Authentication & Profile Lock):**
   - Password-only login là yêu cầu UX. Chưa quyết định mật khẩu chỉ khóa phiên hay tham gia giải mã dữ liệu; profile boundary, key management, timeout và recovery còn pending.
   - Thiết kế phải giới hạn thời gian giữ secret trong memory và quyền truy cập khi khóa phiên. Không hứa xóa sạch mọi bản sao RAM: mức bảo vệ phải được đánh giá theo runtime/OS, không giả định zeroization tuyệt đối.

---

## 4. Bất Biến Nghiệp Vụ Giả Lập & Kiểm Thử (Trading Simulation & Quant)

1. **Mô Phỏng Thực Tế (Paper Trading Realism):**
   - Paper Trading và Backtest phải tuân thủ nghiêm ngặt các quy tắc vận hành của thị trường chứng khoán Việt Nam:
     - Session/auction rules phải tách theo venue/instrument và có ngày hiệu lực; không khẳng định ATO/ATC luôn ưu tiên trước mọi LO.
     - Price limits, reference price, tick/lot và giới hạn lệnh cần evidence trước khi cấu hình simulator; không có universal numeric defaults.
     - Phân biệt chu kỳ thanh toán T+2 với thời điểm tài sản khả dụng; áp dụng instrument, lịch và phiên bản quy tắc đúng ngày hiệu lực theo [settlement evidence](07-portfolio/vn-market-rules.md#4-thanh-toán-t2-và-thời-điểm-tài-sản-khả-dụng).
     - Thuế/phí cần nguồn, phạm vi nhà đầu tư/instrument và ngày hiệu lực; slippage/fill là giả định mô phỏng được ghi version. Xem [market rules](07-portfolio/vn-market-rules.md).
2. **Không Lookahead Bias Trong Backtesting:**
   - Động cơ kiểm thử chiến lược (Backtest Engine) tuyệt đối không được sử dụng dữ liệu của tương lai để tính toán tín hiệu cho quá khứ (không dùng nến chưa đóng, không dùng giá tương lai của cùng phiên để khớp lệnh hiện tại).
3. **Cảnh Báo Rủi Ro Minh Bạch:**
   - Mọi kết quả backtest và giao dịch giả lập đều phải đi kèm nhãn xác nhận rõ ràng: *Đây là kết quả mô phỏng giả lập trong môi trường quá khứ/paper, không phản ánh cam kết lợi nhuận trong đầu tư thực tế*.

---

## 5. Danh Sách Các Hạng Mục Nằm Ngoài Phạm Vi V1 (Out of Scope for V1)

Các tính năng sau đây **tuyệt đối không triển khai trong V1** để giữ tập trung tối đa vào trải nghiệm Local Terminal cốt lõi:
- ❌ **Đặt lệnh thật vào tài khoản chứng khoán (Real Order Execution).**
- ❌ **Dịch vụ máy chủ tập trung, đồng bộ tài khoản đa thiết bị qua Cloud.**
- ❌ **Hệ thống huấn luyện mô hình học máy phức tạp (Model Lab) — Hoãn sang V2.**
- ❌ **Tích hợp News Engine vào terminal trong MVP đầu tiên — engine là workstream độc lập, cần source gates và integration contract trước khi kết nối.**

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
   - Mọi cấu hình, dữ liệu thị trường đã tải (nến, tick, bảng giá), danh mục theo dõi, lịch sử lệnh mô phỏng (Paper Trading), và kết quả kiểm thử chiến lược (Backtest) được lưu trữ trực tiếp trên ổ cứng máy người dùng.
   - Khi người dùng xóa thư mục ứng dụng hoặc xóa file cơ sở dữ liệu local, toàn bộ dữ liệu bị tiêu hủy hoàn toàn, không có bản sao lưu trên đám mây.

---

## 2. Bất Biến Nguồn Dữ Liệu & Bản Quyền (Market Data & Rights)

1. **SSI FastConnect Data Là Nguồn Dữ Liệu Mục Tiêu Duy Nhất Cho V1:**
   - Ứng dụng khai thác dữ liệu chứng khoán cơ sở Việt Nam (HOSE, HNX, UPCOM) thông qua API chính thức **SSI FastConnect Data (FC Data)**.
   - Người dùng tự đăng ký và sử dụng cặp định danh truy cập cá nhân: `ConsumerID` và `ConsumerSecret`.
2. **Chỉ Đọc Dữ Liệu — Tuyệt Đối Không Gửi Lệnh Thật (Read-Only Data Only):**
   - Chỉ sử dụng SSI FastConnect Data (Market Data API).
   - **Tuyệt đối không tích hợp SSI FastConnect Trading** hay bất kỳ API đặt lệnh thật nào của công ty chứng khoán. Ứng dụng không có khả năng và không bao giờ yêu cầu private key / mã PIN / mã OTP đặt lệnh thật của người dùng.
3. **Quy Tắc Source Gate (Acceptance Gate):**
   - Mọi nguồn dữ liệu phải vượt qua 4 điều kiện trước khi được kích hoạt trực tiếp trong code production:
     `documented=true` $\rightarrow$ `access-tested=true` $\rightarrow$ `rights-confirmed=true` $\rightarrow$ `approved=true`.
   - Trong quá trình phát triển khi Gate chưa được duyệt hoàn toàn (`approved=false`), toàn bộ code frontend, gateway và services chỉ được phép chạy trên bộ dữ liệu giả lập chuẩn hóa (**Synthetic Fixtures**). Không được phép hardcode credential hay bypass gate.
4. **Ghi Nhận Bản Quyền Nguồn Minh Bạch (Explicit Attribution):**
   - Mọi dữ liệu hiển thị trên giao diện hoặc lưu trong cơ sở dữ liệu local đều phải gắn nhãn nguồn gốc xuất xứ (`SSI-FC-DATA` hoặc `SYNTHETIC-FIXTURE`) kèm timestamp chính xác. Không che giấu nguồn gốc hoặc mạo danh dữ liệu.

---

## 3. Bất Biến Bảo Mật & Quản Lý Thông Tin Nhạy Cảm (Security & Secrets)

1. **Không Lưu Credential Trong Trình Duyệt Web (No Web Storage for Secrets):**
   - Trình duyệt (`apps/web` React UI) tuyệt đối không được lưu `ConsumerSecret`, mật khẩu master, hay token dài hạn vào `localStorage`, `sessionStorage`, hoặc cookie không an toàn.
   - `ConsumerSecret` chỉ được xử lý tại tiến trình local backend và được mã hóa lưu trữ an toàn.
2. **Bảo Mật Bằng Cơ Chế Mã Hóa Của Hệ Điều Hành (OS-Level Credential Protection):**
   - Trên Windows, các khóa nhạy cảm (`ConsumerSecret`, access tokens) phải được bảo vệ bằng cơ chế mã hóa cấp hệ điều hành (ví dụ: **Windows DPAPI** hoặc **Windows Credential Manager**).
   - Không lưu trữ plaintext credential trong các file cấu hình `.env`, `.json`, hay commit vào Git repository.
3. **Xác Thực Cục Bộ (Local Authentication & Profile Lock):**
   - Ứng dụng sử dụng cơ chế đặt mật khẩu cục bộ (Local Profile Password) để mở khóa vault giải mã cấu hình và mở phiên làm việc.
   - Khi hết phiên (timeout) hoặc khi người dùng chủ động Khóa (Lock), toàn bộ khóa nhạy cảm trong bộ nhớ RAM phải được giải phóng (zeroize/clear).

---

## 4. Bất Biến Nghiệp Vụ Giả Lập & Kiểm Thử (Trading Simulation & Quant)

1. **Mô Phỏng Thực Tế (Paper Trading Realism):**
   - Paper Trading và Backtest phải tuân thủ nghiêm ngặt các quy tắc vận hành của thị trường chứng khoán Việt Nam:
     - Đúng khung giờ các phiên: Khớp lệnh định kỳ mở cửa (ATO), Khớp lệnh liên tục, Khớp lệnh định kỳ đóng cửa (ATC).
     - Đúng biên độ giá trần/sàn: HOSE $\pm7\%$, HNX $\pm10\%$, UPCOM $\pm15\%$.
     - Đúng bước giá (Tick size) và quy định lô chẵn tối thiểu (100 cổ phiếu).
     - Đúng chu kỳ thanh toán chứng khoán (T+2.5) và tiền bán (T+2).
     - Tính toán đầy đủ thuế thu nhập cá nhân khi bán (0.1%) và phí giao dịch ước tính.
2. **Không Lookahead Bias Trong Backtesting:**
   - Động cơ kiểm thử chiến lược (Backtest Engine) tuyệt đối không được sử dụng dữ liệu của tương lai để tính toán tín hiệu cho quá khứ (không dùng nến chưa đóng, không dùng giá tương lai của cùng phiên để khớp lệnh hiện tại).
3. **Cảnh Báo Rủi Ro Minh Bạch:**
   - Mọi kết quả backtest và giao dịch giả lập đều phải đi kèm nhãn xác nhận rõ ràng: *Đây là kết quả mô phỏng giả lập trong môi trường quá khứ/paper, không phản ánh cam kết lợi nhuận trong đầu tư thực tế*.

---

## 5. Danh Sách Các Hạng Mục Nằm Ngoài Phạm Vi V1 (Out of Scope for V1)

Các tính năng sau đây **tuyệt đối không triển khai trong V1** để giữ tập trung tối đa vào trải nghiệm Local Terminal cốt lõi:
- ❌ **Đặt lệnh thật vào tài khoản chứng khoán (Real Order Execution).**
- ❌ **Dịch vụ máy chủ tập trung, đồng bộ tài khoản đa thiết bị qua Cloud.**
- ❌ **Thị trường Tiền mã hóa (Crypto / Binance) và Ngoại hối (FX) — Đã chuyển sang `_archive`.**
- ❌ **Hệ thống huấn luyện mô hình học máy phức tạp (Model Lab) — Hoãn sang V2.**
- ❌ **Tin tức đa kênh tự động (News Ingestion Engine) — Tách thành dự án độc lập, chưa tích hợp vào V1.**

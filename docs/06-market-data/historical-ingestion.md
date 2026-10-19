# Dữ Liệu Lịch Sử Thị Trường (Historical Ingestion) — Định Hướng SSI FastConnect Data

**Trạng thái:** Định hướng mục tiêu V1.  
SSI FastConnect Data là nguồn dữ liệu lịch sử và tham chiếu duy nhất cho thị trường chứng khoán Việt Nam (HOSE, HNX, UPCOM). Tài liệu thiết kế cũ cho Binance đã được lưu trữ tại [`docs/_archive/market-data-legacy/historical-ingestion-binance.md`](../_archive/market-data-legacy/historical-ingestion-binance.md).

---

## 1. Mục Tiêu V1 Với SSI FastConnect Data

Khi cổng kết nối SSI được duyệt đầy đủ trong [Source Register](../03-market-research/source-register.md):
1. **Lịch sử nến ngày (Daily OHLC):** Lấy toàn bộ lịch sử giá đóng/mở/cao/thấp và khối lượng của các mã cổ phiếu và chỉ số (VN-Index, VN30, HNX-Index).
2. **Lịch sử nến trong ngày (Intraday OHLC):** Phục vụ phân tích kỹ thuật và kiểm thử chiến lược (Backtest) trên các khung thời gian tiêu chuẩn (`1m`, `5m`, `15m`, `1h`).
3. **Dữ liệu tham chiếu (Reference Data):** Danh sách mã chứng khoán đang niêm yết, sàn giao dịch, tình trạng đình chỉ/giao dịch, bước giá, và thông tin cổ tức/chia tách cơ bản.

---

## 2. Nguyên Tắc Chuẩn Hóa & Bất Biến Dữ Liệu Local

1. **Khóa Tự Nhiên (Natural Identity):**
   - Định danh nến: `venue` (HOSE/HNX/UPCOM), `symbol` (ví dụ: `SSI`, `VNM`, `HPG`), `interval` (`1d`, `1h`, `15m`, `5m`, `1m`), và `open_time_utc`.
2. **Xử Lý Timezone & Session:**
   - SSI trả timestamp theo giờ Việt Nam (UTC+7). Mọi điểm thời gian lưu trữ trong database local đều được quy đổi chuẩn hóa sang **UTC timestamp**. Giao diện người dùng sẽ định dạng lại sang `Asia/Ho_Chi_Minh`.
   - Phân định rõ nến thuộc phiên ATO (09:00 - 09:15), phiên Khớp lệnh liên tục, và phiên ATC (14:30 - 14:45).
3. **Tính Bất Biến & Chống Sửa Đổi Dữ Liệu (Immutability):**
   - Chỉ nến đã đóng phiên (`is_closed = true`) mới được đưa vào tập dữ liệu dùng cho Backtesting. Nến đang nhảy trong phiên chỉ được lưu dưới dạng provisional/live buffer.
   - Không tự ý nội suy (forward-fill) hoặc bịa đặt nến cho các khoảng thời gian thị trường ngừng giao dịch (cuối tuần, nghỉ lễ, hoặc mã bị tạm ngừng giao dịch).
4. **Chi Tiết Adapter Contract:**
   - Xem chi tiết model, payload mẫu và quy tắc parse tại [ssi-adapter-contract.md](ssi-adapter-contract.md).

# Dữ Liệu Lịch Sử Thị Trường (Historical Ingestion) — Định Hướng SSI FastConnect Data

**Trạng thái:** hướng thiết kế V1; chưa triển khai và phụ thuộc source gate. SSI là provider direction duy nhất hiện được chọn, nhưng coverage theo venue/instrument, entitlement, history depth, timestamp semantics và quyền local retention chưa xác minh. Không giả định mọi venue hoặc feed đều được hỗ trợ.

---

## 1. Mục Tiêu V1 Với SSI FastConnect Data

Production ingestion cần source approval đầy đủ. [Scoped probe](../03-market-research/source-register.md#access-probes-and-operating-states) là kiểm tra riêng có giới hạn; không tạo production snapshot hoặc ngầm cấp quyền lưu history. Khi production capability được duyệt trong [Source Register](../03-market-research/source-register.md):
1. Đánh giá daily OHLC, intraday OHLC và reference data trong đúng entitlement.
2. Chốt supported instruments, intervals, history depth, adjustment semantics, fields và quota dựa trên evidence tài khoản và API.
3. Chỉ ingest/persist dữ liệu sau khi quyền lưu trữ, research use và retention được xác nhận.

---

## 2. Nguyên Tắc Chuẩn Hóa & Bất Biến Dữ Liệu Local

1. **Khóa Tự Nhiên (Natural Identity):**
   - Candidate identity: `venue`, board/market type, instrument class, native symbol, interval và open time UTC; chốt sau khi mapping schema của nguồn được xác minh.
2. **Xử Lý Timezone & Session:**
   - Không giả định timezone/unit do provider trả về; giữ raw timestamp/unit và xác minh theo endpoint trước khi chuẩn hóa UTC. UI định dạng `Asia/Ho_Chi_Minh`.
   - Session labels cần đối chiếu với market calendar và semantics feed trước khi dùng trong simulator.
3. **Tính Bất Biến & Chống Sửa Đổi Dữ Liệu (Immutability):**
   - Chỉ bar đã đóng theo quy tắc nguồn/calendar đã xác minh mới đủ điều kiện backtest. Nến live/provisional được phân biệt riêng.
   - Không tự ý nội suy (forward-fill) hoặc bịa đặt nến cho các khoảng thời gian thị trường ngừng giao dịch (cuối tuần, nghỉ lễ, hoặc mã bị tạm ngừng giao dịch).
4. **Chi Tiết Adapter Contract:**
   - Xem ranh giới chuẩn bị adapter, capability cần xác minh, yêu cầu chuẩn hóa và approval gates tại [ssi-adapter-contract.md](ssi-adapter-contract.md). Payload mẫu, schema cụ thể và parser rules vẫn chờ xác minh tài liệu/entitlement của nguồn.

# Design và accessibility
**Trạng thái:** target.

Ưu tiên local setup, khảo sát market data và portfolio simulation theo product scope; news integration để sau. Giữ visual primitives dùng lại được sau inventory. Màu accent đồng bộ `#21684e` theo ADR-014; typography/color tokens phải kiểm contrast.

- Responsive desktop/tablet cho research; ở màn nhỏ giữ source/quality labels, bảng và report đọc được. Không đặt mobile training hoặc news-first workflow làm yêu cầu V1.
- Dùng màu cùng text/icon, không chỉ xanh/đỏ cho tăng/giảm hay lỗi.
- Keyboard navigation, focus rõ, semantic labels, error summaries và screen-reader-friendly tables.
- Number formatting tiếng Việt; CSV/API dùng canonical decimals. Ghi rõ currency đã chốt (reporting currency vẫn pending) và timezone UTC/Asia/Ho_Chi_Minh.
- Chart có table/summary thay thế; giảm animation khi prefers-reduced-motion.
- Price updates không làm focus nhảy hoặc screen reader đọc từng tick.
- Loading, data stale và permission/source unavailable là các trạng thái khác nhau.
- Risk/model caveats gắn ngay report liên quan, không dùng banner chung thay cho source/time evidence.

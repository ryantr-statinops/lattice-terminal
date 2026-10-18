# Design và accessibility
**Trạng thái:** target.

Ưu tiên đọc tin và so sánh bối cảnh, không nhồi chart/indicator mặc định. Giữ visual primitives dùng lại được sau inventory, không giữ copy/branding nhà ở. Có thể giữ Royal Blue làm token tạm thời; typography/color tokens phải kiểm contrast, không khẳng định đã restyle.

- Responsive desktop/tablet; mobile ưu tiên đọc news/portfolio/report. Training mobile chỉ bật sau browser benchmark.
- Dùng màu cùng text/icon, không chỉ xanh/đỏ cho tăng/giảm hay lỗi.
- Keyboard navigation, focus rõ, semantic labels, error summaries và screen-reader-friendly tables.
- Number formatting tiếng Việt but CSV/API use canonical decimals; clearly label the confirmed currency (VND/currency decision pending) and UTC/Asia_Ho_Chi_Minh.
- Chart có table/summary thay thế; giảm animation khi prefers-reduced-motion.
- Price updates không làm focus nhảy hoặc screen reader đọc từng tick.
- Loading, data stale và permission/source unavailable là các trạng thái khác nhau.
- Risk/model caveats gắn ngay report liên quan, không dùng banner chung thay cho source/time evidence.

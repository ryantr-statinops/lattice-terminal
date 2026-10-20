# Design và accessibility
**Trạng thái:** implemented fixture UI; manual screen-reader and broader browser coverage remain.

Ưu tiên local setup, khảo sát market data và portfolio simulation theo product scope; news integration để sau. Giữ visual primitives dùng lại được sau inventory. Appearance dùng màu theo vai trò; accent mặc định #4DB5FF tách khỏi tăng/giảm. Preset typography/color tokens được kiểm contrast; tùy chỉnh tương phản thấp có cảnh báo.

- Responsive desktop/tablet cho research; ở màn nhỏ giữ source/quality labels, bảng và report đọc được. Không đặt mobile training hoặc news-first workflow làm yêu cầu V1.
- Dùng màu cùng text/icon, không chỉ xanh/đỏ cho tăng/giảm hay lỗi.
- Keyboard navigation, focus rõ, semantic labels, error summaries và screen-reader-friendly tables.
- Number formatting tiếng Việt; CSV/API dùng canonical decimals. Ghi rõ currency VND đã chốt và timezone UTC/Asia/Ho_Chi_Minh.
- Chart có table/summary thay thế; giảm animation khi prefers-reduced-motion.
- Price updates không làm focus nhảy hoặc screen reader đọc từng tick.
- Loading, data stale và permission/source unavailable là các trạng thái khác nhau.
- Risk/model caveats gắn ngay report liên quan, không dùng banner chung thay cho source/time evidence.

## Terminal interaction acceptance

Dialogs use native modal behavior plus focus trapping/return; pending operations prevent duplicate submissions and cancellation. File tree uses arrow keys and a roving Tab entry. Ctrl/Cmd+S and Ctrl/Cmd+Enter are captured only inside the workspace, outside open dialogs. Separators support arrow keys (8px, Shift 32px), pointer capture and persisted bounded sizes. Route navigation returns focus to the main content.

Screen review covers desktop/tablet sizes, with table/pane scrolling contained inside panels. Reduced motion is respected; background refresh preserves data/focus. Editor lazy-load failures stay inside the editor pane and offer a reload action; normal dirty-buffer browser warnings still apply. Automated tests cover the high-risk interaction and persistence cases; this is not a complete assistive-technology audit.

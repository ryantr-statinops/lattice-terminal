# Trạng thái và lifecycle
**Trạng thái:** target.

| Tình huống | Hành vi |
|---|---|
| Mật khẩu sai | Không cấp phiên; không hiển thị secret. Chưa chọn vault/encryption mechanism |
| Khóa profile | Ngăn UI truy cập dữ liệu nhạy cảm theo thiết kế session; tác động tới live/paper còn pending, không hứa xóa sạch mọi bản sao RAM |
| Reset local | Luồng riêng với inventory/phạm vi xóa và recovery đã review; không đồng nghĩa lock hoặc đổi mật khẩu |
| Tab ẩn/heartbeat mất | Live paused sau grace được P02 khóa; browser có thể throttle/freeze nên không hứa timer chính xác |
| Tab hoạt động trở lại | Xác minh session, snapshot/backfill rồi nối stream |
| Feed ngắt/region inaccessible | Reconnecting có backoff hoặc unavailable; không silent proxy bypass |
| Bar thiếu/trùng/nến mở | Quality flag; không đưa vào feature như bar đầy đủ |
| News không có/nguồn unapproved | Empty/source-limited state, không bịa tin hoặc timestamp |
| Worker download/crash/unsupported | Tách loading runtime và run; cho retry/cancel; view-only nếu không hỗ trợ |
| Đóng tab khi train | Run có thể interrupted; config đã lưu, không hứa background/resume |
| Result sync lỗi | Giữ bản local theo owner, cho retry idempotent; ghi chưa sync |
| Valuation stale | Ghi thời điểm/nguồn, hạn chế kết luận P&L realtime |
| Demo synthetic/replay | Nhãn xuyên suốt, không trình bày là current market |

Không âm thầm đổi model, source hoặc dataset khi fallback; record version/reason. UX tests bao phủ tab hide/resume/logout cùng lúc đang train/stream.

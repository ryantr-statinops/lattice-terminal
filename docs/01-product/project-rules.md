# Quy tắc sản phẩm

**Trạng thái:** các nguyên tắc sau theo hướng local-first được chốt ngày 2026-10-18; các điểm chưa quyết định được liệt kê trong [roadmap](../../task/next-plan.md).

1. V1 là mã nguồn mở, miễn phí, clone và chạy local trên Windows; không phụ thuộc backend hay dịch vụ hosted để dùng chức năng cốt lõi.
2. Mỗi bản chạy dùng cấu hình, SSI credentials, market data, portfolio, backtest và paper-trading history của người vận hành đó. Không gửi nội dung/secret lên dịch vụ dự án.
3. Chỉ dùng SSI FastConnect Data, không FastConnect Trading. Credentials là secret: không commit, log, đưa vào browser bundle, URL, crash report hoặc fixture.
4. Dùng tối đa những capability SSI phù hợp với nhu cầu và entitlement thực tế; mỗi REST/stream product có access, quota, storage/display permission và evidence riêng. Tài liệu endpoint không tự chứng minh quyền lưu trữ.
5. News engine được xây riêng cho nguồn quốc tế và Việt Nam, theo source-specific policy; tích hợp vào terminal sau. RSS/link access không tự cấp quyền lưu full-text, dịch, ML hoặc redisplay.
6. Hiển thị nguồn, coverage, freshness, gaps, provisional/closed state và unavailable/partial chính xác. Unknown khác zero; không tự fill missing prices/volume.
7. Portfolio v1 chỉ mô phỏng nghiên cứu: backtest và paper live trading, không có order route, broker account, margin hoặc custody.
8. Tất cả timestamps nội bộ dùng UTC; UI có thể hiển thị Asia/Ho_Chi_Minh. Decimal tài chính giữ chính xác qua parse/serialize.
9. Password-only login là yêu cầu UX, không được xem như encryption-at-rest hoặc recovery model. Credential storage, local encryption, profile isolation và reset/recovery phải được thiết kế trước khi lưu dữ liệu nhạy cảm.
10. Synthetic fixtures được nhận diện rõ là giả lập. Chúng không chứng minh quyền nguồn, market access hoặc chất lượng dữ liệu thật.
11. Model Lab không nằm trong MVP đầu tiên. Backtesting cho portfolio được thiết kế độc lập, không kéo toàn bộ runtime Model Lab vào scope.
12. Không tự động cập nhật provider/permission hoặc mở rộng instrument classes. Khi capability không được cấp hoặc lỗi policy, dừng an toàn và báo trạng thái.

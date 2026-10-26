# FiinGroup API DataFeed

**Rà soát:** 26/10/2026. **Trạng thái:** API catalogue công khai rộng; quyền, gói dịch vụ và production access cần tư vấn/đăng ký thương mại. Chưa có credential hoặc payload được phép để xác minh thực tế.

## Sản phẩm và catalogue

Tài liệu [API Trading catalogue](https://datafeed.fiingroup.vn/api-datafeed-en/api-trading) liệt kê các nhóm dataset sau. Mỗi endpoint/version là capability độc lập; catalogue không có nghĩa mọi gói thuê bao đều bao gồm tất cả endpoint.

| Nhóm | Dataset được liệt kê |
|---|---|
| Cổ phiếu/chỉ số | HOSE, HNX, UPCoM stock V2; chỉ số từng sàn; adjusted price ratio; consensus. Stock V2 nêu EOD, giao dịch khối ngoại, giá điều chỉnh. |
| Chứng quyền | Dữ liệu giao dịch, thông tin sản phẩm, nhóm, giao dịch khối ngoại. |
| Phái sinh | Giao dịch HNX, thông tin cơ bản, nhóm, proprietary, price data. |
| Quỹ | Thông tin quỹ, danh mục, báo cáo NAV, báo cáo tài chính và các bảng thay đổi/đầu tư/tài sản. |
| Trái phiếu | Thông tin cơ bản, coupon/lãi, ước tính lãi thả nổi, tài sản bảo đảm, phát hành, tổ chức liên quan, chuyển đổi, lịch thanh toán/chuộc lại/sự kiện; thống kê giao dịch doanh nghiệp, YTM; giao dịch trái phiếu chính phủ, yield curve/yield/đấu thầu. |
| Khác | Giao dịch tự doanh cổ phiếu, chứng quyền, phái sinh. |

[FiinGroup giới thiệu](https://fiingroup.vn/en/financial-investment.html) giải pháp dữ liệu cho cổ phiếu, trái phiếu, quỹ và vĩ mô, đồng thời mô tả API Datafeed là giải pháp tích hợp cho hệ thống nội bộ/nền tảng tài chính. Luồng công khai kêu gọi đăng ký tư vấn; không công bố bảng giá/API SLA/quyền lưu dữ liệu.

## Thông tin chưa được xác nhận công khai

- Phiên bản schema cụ thể theo endpoint, authentication/token/refresh, sandbox, quota, rate limit, pagination, lịch sử sâu, timezone và đơn vị cần lấy từ tài liệu được cấp khi onboarding.
- Không suy ra live streaming, quote/depth, trade tick, sequence/reconnect hay backfill từ các trang API Trading. Từng endpoint được liệt kê cần phân loại historical/EOD/live và semantics.
- Catalogue có giá điều chỉnh và dữ liệu khối ngoại cho một số nhóm; cần xác minh phương pháp điều chỉnh, corporate action nguồn, revision/correction và thời điểm công bố.
- NAV, yield, bond payment và dữ liệu tài chính có semantics riêng; giữ dataset định lượng tương ứng thay vì ép vào OHLC candle.
- Asset IDs, mã phát hành, mã hợp đồng phái sinh, currency, vòng đời và coverage theo sàn cần xác nhận trong API schemas/mẫu payload.
- Account/balance/positions/transaction/order/fill broker không được catalogue API Datafeed này chứng minh; không coi FiinGroup là broker account API.
- Phí, quyền hiển thị, lưu local, backtest, tạo dữ liệu phái sinh và xuất dữ liệu phải được xác định trong hợp đồng/gói sản phẩm.

## Hướng tích hợp

Tạo endpoint inventory theo từng dataset và version; yêu cầu bộ mẫu được phép sử dụng, tài liệu auth, coverage/retention, đơn vị, lịch công bố, quota và rights. Kiểm thử parser offline bằng fixture đã được cho phép. Trạng thái ban đầu: **có tài liệu catalogue; chờ tài khoản/gói/quyền để đánh giá production**. Không chạy live query hoặc lưu payload trước khi được cấp quyền. Mỗi dataset/operation đủ điều kiện trở thành một `P-fiingroup-*` task/commit riêng.

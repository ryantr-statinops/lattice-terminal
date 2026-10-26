# FireAnt REST API

**Rà soát:** 26/10/2026. **Trạng thái:** OpenAPI REST v1.0.0 có public catalogue và OAuth scope rõ; quyền sử dụng, quota/plan và phù hợp OAuth flow cho app local cần xác nhận. Các scope giao dịch ghi cả quyền đặt/sửa/hủy lệnh; sản phẩm chỉ dùng scope read-only và không gọi các route write.

## Tài liệu và xác thực

Tài liệu tại [api.fireant.vn](https://api.fireant.vn/) công bố RESTFUL API v1.0.0 và tải OpenAPI specification. OAuth2 được đặc tả theo **Implicit Grant**, authorization URL `https://accounts.fireant.vn/connect/authorize`; docs cũng liệt kê API refresh-token nhưng không thể mặc định authorization flow phù hợp native/local app. Yêu cầu vendor xác nhận flow được hỗ trợ hiện nay (PKCE/loopback nếu có), token lifetime, refresh semantics, redirect URI đăng ký và tài khoản/quyền cần có.

## Catalogue có trong spec

Public spec cho thấy các nhóm endpoint về companies/finance, market/price/stock, tài khoản, bài viết/news/social, funds/FMarket và dữ liệu tham chiếu. Cần lập inventory trực tiếp từ OpenAPI file trước khi viết adapter để ghi endpoint, response schema và scopes chính xác; tên nhóm trong spec không xác nhận entitlement hay freshness.

| Capability | Bằng chứng trong spec | Trạng thái tích hợp dự kiến |
|---|---|---|
| Company/financial data | `companies-read`, `finance-read` scopes. | Dataset riêng; cần xác định coverage, historical depth, revision và rights. |
| Market/stock prices | API có các nhóm dữ liệu mã/chứng khoán/giá. | Phân biệt historical/EOD/intraday/live, bar semantics, units và pagination từ schema từng route. |
| Broker accounts | `accounts-read`, endpoint account liên quan và liên kết account. | Chỉ endpoint đọc snapshot được xét; hỏi scope/consent và account ownership. |
| Orders | `orders-read` và `orders-write`; tài liệu mô tả orders-write cho đặt/sửa/hủy. | Chỉ review GET read-only khi cần; tuyệt đối loại bỏ write scopes/routes khỏi connector. |
| Funds, bonds, FMarket and reference | Có catalogue nhóm fund/bond/FMarket và dữ liệu phụ trợ. | Cần rà từng schema; không suy ra mọi asset/dataset được cấp cùng quyền. |
| Live streaming/depth | Chưa xác định trong REST catalogue đã rà. | Cần tài liệu transport riêng, subscription limits, sequence, reconnect và gap recovery. |

## Quyền và vận hành cần xác minh

- Public docs chưa đủ để xác nhận free/paid plan, giá, quota, rate limits, history, market delay, local archive/backtest/derived-data rights hoặc export policy.
- Với từng dataset cần ghi rõ instrument IDs, venue/asset class, currency/units, timezone, corporate actions/adjustment, release time, correction/revision, pagination và mẫu payload được phép dùng.
- Account sync phải namespace riêng; đọc account/cash/positions/transactions/order history không được tạo/chỉnh/hủy order và không thay đổi local fund.
- Phải đánh giá token scopes tối thiểu. Không dùng `orders-write`, `accounts-write` hay scope write khác; không lưu token ở browser. Nếu OAuth implicit là flow duy nhất và không phù hợp native app an toàn thì capability ở trạng thái chưa triển khai.
- Yêu cầu vendor xác nhận đăng ký developer, approval, redirect URI, OAuth client type, revocation, session expiry, sandbox và support contact.

## Hướng tích hợp

Đầu tiên lưu bản OpenAPI spec/version và dựng inventory theo endpoint×dataset×scope. Chỉ sau khi quyền/gói và auth flow phù hợp được xác nhận mới tách từng P-task riêng cho catalogue, data history, live data và account reads. Trạng thái ban đầu: **có tài liệu API; cần xác minh gói/quyền và OAuth flow**. Không gửi lệnh broker qua FireAnt.

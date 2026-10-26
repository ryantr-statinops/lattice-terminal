# VNDIRECT: DChart, DataFeed và Open API

**Rà soát:** 26/10/2026  
**Kết luận:** tách ba nguồn/chương trình khác nhau. DChart UDF đang được repository gọi trực tiếp nhưng chưa tìm thấy hợp đồng API công khai xác nhận quyền sử dụng; DataFeed chính thức đang thông báo tạm dừng cung cấp; Open API được VNDIRECT mô tả cho khách hàng tổ chức/đối tác nhưng tài liệu kỹ thuật và quyền truy cập phải làm rõ trực tiếp. Không coi nguồn DChart hiện tại là production-ready.

## Nguồn và trạng thái bằng chứng

| Nguồn | Điều tài liệu chính thức xác nhận | Trạng thái |
|---|---|---|
| DChart | Trang DStock có trang trợ giúp “DChart - API”, chart theo mã; không công bố ở trang đó schema, endpoint contractual, quota, đăng ký hoặc quyền lưu/tái sử dụng. | Có dấu hiệu sản phẩm chart; API access/rights chưa được xác minh. |
| DataFeed | Trang DataFeed hiện thông báo VNDIRECT tạm dừng cung cấp gói Datafeed. | Chưa thể đăng ký gói qua luồng công khai hiện tại; hỏi VNDIRECT xem còn kênh hợp đồng khác không. |
| Open API tổ chức | Trang dịch vụ tổ chức đề cập khách hàng/đối tác kết nối Open API với hệ thống dữ liệu giao dịch và ngân hàng lưu ký; yêu cầu liên hệ bộ phận khách hàng tổ chức và thị trường nước ngoài. | Ứng viên theo hợp đồng; cần onboarding, tài liệu, quyền và báo giá. Trang giới thiệu không đủ để khẳng định endpoint market-data hay broker read-only cụ thể. |

Nguồn chính thức: [DStock DChart API](https://dstock.vndirect.com.vn/tong-quan/API/stock-chart-popup), [trang DataFeed](https://datafeed.vndirect.com.vn/), [dịch vụ chứng khoán cho tổ chức](https://www.vndirect.com.vn/hieu-ve-vndirect/dich-vu-to-chuc/dich-vu-chung-khoan/). Trang dịch vụ tổ chức dẫn đến một chương trình thương mại; không suy ra khả năng giao dịch hoặc quyền dùng dữ liệu cho ứng dụng cá nhân.

## Dấu vết trong repository (không phải đặc tả chính thức)

`VndirectCommunityProvider` trong `services/engine/kestrel_engine/providers.py` gọi `https://dchart-api.vndirect.com.vn/dchart/history`, gửi TradingView UDF query `resolution`, `symbol`, `from`, `to`, rồi đọc các mảng `t/o/h/l/c/v`. Code hiện chỉ ánh xạ `1m` sang resolution `1` và mọi interval còn lại thành `D`; symbol được ghép `VN:{symbol}`. Mã cũng mô tả các venue HOSE/HNX/UPCOM. Đây là quan sát từ adapter hiện hữu, không xác minh được trên tài liệu chính thức về tính ổn định, quyền truy cập, quyền lưu, quyền backtest hay phân phối.

TCBS adapter hiện gọi lại VNDIRECT cho candles và instruments trong fallback nội bộ. Vì vậy dữ liệu trả về cần provenance VNDIRECT rõ ràng, không được ghi nhận là TCBS. Bỏ fallback ẩn là việc riêng ở F03.

| Dataset | Hiện trạng bằng chứng | Điều còn thiếu để triển khai |
|---|---|---|
| Mã/catal​ogue instrument | Code có phương thức `fetch_instruments`; trang DChart công khai không phải catalogue API. | Endpoint, universe, ID ổn định, alias/venue, delisting và quyền lưu. |
| OHLCV ngày | Được adapter yêu cầu bằng UDF `D`; tài liệu DStock xác nhận chart nhưng không xác nhận API contract. | Lịch sử sâu đến đâu, adjusted/raw, corporate actions, timezone, đơn vị, revision, pagination, quota và rights. |
| OHLCV 1 phút | Được adapter yêu cầu bằng UDF `1`. | Coverage/retention, semantics timestamp/bar, market session, giới hạn request và rights. |
| Trade, quote, depth, live stream | Chưa thấy bằng chứng chính thức trong tài liệu công khai đã rà soát; adapter repository không triển khai các loại này. | Hỏi API/đối tác về từng dataset và transport; không suy luận từ DChart. |
| Corporate action / fundamentals / financial statements | Chưa được xác minh qua DChart docs. | Endpoint riêng, announcement timestamp, revision, units và rights. |
| Broker account read-only | Trang Open API tổ chức nói tới tích hợp hệ thống dữ liệu giao dịch nhưng không liệt kê public account endpoints. | Xác nhận riêng account list, cash, positions, transactions, order/fill history, auth/OTP/IP và quyền read-only. |
| Asset classes | Trang trợ giúp chart theo mã không đủ chứng cứ để xác nhận catalogue asset classes. | Xin catalogue chính thức theo equities, covered warrants, derivatives, bonds/funds và các dataset tham chiếu. |

## Đăng ký, vận hành và quyền sử dụng

- DChart: không tìm thấy public API-version/changelog, quy trình cấp credential, quota, giới hạn subscription, sequence/reconnect hay chính sách sửa đổi dữ liệu. Endpoint công khai truy cập được không chứng minh quyền dùng trong app, archive local hoặc backtest.
- DataFeed: dịch vụ đang tạm dừng theo trang chính thức; giá, SLA, lịch sử, feed và retention do đó chưa thể xác nhận.
- Open API tổ chức: liên hệ đúng bộ phận được liệt kê ở trang chính thức để xin bộ tài liệu và đề xuất thương mại. Cần xác nhận API nào là market data, API nào là account, điều khoản hiển thị/lưu/dẫn xuất/backtest, phí, quota, IP allowlist, phương thức xác thực, expiry/refresh/OTP và mẫu payload được phép.
- Chưa có mẫu payload được phép sử dụng để kiểm chứng parser. Không lưu dữ liệu thu được từ endpoint DChart vào fixture/archive cho đến khi rights được xác nhận.
- Không có bằng chứng công khai đủ để kết luận lịch sử, timezone, đơn vị giá/khối lượng, adjusted price, corporate action, correction/revision, thời điểm công bố, phân trang hoặc khôi phục gap.

## Quyết định đưa vào kế hoạch

Đăng ký VNDIRECT DChart như **nguồn cộng đồng chưa có quyền/cam kết API được xác minh**, không dùng để đánh dấu capability production. DataFeed công khai ở trạng thái **chờ nhà cung cấp mở lại hoặc báo kênh hợp đồng**. Open API tổ chức ở trạng thái **chờ onboarding/tài liệu/quyền**. Chỉ tạo `P-vndirect-*` cho capability cụ thể sau khi có endpoint inventory và rights; mỗi dataset/operation vẫn là commit riêng. Nếu không có API/rights phù hợp, ghi lý do chưa thể triển khai và không tự động dùng endpoint community.

# Ứng viên provider Việt Nam ngoài danh sách chính

**Rà soát:** 26/10/2026. Mục tiêu là sàng lọc nguồn API chính thức có bằng chứng, không biến việc tìm thấy website/API thành quyền truy cập production.

## Ứng viên có tài liệu/website chính thức để tiếp tục khảo sát

| Ứng viên | Bằng chứng chính thức | Khả năng đáng khảo sát | Trạng thái / việc cần xác minh |
|---|---|---|---|
| WiGroup WiFeed | [WiFeed](https://wigroup.vn/san-pham/wifeed) công bố API truyền tải dữ liệu tài chính, API key, dịch vụ cho trading board/app, dashboard, data lake/warehouse và commercial software. | Data feed tài chính; catalogue cần rà từng asset/dataset và mode delivery. | Chưa có inventory endpoint/fields/venue, history/live semantics, quota, pricing hoặc direitos lưu/backtest; liên hệ vendor lấy API docs và gói phù hợp local-only. |
| FiinGroup API Datafeed | [Trang API Data Service](https://dff.fiingroup.vn/ApiDataFeed?lang=vi-vn) công bố price feed, corporate reference, financials, corporate actions, ratio, sector indices, macro và bonds. | Bổ sung nguồn commercial có catalogue rộng; cùng vendor với hồ sơ FiinGroup, không tính là vendor khác. | Đã có hồ sơ riêng; lấy tài liệu contractual để biến mô tả capability thành dataset/endpoint. |
| Vietstock Finance/DataFeed | [Vietstock DataFeed](https://en.vietstock.vn/2021/10/vietstock-datafeed-intergrated-economic-and-financial-data-for-vietnam-36-458082.htm) công bố delivery qua API hoặc Sync Data. | Datafeed/financial data nội địa, có nhiều danh mục portal. | Bài giới thiệu cũ; xác nhận gói, API và coverage hiện hành theo hồ sơ Vietstock riêng. |
| FireAnt REST v1 | [OpenAPI portal](https://api.fireant.vn/) công bố spec, OAuth2 và scopes. | Có thể đọc market/company/finance và account nếu rights cho phép. | OAuth public docs là Implicit Grant; suitability native app, rights, plans và scope tối thiểu cần xác nhận theo hồ sơ riêng. |

SSI, DNSE, TCBS và VPBankS đã có hồ sơ provider riêng. VNDIRECT Open API là kênh tổ chức chờ onboarding. Không đưa API community/không tài liệu thành ứng viên đã xác minh.

## Đối chiếu nhu cầu sản phẩm

- Broker được đánh giá chỉ cho market data và account snapshots read-only. Không yêu cầu `orders-write` vì sản phẩm hiện chỉ backtest/paper và thông báo tín hiệu.
- Datafeed thương mại có thể bao phủ nhiều loại tài sản hơn broker APIs; inventory phải ghi toàn bộ catalogue, không giới hạn equity. Từng dataset được cấp quyền và normalized độc lập.
- Dataset macro, NAV, bond yield, statements, corporate actions và ratios là typed series/records; chúng không thuộc candle schema.
- Local-only deployment không tự cấp quyền lưu dữ liệu. Cần hỏi cụ thể local persistence, historical backtest, derived data, backup, export và single-user application rights.

## Bằng chứng chưa đủ / loại khỏi danh sách hiện tại

Search results có thể nhắc đến API của broker khác hoặc community libraries, nhưng trong lượt rà soát này chưa xác định được public official technical docs đủ để cam kết API. Không thêm VPS, MBS, HSC, BSC, KIS, Mirae, VCBS, VCI hay các bên khác vào danh sách tích hợp đã chọn nếu thiếu evidence về endpoint chính thức và rights. Có thể bổ sung nếu vendor cấp docs/private onboarding; cần phân biệt tài liệu vendor với SDK bên thứ ba.

## Câu hỏi vendor để tiếp tục

Xin bộ docs và sample payload được phép; catalogue dataset/asset class/venue; IDs và lifecycle; lịch sử/latency/timezone/units; adjusted/raw, corporate actions, revision/release time; live protocols, quota/subscription/reconnect/gap recovery; API key/token expiry/refresh/IP; giá/SLA; quyền local display/storage/backtest/derived/export; sandbox và contact hỗ trợ. Ghi rõ từng mục đã tài liệu xác nhận, phụ thuộc account, phụ thuộc contract hoặc chưa có bằng chứng.

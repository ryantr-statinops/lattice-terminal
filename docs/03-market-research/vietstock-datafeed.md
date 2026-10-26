# Vietstock DataFeed

**Rà soát:** 26/10/2026. **Trạng thái:** vendor công bố dịch vụ API hoặc đồng bộ dữ liệu, nhưng trang công khai được tìm thấy chưa cung cấp schema, coverage contractual, điều khoản lưu/backtest hay giá hiện hành. Cần xác nhận với nhà cung cấp trước khi triển khai.

## Sản phẩm và phạm vi có bằng chứng

Bài giới thiệu [Vietstock DataFeed](https://en.vietstock.vn/2021/10/vietstock-datafeed-intergrated-economic-and-financial-data-for-vietnam-36-458082.htm) mô tả dịch vụ đưa dữ liệu kinh tế và tài chính vào ứng dụng/nền tảng thông qua **API hoặc Sync Data**. Bài có liên kết tới trang coverage và dịch vụ, nhưng là bài giới thiệu năm 2021; không đủ để xác nhận danh mục hoặc giá hiện hành.

Danh mục nội dung VietstockFinance công khai bao gồm thông tin thị trường, thống kê giao dịch, sentiment, chỉ số ngành, dữ liệu doanh nghiệp/sự kiện, báo cáo tài chính, nội bộ/cổ đông, futures, covered warrant, ETF, macro-economics và bonds. Đây là catalogue sản phẩm nội dung; không khẳng định mọi mục đều có trong DataFeed/API.

| Dataset cần khảo sát riêng | Bằng chứng công khai | Câu hỏi cần làm rõ |
|---|---|---|
| EOD/intraday, trade, quote/depth | Trang có mục thị trường và thống kê giao dịch, không có schema/API contract công khai. | Board/venue, interval/history, live vs delayed, depth, quota, transport và backfill. |
| Instrument/catalogue | Nội dung chứng khoán/công cụ trên VietstockFinance. | Stable ID, aliases, venue, delisting, asset classes/API endpoint. |
| Financial statements, corporate events | Menu công khai có báo cáo tài chính, sự kiện, cổ đông/nội bộ. | Periods, announcement time, restatement/revision, units/currency, corporate actions. |
| Futures, covered warrants, ETF, bonds | Các danh mục riêng có trên portal. | Chính xác dataset, contract/security IDs, expiry, valuation fields và lịch sử. |
| Macro/economic | Vietstock nêu nội dung macro và kinh tế. | Series catalogue, cadence, units, release time/revisions, country coverage. |
| Sync delivery | Bài DataFeed công bố API hoặc Sync Data. | File format, transport/schedule, checkpoints, retention, correction and recovery. |

## Quyền, đăng ký và vận hành

- Coverage hiện hành, gói/giá, SLA, sandbox, auth/token, giới hạn request, pagination và IP allowlist cần hỏi nhà cung cấp. Không có giá công khai đủ để trích dẫn.
- Xác minh rõ quyền dùng local, hiển thị trong ứng dụng, archive, backtest, dữ liệu dẫn xuất và export; bài giới thiệu không cấp các quyền này.
- Yêu cầu sample payload được phép sử dụng cho từng endpoint, có timezone, currency, price/volume units và quy tắc adjusted/raw.
- Chưa có bằng chứng public về streaming, sequence, reconnect, subscription limits, data corrections hoặc corporate action adjustment policy.
- Không thấy public broker account API trong nguồn DataFeed đã khảo sát; account sync read-only là capability riêng cần bằng chứng riêng.

## Hướng xử lý

Xem Vietstock là ứng viên **chờ vendor xác nhận catalogue/API và báo giá**. Mỗi dataset trong catalogue được xác minh sau này sẽ có trạng thái riêng: đủ thông tin, chờ account, chờ quyền/gói, hoặc không có API phù hợp. Không gọi endpoint không được công bố, không lưu dữ liệu thử nếu chưa xác nhận rights. Tài liệu API/DataFeed hiện tại chưa đủ để tạo adapter production.

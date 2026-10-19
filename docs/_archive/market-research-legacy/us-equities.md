# Cổ phiếu Mỹ — hướng mở rộng

**Khảo sát:** 2026-10-16; chưa feed test, chưa quyền public redisplay; ngoài MVP.

## Nguồn và khả năng

[SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) cung cấp submissions/XBRL cho công bố doanh nghiệp. Dùng CIK và mapping ticker có thời hạn; submission/filing timestamp là evidence sự kiện, không đồng nhất với thời điểm hệ thống tải được. Phải tuân fair access và identity theo SEC; XBRL facts sau sửa không phải bản point-in-time mặc định.

[Alpaca market data](https://docs.alpaca.markets/us/docs/about-market-data-api) phân biệt IEX và SIP; free/basic không đại diện quyền truy cập consolidated real-time đầy đủ. Phải xác minh plan hiện hành, vùng tài khoản, history window, quota và entitlement trước khi chọn. Không dùng volume một venue làm total market volume.

[Alpaca historical news](https://docs.alpaca.markets/us/docs/historical-news-data) là ứng viên news qua API; quyền dùng cá nhân/API không đồng nghĩa quyền hiển thị cho mọi account trên public website. Giá, news và redistribution có thể theo điều khoản khác nhau; trial hoặc quota free không phải production license.

News bổ sung là issuer investor-relations releases và SEC press releases, source-by-source. Chưa chốt commercial news vendor, không giả định free historical full text.

## Provider matrix — evidence tại ngày khảo sát

| Provider / product | Access và dữ liệu | Giới hạn được documentation nêu | Rights còn mở |
|---|---|---|---|
| [SEC EDGAR](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) | Public/free filings, indexes, submissions/XBRL | Tối đa 10 requests/giây; khai báo User-Agent; moderate load | Attachments/derived processing, attribution và mục đích display cần policy |
| [Alpaca Basic equities](https://docs.alpaca.markets/us/docs/about-market-data-api) | Account-gated, free Trading API plan; real-time IEX | 30 WebSocket symbols, historical từ 2016, 200 historical calls/phút; SIP gần nhất bị giới hạn 15 phút | Personal entitlement không cấp quyền multi-user redisplay |
| [Alpaca paid equities](https://docs.alpaca.markets/us/docs/about-market-data-api) | Paid plan; coverage rộng hơn Basic | Pricing/entitlement cần review tại lúc mua; không mặc định Basic đủ consolidated intraday | Commercial/Broker use cần agreement phù hợp |
| [Alpaca news](https://docs.alpaca.markets/us/docs/historical-news-data) | API news candidate, account/vendor terms | Chưa access-test history/retention/quota | Store, ML, excerpts và public display chưa confirmed |
| Issuer IR | Public releases theo từng doanh nghiệp | Interface/timestamp/archive không đồng đều | Không blanket approval cho mọi issuer |

Các con số trên là documentation evidence 2026-10-16, không SLA hoặc cấu hình production đã test. Delayed SIP và live IEX phải có feed labels riêng; không trộn chúng thành consolidated real-time. SEC corrections/deletions có thể làm archive hiện tại khác lịch sử quan sát; lưu first_seen/version.

## Features và giới hạn nghiên cứu

Filings/events, earnings timing, fundamentals đã công bố, price/volume reaction và volatility. Phải xử lý split/dividend, delisted symbols, ticker changes, exchange calendar/DST và adjusted/unadjusted prices. Earnings surprise cần consensus tại thời điểm đó; không tự có từ SEC.

Đánh giá event windows không được dùng filing revisions hoặc financial restatements trước lúc công bố. Universe lịch sử tránh survivorship. Intraday và daily cần separate coverage/latency reports.

## Quyết định/gate

Giữ làm ứng viên sau crypto, đặc biệt nếu sản phẩm chuyển trọng tâm company-event research. Cần chốt broker/provider quyền price+news, corporate-action dataset, historical universe và point-in-time fundamentals trước roadmap thực thi. Chi phí chưa có báo giá/quota đo thật; store/train/display đều chưa confirmed trong [register](source-register.md).

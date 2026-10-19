# FX — hướng nghiên cứu vĩ mô

**Khảo sát:** 2026-10-16; documentation-only, ngoài MVP.

## Giá và nguồn vĩ mô

[OANDA pricing API](https://developer.oanda.com/rest-live-v20/pricing-ep/) là ứng viên account/token-gated; feed broker-specific. Cần test quyền tài khoản/vùng, candles bid/ask/mid, historical range và quota theo endpoint. Không có consolidated FX tape miễn phí được xác nhận trong khảo sát này.

[ECB reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html) là dữ liệu tham chiếu daily; không thay executable quotes hoặc intraday broker price. [Fed RSS](https://www.federalreserve.gov/feeds/feeds.htm), [ECB RSS](https://www.ecb.europa.eu/home/html/rss.en.html), [BLS API](https://www.bls.gov/bls/api_features.htm), [BEA API](https://apps.bea.gov/api/) là ứng viên announcements và actual macro releases. Phải kiểm tra quyền nguồn trực tiếp, revisions/vintage và thời gian release. Chưa xác nhận consensus forecast history miễn phí; không tạo surprise bằng latest revised actual trừ consensus giả định.

## Provider matrix và dữ liệu bổ sung

| Provider | Access/capability | Giới hạn và rights còn mở |
|---|---|---|
| [OANDA](https://developer.oanda.com/rest-live-v20/pricing-ep/) | Account/token-gated broker prices | Live/demo entitlement, intraday history, quotas/store/train/redisplay cần test |
| [Dukascopy Historical Export](https://www.dukascopy.com/swiss/english/marketwatch/historical/) | Công cụ export miễn phí; docs nêu CSV, tick đến monthly | Chưa test export; không suy ra automated API/public redistribution license; venue-specific |
| [ECB reference rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html) | Public daily reference | Không dùng thay bid/ask thực thi; rights review riêng |
| [Fed](https://www.federalreserve.gov/feeds/feeds.htm), [ECB](https://www.ecb.europa.eu/home/html/rss.en.html) | RSS policy/news | Metadata/full text/ML chưa approved; thiếu consensus |
| [BLS](https://www.bls.gov/bls/api_features.htm), [BEA](https://apps.bea.gov/api/) | Macro actual APIs; registration/quota tùy interface | Revision/vintage coverage và source terms phải review |
| [CFTC COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) | Public futures positioning reports | Thường công bố thứ Sáu 15:30 ET cho vị thế thứ Ba; ngày lễ có thể đổi lịch |
| [FRED](https://fred.stlouisfed.org/legal/) | Public aggregation/API key | Không eligible ML/cache hiện tại; xem gate dưới |

COT là futures positioning, không trực tiếp đo spot FX order flow. Feature chỉ available sau release; không join vào thứ Ba theo position date. Intraday không được forward-look ba ngày công bố; giữ release calendar/timezone/DST evidence. Dukascopy là candidate lịch sử, không thay OANDA quote khi backfill cùng series.

## FRED restrictions

[FRED legal terms](https://fred.stlouisfed.org/legal/) tại ngày khảo sát nêu hạn chế sử dụng services/content trong phát triển hoặc training ML/AI; API terms còn nêu hạn chế lưu/cache/archive. Vì vậy FRED **không eligible** cho training hoặc dataset cache theo thiết kế hiện tại khi chưa có quyền thích hợp. Không suy ra public-domain label của series xóa các điều khoản dịch vụ. Nguồn gốc trực tiếp BLS/BEA/Fed là ứng viên cần review riêng, không phải cách tự động né điều khoản.

## Features và evaluation

Returns, volatility, spread, trading-session/calendar features; release type và actual/vintage khi đủ evidence. Macro actual, revision và consensus phải là trường riêng. Chuẩn hóa UTC nhưng giữ source timezone/DST; xử lý weekend, rollover và bid/ask costs. News tại ngày kinh tế không có precise time phải bị loại khỏi intraday feature hoặc dùng availability bảo thủ.

## Gate mở rộng

Chọn một broker venue, cặp nhỏ và calendar; xác minh store/train/redisplay; lấy dữ liệu revision-aware. Không chốt OANDA là miễn phí production hoặc hứa lịch sử tick. Chi phí/quota hiện chưa đo. FX phù hợp macro-event study nhưng point-in-time releases và transaction cost quan trọng hơn việc có nhiều indicator.

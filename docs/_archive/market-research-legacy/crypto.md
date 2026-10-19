# Crypto — thị trường đầu tiên

**Khảo sát:** 2026-10-16, documentation-only. This is a historical review of the previous Binance prototype direction, not current product scope. SSI FastConnect Data for Vietnam is the selected first-market direction; see [current SSI research](vn-equities.md). No feed test or source approval is implied here.

## Giá và lịch sử

[Binance market-data-only](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) mô tả REST public và WebSocket public không cần API key. Browser stream là giá hiển thị theo tab; lịch sử nghiên cứu do ingestion lấy từ bulk/REST. Không cần tài khoản trading trong thiết kế này; accessibility ở browser/runner và vùng triển khai còn phải test.

[Binance archive](https://github.com/binance/binance-public-data) có daily/monthly archives, checksum và ghi nhận các lần sửa. Phải giữ file hash/version; không coi archive hiện tại là dữ liệu người nghiên cứu đã có tại thời điểm lịch sử. Điểm quan trọng: Spot archive từ 2025-01-01 sử dụng microseconds; adapter phải khai báo đơn vị và chuẩn hóa, không đoán từ tên file. [Dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md) phải được review riêng; chữ MIT ở repository không tự cấp quyền mọi cách khai thác dữ liệu.

[Kraken OHLCVT archive](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data) là ứng viên đối chiếu/venue sau. Không nối nến Kraken vào Binance để vá lỗ. Quyền store/train/public redisplay chưa xác nhận. Archive không tự chứng minh tính đầy đủ tại mọi interval/ngày cần dùng.

## Provider matrix và giới hạn đã biết

| Provider | Capability / mô hình access | Giới hạn, quyền và bước xác minh |
|---|---|---|
| [Binance public API](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) | Public REST/WS không key; giá và nến | Quota/region/CSP cần access test; quyền API/live review riêng |
| [Binance Vision](https://github.com/binance/binance-public-data) | Bulk daily/monthly miễn phí theo terms | Chỉ use case đủ điều kiện; revision/hash và timestamp-unit checks |
| [Kraken](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data) | Public historical OHLCVT | Venue khác; historical coverage, store/ML/display chưa xác nhận |
| [SEC](https://www.sec.gov/newsroom/press-releases), [CFTC](https://www.cftc.gov/RSS/index.htm) | Regulator news công khai | Tin chọn lọc pháp lý, không broad market feed; approval theo fields |
| [Ethereum](https://blog.ethereum.org/), [Bitcoin Core](https://bitcoincore.org/en/releases/) | Project announcements công khai | Không trung lập/toàn thị trường; rights/ML review từng nguồn |
| [CoinDesk candidate](https://www.coindesk.com/arc/outboundfeeds/rss/) | RSS báo chí chưa xác minh được | Browsing lỗi; chưa kết luận free/paid, history hay quyền |

### Dataset terms ảnh hưởng scope

[Binance Vision terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md), version 1.0 ngày 2026-08-26, áp dụng CC BY-NC-SA 4.0 kèm điều khoản bổ sung. Use case được nêu gồm nghiên cứu học thuật, giáo dục mở không kiếm tiền và backtest cá nhân ngoài production. Dùng thương mại cần thỏa thuận riêng; live proprietary execution, signal có đền bù và khai thác feed thương mại bị hạn chế. Derivative work chịu attribution/share-alike theo terms.

Vì vậy không mặc định archive hỗ trợ multi-account retail terminal hoặc public demo. P03 phải đánh giá đúng mục đích/khán giả và artifacts trước approval; nếu không phù hợp, dùng synthetic fixtures trong demo hoặc chọn licensed source qua ADR. Terms archive không tự quyết định quyền REST/live.

## News candidates

Nguồn hẹp, xác định được xuất xứ trước: [SEC press releases](https://www.sec.gov/newsroom/press-releases), [CFTC RSS](https://www.cftc.gov/RSS/index.htm), [Ethereum blog](https://blog.ethereum.org/) và [Bitcoin Core releases](https://bitcoincore.org/en/releases/). Regulator mạnh về pháp lý, project mạnh về nâng cấp/release; chúng không phủ đầy đủ thị trường hoặc tin breaking.

[CoinDesk RSS candidate](https://www.coindesk.com/arc/outboundfeeds/rss/) là ứng viên báo tài chính crypto; browsing URL trả lỗi trong lần khảo sát này nên chưa đánh dấu documented hoặc xác nhận feed còn hoạt động. Chưa test retention/quyền. Không coi RSS là quyền crawl toàn văn, dịch/tóm tắt bằng model hay phân phối lại. Chỉ ingest fields được source policy cho phép sau approval; link gốc và attribution là bắt buộc khi policy yêu cầu. MVP chưa có nguồn news tổng hợp production được duyệt.

## Feature và nghiên cứu

Price-only: lagged returns, rolling volatility, momentum, volume anomaly; spread chỉ khi có quote history phù hợp. News: count, novelty, asset/event mapping theo available_at. Funding/OI thuộc derivatives, deferred và không gắn vào spot series như cùng một instrument.

Chạy intraday và multi-day/weekly thành hai protocol; holdout theo thời gian, fees/slippage explicit, long/cash. Tin backfill có published_at cũ không đủ để chạy historical news backtest. News-only/combined chỉ được đánh giá với availability evidence và quyền ML hợp lệ.

## Gate trước triển khai

- Kiểm thử BTC/ETH, từng timeframe, archive checksum, timestamp transition, REST pagination và browser region/CSP.
- Ghi giới hạn rate/connection hiện hành từ docs trong cấu hình/version evidence; không hardcode từ trí nhớ.
- Review điều khoản dataset/API và từng news provider cho store/train/public display.
- Đo gaps, duplicates, closed bars, freshness và retention; khóa coverage thực tế trước khi công bố.

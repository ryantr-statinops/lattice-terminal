# Market data — Binance Spot trước

**Trạng thái:** nghiệp vụ ingestion/live lifecycle vẫn là thiết kế mục tiêu; chưa source-approved hoặc triển khai feed vào app. Tài liệu trước đây ghi P02 đã thử 6 REST requests và một BTC trade stream, nhưng evidence paths được tham chiếu hiện không có trong checkout; xem [source register](../03-market-research/source-register.md). Coi các access-test claims đó là lịch sử/chưa audit được, không dùng làm bằng chứng cấp quyền hay production readiness.

1. [Historical ingestion và normalization](historical-ingestion.md)
2. [Browser live lifecycle](browser-live-lifecycle.md)

Scope: Binance Spot BTCUSDT/ETHUSDT, 15m/1h/1d. [Nguồn](../03-market-research/crypto.md), [data contracts](../04-data/data-model.md), [ADRs](../02-architecture/decisions.md).

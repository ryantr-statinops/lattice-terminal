# Research Terminal — documentation

**Trạng thái:** product direction đã cập nhật ngày 2026-10-18 theo quyết định local-first. Đây là mục tiêu, không mô tả trạng thái implementation: code hiện tại vẫn là prototype synthetic fixture React/Vite, Go Gateway, FastAPI và CLI. SSI, password login, local persistence, backtest và paper trading chưa triển khai.

## Bắt đầu

1. [Glossary](glossary.md), [vision và scope](01-product/vision-and-scope.md), [quy tắc sản phẩm](01-product/project-rules.md).
2. [Kiến trúc và ADR](02-architecture/README.md).
3. [Nghiên cứu nguồn thị trường](03-market-research/README.md), đặc biệt [SSI FastConnect Data](03-market-research/vn-equities.md) và [source register](03-market-research/source-register.md).
4. [Dữ liệu](04-data/README.md), [news engine](05-news-ingestion/README.md), [market data](06-market-data/README.md).
5. [Portfolio](07-portfolio/README.md), [Model Lab](08-model-lab/README.md), [API/local service contracts](09-api/README.md).
6. [UI/UX](10-ui-ux/README.md), [engineering](11-engineering/README.md), [operations](12-operations/README.md).
7. [Roadmap hiện hành](../task/next-plan.md).

## Nguồn sự thật

Product scope ở `01-product` và status/sequence ở `task/next-plan.md` sở hữu quyết định mới. Domain docs ghi contract chi tiết; nơi nào còn Binance, USDT, managed auth hoặc hosted architecture thì đó là prototype/legacy proposal cho đến khi được cập nhật và không override local-first direction. Cập nhật domain owner và consumer cùng lúc khi contract đổi.

## Hướng sản phẩm đã chốt

Mã nguồn mở, miễn phí, người dùng Việt Nam clone repo và chạy local trên Windows/localhost; mọi config, credentials, data và portfolio ở máy người dùng. Market data mục tiêu là SSI FastConnect Data, tận dụng các REST/reference/stream capabilities phù hợp sau khi xác nhận entitlement và điều kiện dùng. News engine do dự án tự xây riêng rồi tích hợp sau. Portfolio MVP gồm backtesting và paper live trading, không gửi lệnh thật. Model Lab deferred.

## Cách đọc bằng chứng

`documented`, `access-tested`, `rights-confirmed` và `approved` là trạng thái riêng. Chỉ tài liệu official chứng minh capability được công bố; không chứng minh tài khoản của người dùng có entitlement, quyền lưu trữ/display, quota hoặc giá cụ thể. Chưa có secret/SSI account được cung cấp hoặc access test; không dùng network/live data trước khi source gate đạt.

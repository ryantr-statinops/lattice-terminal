# Research Terminal — Documentation Hub

**Định hướng:** công cụ nghiên cứu local-first cho thị trường Việt Nam. SSI FastConnect Data là provider direction, nhưng source gate hiện chưa mở; prototype hiện tại chủ yếu dùng fixtures/mocks. Tài liệu này là bản đồ docs, không thay thế trạng thái code hoặc evidence nguồn.

## Cách đọc tài liệu

1. Bắt đầu từ [Vision và phạm vi](01-product/vision-and-scope.md), [Quy tắc sản phẩm](01-product/project-rules.md) và [Constraints](CONSTRAINTS.md) để hiểu mục tiêu, ranh giới và nguyên tắc.
2. Xem [Architecture](02-architecture/README.md) và [API](09-api/README.md) để phân biệt kiến trúc mục tiêu với scaffold hiện tại.
3. Với market data, đọc [source register](03-market-research/source-register.md), [SSI research](03-market-research/vn-equities.md) và [contracts](06-market-data/README.md). Default là fixture-only; production đang blocked. Access probe cần authorization riêng theo source register và không cấp quyền lưu/serve payload.
4. Với portfolio simulation, xem [Portfolio](07-portfolio/README.md); backtest và paper trading là mục tiêu V1, chưa phải năng lực đã triển khai.
5. [News engine](05-news-ingestion/README.md) là workstream độc lập cho nguồn quốc tế và Việt Nam; chưa tích hợp vào terminal.
6. [UI/UX](10-ui-ux/README.md), [Engineering](11-engineering/README.md) và [Operations](12-operations/README.md) mô tả mục tiêu, prototype và yêu cầu phát hành.

## Bản đồ thư mục

| Thư mục | Nội dung |
|---|---|
| `01-product/` | Vision, scope, journeys, routes, quy tắc và metrics |
| `02-architecture/` | ADR, hệ thống, frontend, stack và cấu trúc repository |
| `03-market-research/` | Nghiên cứu thị trường/nguồn và source approval gates |
| `04-data/` | Data model, quality, lifecycle, storage và retention |
| `05-news-ingestion/` | Thiết kế workstream news độc lập và contract tích hợp tương lai |
| `06-market-data/` | SSI adapter, lịch sử và lifecycle streaming |
| `07-portfolio/` | Sổ cái, quy tắc thị trường và mô phỏng |
| `08-model-lab/` | Tài liệu mô hình được hoãn ngoài MVP đầu tiên |
| `09-api/` | API scaffold hiện tại và hướng contract local |
| `10-ui-ux/` | UI flows, lifecycle, tokens và inventory prototype |
| `11-engineering/` | Workflow, security, testing và đánh giá prototype |
| `12-operations/` | Local setup, quota, recovery và release gates |
| `_archive/` | Tài liệu lịch sử không phải yêu cầu hiện hành |

## Nguồn sự thật và trạng thái

- Product scope: [vision](01-product/vision-and-scope.md) và [project rules](01-product/project-rules.md).
- SSI gate: [source register](03-market-research/source-register.md); `documented`, `access-tested`, `rights-confirmed`, `approved` là các evidence flag độc lập.
- Quyết định kỹ thuật: [ADR](02-architecture/decisions.md); mục còn proposal/pending không phải quyết định đã chốt.
- Roadmap: [task/next-plan.md](../task/next-plan.md).

Mỗi tài liệu cần phân biệt rõ **đã quyết định**, **mục tiêu**, **prototype hiện tại**, và **chưa xác minh/chưa triển khai**. Khi tài liệu mô tả thiết kế cũ, phải ghi trạng thái historical/deferred và không dùng làm yêu cầu V1.

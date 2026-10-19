# Market data — SSI FastConnect Data

**Trạng thái:** SSI FastConnect Data là provider direction cho local-first V1. Official docs đã được xem xét; account entitlement/access, rights, schema mapping và production integration chưa được xác nhận/triển khai. Không gọi SSI hoặc persist payload thật khi source gate còn blocked.

V1 target đánh giá REST historical/reference và streaming feeds phù hợp với research + paper simulation. Khi được triển khai, SSI access/credentials thuộc local process và UI gọi local API. Historical data và stream cần reconciliation; stream không thay thế lịch sử. Đây là target architecture, chưa phải implementation.

1. [SSI FastConnect Data adapter technical contract](ssi-adapter-contract.md)
2. [SSI FastConnect Data scope, source gate and required contracts](../03-market-research/vn-equities.md)
3. [Dữ liệu lịch sử thị trường (Historical Ingestion)](historical-ingestion.md)
4. [SSI local stream lifecycle target](browser-live-lifecycle.md)

Scope instrument classes, markets, intervals, field retention and permission are still to be confirmed with the user's entitlement and reviewed terms. See [source register](../03-market-research/source-register.md), [data model](../04-data/data-model.md), and [architecture decisions](../02-architecture/decisions.md).

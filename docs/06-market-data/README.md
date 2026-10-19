# Market data — SSI FastConnect Data

**Trạng thái:** SSI FastConnect Data là provider direction cho local-first V1. Capability đã được review từ official docs; account entitlement/access, rights, schema mapping và production integration chưa được xác nhận/triển khai. Không gọi SSI hoặc persist real payload khi source gate còn blocked.

V1 target tận dụng REST historical/reference endpoints và streaming feeds phù hợp với research + paper trading. SSI access/credentials được giữ trong local process; UI gọi local API. Nguồn lịch sử và stream phải reconcile; stream không thay lịch sử.

1. [SSI FastConnect Data adapter technical contract](ssi-adapter-contract.md)
2. [SSI FastConnect Data scope, source gate and required contracts](../03-market-research/vn-equities.md)
3. [Dữ liệu lịch sử thị trường (Historical Ingestion)](historical-ingestion.md)
4. [SSI local stream lifecycle target](browser-live-lifecycle.md)

Scope instrument classes, markets, intervals, field retention and permission are still to be confirmed with the user's entitlement and reviewed terms. See [source register](../03-market-research/source-register.md), [data model](../04-data/data-model.md), and [architecture decisions](../02-architecture/decisions.md).

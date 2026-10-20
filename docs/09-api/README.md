# API contracts

**Tóm tắt:** UI chỉ gọi Go. Có kiểm tra drift cho routes/response DTO và internal OpenAPI, nhưng chưa có bộ request OpenAPI/SDK TypeScript sinh tự động đầy đủ.


Browser uses Go `/api/v1` and session/Host/Origin checks. Python `/internal/v1` is loopback bearer-authenticated. Browser proxy does not expose internal runner/finance endpoints.

- [Auth / HTTP](auth-and-http.md)
- [Frontend contract](frontend-data-contracts.md)
- [Capabilities](capabilities.md)
- [Generated routes](../../contracts/gateway-routes.json)
- [Gateway response DTO schemas](../../contracts/gateway.schema.json)
- [Internal OpenAPI](../../contracts/engine.openapi.json)
- [Market models](../../contracts/market.schema.json)

CI checks route/response/internal-schema drift. Go response schemas are not complete external request OpenAPI or generated TS clients. Semantic consumer review and tests remain necessary. Contracts do not approve unavailable sources/rules.

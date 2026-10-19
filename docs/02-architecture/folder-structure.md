# Repository — current scaffold and target boundary

**Reviewed 2026-10-19:** cây dưới đây ghi nhận code prototype hiện có. Có page/component, fixture HTTP services và local-file CLI; chưa có SSI integration, local auth/persistence production hoặc portfolio simulator. README ownership không thay thế bằng chứng implementation.

~~~text
apps/web/src/
  main.tsx                 Router, providers và frontend entry hiện tại
  app/                     Ownership README và layout test; router không nằm tại đây
  features/
    news/                  Fixture article cards và filter; chưa có engine
    market/                Fixture instruments/chart/watchlist và stream-status prototype
    portfolio/             Manual/CSV holdings, browser storage và fixture valuation
    model-lab/             Mock form/adapter; không có training runtime
    account/               Placeholder page; không có auth/profile implementation
  workers/                 Ownership README; chưa có worker runtime
  services/                Ownership README; actual API client ở lib/api.ts
  lib/                     API client, query config, theme và utilities
  components/              UI dùng chung
services/gateway/          Go HTTP ingress
services/api/              FastAPI fixture endpoints; chưa có local auth/SSI domains
services/ingestion/        Go fixture/local-file CLI và parser; chưa có source scheduler/network adapter
services/research/         Python dataset/evaluation tooling
packages/contracts/        OpenAPI, event và manifest contracts
data/fixtures/              Dữ liệu synthetic dùng dev/test
data/samples/               Mẫu nhỏ có source rights rõ ràng
experiments/                Spike độc lập, chưa tự động thành production
docs/                       Tài liệu chuẩn theo domain
task/next-plan.md          Roadmap và trạng thái phase
.github/workflows/          CI, test, lint và security checks
~~~

V1 target dùng local service cho SSI và simulator; giữ/tách/hợp nhất Go/Python processes vẫn pending ADR. Sự tồn tại của `workers/` không chọn runtime cho portfolio backtest; Model Lab ngoài MVP. Không có browser Python bundle/runtime manifest được triển khai. Raw dumps, private CSV, credentials và model binaries không commit Git.

Đối chiếu entrypoints, package manifests và code để xác định implementation; xem [frontend architecture](frontend-architecture.md), [API prototype contracts](../09-api/frontend-data-contracts.md) và [ADR](decisions.md). Không tạo package/toolchain chỉ để lấp cây thư mục mục tiêu.

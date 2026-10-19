# Repository mục tiêu
**Trạng thái:** cây thư mục mục tiêu đã được khởi tạo trong repo. Các `README.md` bên trong `apps/web/src/app`, `features`, `workers`, `services` và `data/samples` là placeholder mô tả ownership; hiện chưa có các nghiệp vụ đó. Runtime vẫn chủ yếu là UI/HTTP và CLI đọc fixture.

~~~text
apps/web/src/
  app/                     Router và khung ứng dụng
  features/
    news/                  News feed, lọc và sự kiện
    market/                VN Equities (HOSE, HNX, UPCOM), chart và watchlist
    portfolio/             Holdings, giao dịch và P&L
    model-lab/             Cấu hình và kết quả nghiên cứu
    account/               Workspace, đăng nhập và cài đặt
  workers/                 Web Worker cho training/backtest
  services/                API client và stream lifecycle
  components/              UI dùng chung
services/gateway/          Go HTTP ingress
services/api/              FastAPI auth/account/domain
services/ingestion/        Go scheduled source adapters
services/research/         Python dataset/evaluation tooling
packages/contracts/        OpenAPI, event và manifest contracts
data/fixtures/              Dữ liệu synthetic dùng dev/test
data/samples/               Mẫu nhỏ có source rights rõ ràng
experiments/                Spike độc lập, chưa tự động thành production
docs/                       Tài liệu chuẩn theo domain
task/next-plan.md          Roadmap và trạng thái phase
.github/workflows/          CI, test, lint và security checks
~~~

Thư mục worker thuộc web vì runtime browser, không tạo server worker queue cho training. Browser Python bundle/package assets được pin theo runtime manifest và deployment budget. Raw dumps, personal CSVs, credentials và binary model lớn không commit Git.

Các phase chỉ thêm code nghiệp vụ khi input contract và acceptance gate tương ứng được duyệt. README placeholder không đồng nghĩa service, feature hay integration đã chạy; không tạo package/toolchain mới chỉ để lấp cây thư mục.

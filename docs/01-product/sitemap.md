# Sitemap

**Trạng thái:** route direction only; current routes belong to prototype.

| Area | V1 function |
|---|---|
| `/` | Local app landing/status, setup and data/security limits |
| `/login` | Local password-only lock/login; recovery contract pending |
| `/settings/data` | Local SSI FastConnect Data configuration and entitlement/connection status |
| `/market` | SSI-supported instruments, reference/history/chart and data quality states |
| `/portfolio` | Local portfolio overview and simulated ledger |
| `/portfolio/backtest` | Historical snapshot selection, assumptions, replay and results |
| `/portfolio/paper` | Start/stop/pause paper live session and inspect simulated orders/fills |
| `/news` | Tích hợp sau khi news engine độc lập và source gates sẵn sàng |

Không có hosted `/auth`, public demo account, server workspace hay cloud portfolio API trong hướng V1. Tên route có thể đổi khi triển khai; local data flow và simulated-only trading boundary là yêu cầu sản phẩm.

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
| `/news` | Deferred until separate project-built news engine is integrated |
| `/model-lab` | Deferred outside first MVP |

There is no hosted `/auth`, public demo account, server workspace or cloud portfolio API in the V1 direction. Route names may change with implementation, but local-only data flow and simulated-only trading boundary may not.

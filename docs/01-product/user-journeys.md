# Journeys / Luồng sử dụng

**Tóm tắt:** Luồng chính đi từ Market qua Quant, Backtest rồi Portfolio. Strategies có khu vực riêng; Assets quản lý quỹ và từng ngân sách.


Setup toolchains → start local Go/Python → password setup/login → Market with fixture badge. Adding credentials does not open source gates.

Market snapshot → Quant indicator or Research file → save/run frozen code → logs/table/Parquet/2D artifact. File navigation is a sidebar, not tabs.

Separate Backtest file → detailed tape/capital/non-overlapping UTC ranges → Train → frozen Test → per-run report/history. No optimizer or Strategy-file conversion.

Assets → named fund → separate Manual/Strategy budgets → explicit synthetic replay → orders/callbacks → Portfolio source-marked positions/cash. Missing prices leave NAV/P&L unavailable.

Lock/close browser keeps services running. Stop/crash interrupts jobs and retains capital/positions. Reconcile open remainder explicitly; no inferred missing fills or auto-resume. [Recovery](../12-operations/recovery-release.md).

# Screen flows

Setup/start → local password → Market. Expired/locked session returns to login; no SSI credentials in browser.

Market instrument/snapshot → daily chart/source/as-of. Quant → indicator/benchmark → null warm-up/report or Research editor.

Backtest file → detailed tape/capital/non-overlapping ranges → Train → frozen Test → run report/history. Strategy callback file → Strategy allocation → explicit synthetic replay → Run/Stop. Wrong kinds fail before execution.

Assets → named paper/tracking fund → deposit/withdraw/transfer free cash → separate Manual/Strategy budgets. Manual advances quotes/order/cancel. Portfolio shows source-marked positions and missing NAV reasons; tracking CSV requires Preview then Apply.

Lock/close/switch file keeps services running. Stop/crash interrupts jobs. Reconcile explicitly cancels unfilled remainder, keeps cash/positions/cursor and infers no missing fills. Offline CLI backup restores to new root/profile. [Lifecycle](states-lifecycle.md).

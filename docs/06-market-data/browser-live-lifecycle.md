# Market feed lifecycle

**Tóm tắt:** Reconciler hiện kiểm tra offline. Khi mất feed thật, phải giữ gap và chặn fill, không tạo dữ liệu thay thế.


Browser → authenticated Go → Python is the built-in boundary, never a browser SSI socket. Subscriptions/Reconciler provide offline semantics, not connected transport; live status is unavailable.

Target: approve capability → multiplex subscriptions → normalize timestamps/provisional/closed bars → sequence/freshness checks → reconnect/licensed backfill → reconcile before fills. Lost intervals remain gaps, not fabricated data.

Current paper explicitly replays synthetic quotes. Manual/Strategy allocations have independent cursors/books; global exchange liquidity is not shared across allocations. An order cannot fill on its placement quote. Lock/close browser does not stop services. Service stop interrupts jobs; restart never auto-resumes or infers missing fills.

# Data model / Ownership

**Tóm tắt:** Giữ định danh instrument đầy đủ, decimal dạng chuỗi, thời gian UTC và provenance xuyên suốt. Không dùng ticker đơn lẻ hoặc giá trị 0 để thay dữ liệu thiếu.


Canonical models live in [market schema](../../contracts/market.schema.json). Instrument identity includes venue, board, class and native symbol; ticker alone is insufficient. UTC timestamps separate event/received/available times. Money/prices/quantity cross APIs as decimal strings.

Go SQLite owns Run/Event/Artifact, Fund/Allocation/Position/LedgerEvent, simulated orders and replay cursors. [Response DTO schemas](../../contracts/gateway.schema.json) are generated from Go, not a complete request OpenAPI. Python internal contracts are generated separately.

Market snapshots carry source/quality/revisions/checksums/parser/schema version and synthetic status. CodeSnapshot freezes entry/helpers/params/uv.lock; selected data/rules use immutable IDs. Trusted user code is not a sealed environment.

Tracking funds contain settled user assertions; simulated fills belong to paper allocations. Weighted-average cost includes buy costs. NAV sums parent cash, allocation cash/reserved/unsettled and marked positions once. Unknown mark means null NAV/P&L.

Engine source SHA-256 is frozen in each CodeSnapshot and verified by workers; changed engine source requires a new snapshot. Frozen Test also rejects an engine hash change. Reproducing an older run requires its matching Git/engine/dependency state.

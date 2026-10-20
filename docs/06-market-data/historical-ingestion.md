# Historical ingestion

**Tóm tắt:** Pipeline hiện tại chỉ chuẩn hóa fixture thành Parquet bất biến. Pagination/checkpoint và tải lịch sử từ SSI thật chưa được triển khai.


Implemented: synthetic daily JSON → strict canonical rows → deduplicate exact revisions/reject conflicts → immutable Parquet → checksummed completed manifest → DuckDB in-memory query. Same fixture yields the same snapshot ID. Failed writes do not replace completed snapshots.

Not implemented: SSI network pagination, durable provider checkpoints/retry budgets, real calendar coverage scans and corporate-action pipeline. Daily fixture success does not establish these capabilities or storage rights.

Backtest uses a separate immutable detailed quote tape; daily OHLC is not a detailed-fill fallback. Runs reference data/rules/code/lock IDs. [Quality](../04-data/lifecycle-and-quality.md).

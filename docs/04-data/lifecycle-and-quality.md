# Lifecycle & quality

Current input is synthetic only. Normalization validates identities, timestamps, decimals and closed bars. Exact duplicate revisions deduplicate; conflicts fail; multiple revisions require explicit selection. Parquet/manifest checksum and row count are checked on load; incomplete writes do not publish a completed replacement.

Fixture/partial/stale/unavailable differ. Warm-up/missing output is null, not zero. Daily fixtures do not establish calendar completeness. Actual trading-calendar gap detection, rights-aware retention and corporate-action adjustment remain blocked/pending.

Offline Reconciler tests sequence/time/freshness/gaps/reconnect transitions; it is not SSI transport. Never synthesize bars/fills for a lost real feed interval. Paper eligibility needs fresh reconciled detailed data and effective rules. Last-observed Portfolio marks can be stale and are not executable quotes.

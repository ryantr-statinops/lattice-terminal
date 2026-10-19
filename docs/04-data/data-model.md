# Entities và data dictionary

**Trạng thái:** logical model định hướng cho local SSI/VN market data; physical schema chưa chốt. Đây là domain proposal, không phải schema production đã triển khai.

```mermaid
erDiagram
    SOURCE ||--o{ INGESTION_RUN : produces
    INGESTION_RUN ||--o{ RAW_OBJECT : records
    INSTRUMENT ||--o{ CANDLE_REVISION : identifies
    INSTRUMENT ||--o{ QUOTE : identifies
    RAW_OBJECT ||--o{ ARTICLE_REVISION : normalizes
    ARTICLE ||--o{ ARTICLE_REVISION : versions
    ARTICLE_REVISION }o--o{ EVENT : evidence
    EVENT }o--o{ ASSET : maps
    DATASET_SNAPSHOT }o--o{ RAW_OBJECT : references
    DATASET_SNAPSHOT }o--o{ CANDLE_REVISION : freezes
```

## Dictionary chuẩn

| Entity | Trường tối thiểu và quy tắc |
|---|---|
| Source | source_id, provider, product/feed, terms_version/hash, permitted_use_policy_id, evidence flags; không có credential |
| Asset | asset_id, canonical name/code and asset class; equities, indices, derivatives and bonds must not be conflated |
| Instrument | instrument_id, venue, market/board type (e.g. HOSE/HNX/UPCOM/DER/BOND where applicable), instrument class, native symbol, lifecycle dates and precision evidence |
| CandleRevision | instrument_id, interval, open_time, close_time, is_closed, OHLC, base_volume, quote_volume nếu có, trade_count nếu có, revision_id, source_object_id, ingested_at, available_at |
| Quote | instrument_id, price/bid/ask theo source payload, event_time, received_at, source; không dùng last trade như bid/ask |
| IngestionRun | run_id, source_id, adapter_version, requested range, started/finished_at, status, checkpoint, counts, error_class |
| RawObject | object_id, source URL an toàn, response metadata cho phép, retrieved_at, content_hash, media/schema version, timestamp_unit, storage_ref, policy_id |
| Article | article_id, source_id, canonical_url/native_id, first_seen_at, lifecycle status |
| ArticleRevision | revision_id, article_id, published_at nullable, source_updated_at nullable, observed_at, available_at, allowed title/summary/text, content_hash, language, parsing_version |
| Event | event_id, type, entity links, confidence, extractor_version, evidence revision IDs, available_at; không thay article gốc |
| DatasetSnapshot | snapshot_id, immutable manifest, content hashes, sources/revisions, time coverage, availability policy, feature version, schema/dtype, policy eligibility |

Natural key nến/ohlc là venue+market_type+instrument_class+native_symbol+interval+open_time; each source correction creates a revision. Never use symbol alone as identity. SSI response fields and timestamps must be mapped with endpoint-specific evidence; preserve original timestamp/unit and normalize to UTC without collapsing board/product semantics.

Lưu UTC có timezone. UI mặc định Asia/Ho_Chi_Minh và hiển thị timezone. Raw giữ original value/unit/timezone khi được phép; standardized timestamp không xóa bằng chứng ban đầu. Published time thiếu là null, không điền retrieval time dưới tên published_at. Source revisions, ingested_at và available_at là các khái niệm riêng.

Price/candle lịch sử không chứa thông tin portfolio riêng. Dataset manifests không chứa user ledger; scope truy cập snapshot theo source policy và account entitlement khi có.

User profiles, if retained, are local to one installation; no server account/workspace ownership is part of V1. Portfolio simulator state and replay rules belong to [portfolio](../07-portfolio/README.md). Model Lab/artifact contracts are deferred. Keep source, instrument, market-data revisions, portfolio simulation and news entities separate; do not imply SSI coverage/permission from a generic entity schema.

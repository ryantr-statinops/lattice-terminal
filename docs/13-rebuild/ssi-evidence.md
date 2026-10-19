# SSI capability evidence for Kestrel

2026-10-19: no account registration, probe, payload capture or production approval. REST and streaming remain documented=true, access-tested=false, rights-confirmed=false, approved=false. Synthetic fixtures do not change these flags.

Official capability references: [REST APIs](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/danh-sach-cac-api), [streaming](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/du-lieu-streaming), [registration](https://guide.ssi.com.vn/ssi-products/service-registration).

| Area | Required account-specific evidence | Current |
|---|---|---|
| Reference/instruments | Equity venue/board/classes, symbol lifecycle, fields and timestamps | Blocked |
| Daily history | Date range, pagination/quota, raw/adjusted semantics and corporate actions | Blocked |
| Intraday history | Resolution, retention/history depth, sessions and corrections | Blocked |
| Trades/depth history | Whether replayable event history exists; ordering, sizes and coverage | Not established by OHLC API documentation |
| Streaming | Exact groups, message identity/order, concurrent subscriptions, reconnect/replay | Blocked |
| Local use | Storage, research/backtest, derived output, display/export, retention/deletion and expiry | Unconfirmed |

Source policy lives in local application data, not Git. Separate scope and evidence references govern probes and production. A schema probe cannot produce a reusable market snapshot or approve retention. UI reports exact gate status; it never enables provider access by toggling a connection switch. There is no SSI Trading route.

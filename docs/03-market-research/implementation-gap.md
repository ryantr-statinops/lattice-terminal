# Implementation gap map

**Review:** 2026-10-26. Read-only repository review. No provider credentials, live calls, or account data were used.

## Current behavior and required outcome

| Area | Current behavior | Required outcome | Main gap |
|---|---|---|---|
| Provider inventory | VNDIRECT, TCBS, DNSE, SSI and fixture are registered in the Python engine; the browser provider hub calls the engine. | Extensible Vietnamese broker/datafeed registry with per-dataset and per-asset coverage. | Provider records describe broad capabilities and do not represent rights, data classes or lifecycle state separately. |
| Connection state | DNSE reports a fixed latency and `connected` when keys exist; listing providers invokes `ping()` for every provider. | Listing is local/cached; a user-triggered check reports measured connection/access state. | Credential presence is mistaken for service reachability and capability approval. |
| TCBS/VNDIRECT | TCBS candle and instrument methods call VNDIRECT. | Independent official TCBS adapter and explicitly named community sources. | UI source identity can differ from the service producing the data. |
| Routing | Router defaults to VNDIRECT/TCBS and stores policy in memory. Fallback may be implicit. | Persistent routing by dataset and coverage, with visible provenance and explicit fallback. | Restart loses policy; consumers can silently switch source. |
| Source gate | SSI REST and stream capabilities have independent records; other provider datasets are not gated generically. | Evidence and approval per provider × dataset × asset scope. | Existing policy cannot express account read-only, rights scope, expiry or provider-specific transports generically. |
| Instruments and series | `Instrument` is limited to HOSE/HNX/UPCOM equity; `Candle.interval` allows `1d` and `1m`. | Typed identities and datasets for every selected-provider asset class. | Bonds, derivatives, funds, commodities, macro series and unknown classes cannot be represented faithfully. |
| Market/Quant reads | Market repository is fixture-backed; Quant derives from that repository. | Read approved persisted provider datasets with quality/provenance. | Provider router does not own the consumed repository path. |
| Historical ingestion | Fixture JSON is published as local Parquet snapshots. | Provider-specific paging, checkpointing, retry, revisions, quality and rights-aware retention. | No durable upstream ingestion workflow. |
| Live transport | Stream ordering/freshness reconciler and source gates exist, but no production provider stream is connected. | Provider-specific subscriptions, reconnect/backfill and gap reconciliation. | No authorized real transport or shared ingestion lifecycle. |
| Account synchronization | SSI secret plumbing exists; no user-facing broker account snapshot workflow. | Read-only account/balance/position/history views separate from local ledger. | No canonical account records, sync cursor, account UI or read-only capability matrix. |
| Backtest | Separate causal detailed-event engine uses fixture tapes and synthetic rules. | Select real immutable snapshots and block unsupported class/rule/fill combinations. | Instruments, rules and datasets assume a narrow synthetic equity tape. |
| Paper Strategy | Strategy callback requires a paper allocation and fixture replay; intents become LO paper orders. Events include paper order/fill/cancel/cursor/session. | Signal-only or paper mode on eligible live feed/replay with explicit per-class simulation coverage. | No typed signal event, no live source connection, and order execution is inseparable from Strategy setup. |
| Market rules/fill | Synthetic LO quote fill; actual sessions, settlement and production liquidity remain unverified. | Effective-dated rule and fill registry selected by asset, venue and session. | Rules cannot be applied safely outside the synthetic fixture case. |
| Notifications | Toast component is transient; run output/job stream is not a user notification inbox. | Persistent inbox, unread badge, toast and opt-in Telegram delivery. | No notification store, preferences, delivery queue or Telegram connection. |
| Secrets | SSI credentials use host OS keyring via CLI; Compose export is a temporary plaintext file and app transport does not consume it. | A general local credential interface usable by native and Compose UI without browser exposure. | Per-provider CRUD and runtime injection do not exist; Compose does not share host keyring. |
| Recovery | SQLite and managed data backup are allowlisted; OS credentials are excluded. | Preserve approved local datasets/account snapshots/inbox while excluding secret material and preventing replayed outbox actions. | New data/outbox classes need explicit backup and restore policy. |

## Implementation order implied by the gaps

1. Replace provider status/routing assumptions and extend capability evidence before adding live fetches.
2. Add stable instrument/dataset contracts and versioned readers before storing provider records.
3. Build durable ingestion and one adapter capability per independently reviewed dataset.
4. Connect Market/Quant and broker read-only snapshots to persisted data while retaining provenance.
5. Add simulation coverage only after matching point-in-time data, rules and fill semantics are reviewed.
6. Separate Strategy signals from paper orders, then persist local notifications and Telegram deliveries.
7. Extend backup/recovery only for the new allowlisted data; never include vault keys or tokens.

## Acceptance state meanings

- **Documented:** official material describes the capability.
- **Configured:** required local settings exist; does not prove connection or access.
- **Access checked:** a scoped, permitted request succeeded.
- **Rights confirmed:** evidence covers the exact fields, local use, purpose and retention.
- **Operational:** adapter, persistence and consumer are implemented and pass tests.
- **Simulation enabled:** dataset also has an approved effective rule pack and fill model.

Do not collapse these states into a single `connected` flag. A capability with missing evidence remains visible with its specific pending reason.

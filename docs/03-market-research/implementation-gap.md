# Implementation gap map

**Review:** 2026-10-28. Repository/code review. No provider credentials, live calls, or account data were used.

## Current behavior and required outcome

| Area | Current behavior | Required outcome | Main gap |
|---|---|---|---|
| Provider inventory | VNDIRECT, TCBS, DNSE, SSI and fixture are registered. SSI has offline-tested dataset paths for selected asset/venue pairs; other provider files remain documentation, legacy behavior or incomplete adapters. | Vietnamese broker/datafeed registry with end-to-end capability coverage by provider, dataset, asset and venue. | Most non-SSI capabilities do not yet have a verified adapter → store → consumer path. |
| Connection state | Provider listing is local and does not ping every service. Credential presence is shown as configured/unknown; DNSE stays blocked because a real connection check is not implemented. | Separate configured, access-checked, rights-approved and healthy states per service/capability. | No real account connectivity/entitlement checks have been run; a successful credential check alone must not approve data rights. |
| TCBS/VNDIRECT | TCBS methods explicitly reject unsupported ingestion rather than returning VNDIRECT data as TCBS. VNDIRECT remains a distinct community source. | Independent official TCBS adapter and explicit source identity for every response. | TCBS OpenAPI datasets still need endpoint-level implementation and account/rights evidence. |
| Routing | Gateway stores routing policy in SQLite and applies validated dataset routes to the engine. SSI Market reads require the selected provider and venue route. | Persistent routing by dataset and coverage, with visible provenance and explicit fallback for every consumer. | Generic capability/rights coverage checks and audits of legacy fallback consumers remain; the engine still has in-memory runtime policy. |
| Source gate | SSI ingestion/read paths authorize exact capability scopes. Other provider datasets are not covered by the same end-to-end gate. | Evidence and approval per provider × dataset × asset × venue. | Provider-wide rights, access evidence, expiry and transport-specific states are not yet implemented generically. |
| Instruments and series | Contracts cover multiple venues and include equity, index, derivative, covered-warrant, ETF and bond identity. Candle intervals and separate non-candle records are represented. | Normalize every selected provider dataset without coercing unknown classes or units. | Current adapters cover only selected SSI class/venue pairs; many provider datasets and lifecycle/alias cases remain unimplemented. |
| Market/Quant reads | Market can read SSI catalogues and selected routed index/daily-candle snapshots. Quant still reads fixture data. | Market and Quant consume approved persisted datasets with quality and provenance. | Provider-backed Quant and a general non-candle dataset explorer remain incomplete. |
| Historical ingestion | SSI REST adapters paginate selected catalogues and daily series into immutable Parquet snapshots; Gateway tracks ingestion jobs/checkpoints. | Provider-specific paging, resumable page state, retries, revisions, quarantine, quality and rights-aware retention across datasets. | Durable page-level resume and common revision/quarantine/quality handling are not complete across provider ingestion. |
| Live transport | Stream ordering/freshness reconciliation exists, but no production provider stream is connected. | Provider-specific subscriptions, reconnect/backfill and gap reconciliation. | No live provider feed has been entitled, connected or reconciled end to end. |
| Account synchronization | Broker credential plumbing exists; broker account snapshots are not synchronized or shown. | Read-only account/balance/position/history views separate from the local fund ledger. | Canonical account snapshots, per-operation allowlist, sync cursor and account UI remain unimplemented. |
| Backtest | Separate causal detailed-event engine runs fixture tapes with synthetic rules. Provider candle snapshots are not a supported Backtest source. | Select immutable real snapshots and block unsupported class/rule/fill combinations. | Real detailed market data, point-in-time release/revision handling and pinned run provenance are missing. |
| Paper Strategy | `signal_only` and `context.signal(...)` work on fixture replay; run events persist/display signal history. Paper order intents still use fixture replay. SSI live is blocked in the UI. | Signals on eligible replay/live sources and paper only under class/venue rule and fill coverage. | No production live feed or provider-backed paper runtime; missing/stale feed reconciliation must block fills. |
| Market rules/fill | Synthetic LO quote fill supports fixture mechanics; real sessions, settlement, fees and production liquidity are unverified. | Effective-dated rule and fill registry selected by asset, venue and session. | Real-market simulation must remain disabled until data, rules and fill evidence match. |
| Notifications | Run history displays Strategy signals. There is no persistent notification inbox or delivery service. | Persistent local inbox, unread badge, toast policy and opt-in Telegram delivery. | Notification store/inbox and Telegram are deliberately deferred from the current implementation scope. |
| Secrets | SSI credentials use host OS keyring via CLI. Compose export is temporary plaintext plumbing and is not consumed by the app. | Provider credential management for native/Compose without browser exposure. | General provider CRUD and Compose runtime secret consumption are incomplete. |
| Recovery | SQLite and managed data backup are allowlisted; OS credentials are excluded. | Preserve approved datasets and account snapshots while excluding secret material and preventing old external deliveries after restore. | Account snapshots and the deferred notification/outbox data do not yet have backup/restore policies. |

## Implementation order implied by the gaps

1. Keep provider configuration, access, rights and health distinct; require exact SourceGate approval before local retention/display.
2. Finish provider-backed consumers from existing snapshots. The next user-visible gap is Quant reading the explicitly selected SSI daily-candle route; keep units, quality and provenance visible.
3. Continue SSI and other-provider integration one endpoint × dataset × asset × venue at a time. UPCoM daily candles are an unimplemented SSI dataset candidate; each addition remains offline-tested and rights-gated until approved.
4. Complete common ingestion recovery, page-level resume, revision/dedup and quarantine before scaling provider history or live feeds.
5. Implement broker account reads with an explicit read-only allowlist and snapshots isolated from the local fund ledger.
6. Enable real Backtest/Paper only after point-in-time data, effective rules, calendar, fees/tax, settlement and observed-liquidity fill behavior all cover the selected instrument and session.
7. Extend Strategy from fixture replay to a reconciled live feed only after provider access and freshness/gap recovery are proven. The signal-only replay core already exists.
8. Keep persistent notifications and Telegram deferred as agreed; extend backup policy only when new allowlisted data is implemented, never with vault keys or tokens.

## Acceptance state meanings

- **Documented:** official material describes the capability.
- **Configured:** required local settings exist; does not prove connection or access.
- **Access checked:** a scoped, permitted request succeeded.
- **Rights confirmed:** evidence covers the exact fields, local use, purpose and retention.
- **Operational:** adapter, persistence and consumer are implemented and pass tests.
- **Simulation enabled:** dataset also has an approved effective rule pack and fill model.

Do not collapse these states into a single `connected` flag. A capability with missing evidence remains visible with its specific pending reason.

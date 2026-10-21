# Architecture decisions / Rebuild register

**Tóm tắt:** Các quyết định rebuild đã chốt thay thế mô tả prototype cũ. Trạng thái triển khai fixture không đồng nghĩa phê duyệt dữ liệu thật.


Accepted rebuild: 2026-10-19. Implementation status reviewed 2026-10-20; this is a fixture build. Earlier prototype/cloud proposals are superseded as runtime descriptions, preserved in Git history. A decision is not evidence of production capability.

| Record | Accepted choice | Implementation / boundary |
|---|---|---|
| RT-ADR-001 | React/Vite/Router/TS/Tailwind | Current web |
| RT-ADR-002 / 027 | Go gateway + authenticated local Python; Compose-first local runtime, three-terminal host debugging | Compose uses one Linux container and Unix process groups; host debugging runs processes separately |
| RT-ADR-003 / 006 | Local-service ownership of future ingestion/stream | Offline reconciler only; no actual SSI transport/scheduler |
| RT-ADR-004 / 010 / 025 | Model Lab deferred | No Pyodide/browser-training runtime |
| RT-ADR-005 / 012 / 020 | Vietnam equities, SSI FastConnect Data direction | Synthetic fixtures; actual rights/coverage blocked |
| RT-ADR-007 / 026 | Go-owned SQLite, Python-owned Parquet, DuckDB queries | Replaces PostgreSQL/object-store and engine-selection proposal |
| RT-ADR-008 / 022 / 028 | Single profile, session password, Argon2id; OS keyring CLI | Not whole-data encryption; Compose secret export is temporary plaintext plumbing, not app SSI access |
| RT-ADR-009 / 023 | Separate historical Backtest and paper Strategy; no real orders | Detailed synthetic LO only; real rules/settlement blocked |
| RT-ADR-011 / 019 | Local-first Compose on Windows/macOS/Linux; no hosted deployment | Compose fixture runtime, Vite dev override and optional three-terminal host debugging |
| RT-ADR-013 | Dark-only terminal presets and Appearance | Owner revision 2026-10-20; immediate versioned local preferences |
| RT-ADR-014 | Editable semantic color roles, accent separate from market colors | Terminal Black accent #4DB5FF; Graphite/Midnight presets |
| RT-ADR-015 | IBM Plex Mono default, JetBrains Mono optional | Licensed WOFF2 bundled locally with Vietnamese glyphs; no runtime CDN |
| RT-ADR-016 | TanStack Query server state + React local state | Already installed; URL filter sharing limited |
| RT-ADR-017 | Apache ECharts 6.1.0 Market candles; Plotly basic 2D reports | ECharts attribution notices retained in repository; no TradingView chart logo; no 3D renderer yet |
| RT-ADR-018 | Semantic CSS variables and shared React primitives | Theme/UI/feature layers; existing chart and execution contracts retained |
| RT-ADR-021 | User-owned local storage with explicit recovery boundaries | Offline ZIP, new-root restore, separate OS secrets/browser/copies |
| RT-ADR-024 | News independent workstream | No current news runtime route |
| RT-ADR-029 | Three separate program kinds; sidebar files, no file tabs | Research run / Backtest replay / Strategy callbacks, distinct runs |
| RT-ADR-030 | Named VND funds and independent allocation ledgers | Decimal/weighted-average; Backtest doesn't touch funds |
| RT-ADR-031 | Lock/close/switch file keeps jobs running | Stop/restart/restore explicit; no auto-resume |

## Rationale and review triggers

Local ownership avoids cloud dependencies. Go owns serialized transactional finance; Python owns analytics/data/workers. Code runs with user privileges, so process separation is cancellation/fault isolation, not a sandbox. Frozen code/lock/data/rule IDs support repeatability, without guaranteeing arbitrary code is deterministic or free of lookahead.

Revisit source/instrument/rule decisions only with account-specific entitlement/rights/coverage evidence. Revisit storage/security with workload, migration, OS-account threat model and backup evidence. Revisit charts for the later 3D/factor milestone; don't assume Plotly basic supports surfaces. Revisit theme/font tokens based on accessibility/performance/license review. Do not silently reopen accepted product/stack choices.

## Still open / blocked

Real SSI transport and paging/checkpoint/reconnect integration; actual market calendars/rules/corporate actions/settlement; production fill semantics/data detail; retention enforcement and large-history recovery. Full external request OpenAPI/generated clients, broad browser regression, run comparison and UX polish remain further engineering work. [Current progress](../13-rebuild/progress.md).

Engine source SHA-256 is frozen in each CodeSnapshot and verified by workers; changed engine source requires a new snapshot. Frozen Test also rejects an engine hash change. Reproducing an older run requires its matching Git/engine/dependency state.

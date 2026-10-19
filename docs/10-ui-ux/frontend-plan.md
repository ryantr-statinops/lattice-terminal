# Frontend plan — local-first V1

**Trạng thái:** kế hoạch thiết kế theo product direction; không phải cam kết V1 đã triển khai. Reviewed 2026-10-19 against current code. Xem [product scope](../01-product/vision-and-scope.md), [sitemap](../01-product/sitemap.md) và [screen flows](screen-flows.md).

## Priorities và implementation gaps

| Area | Current prototype | V1 target / dependency |
|---|---|---|
| Setup/local access | Account placeholder; chưa có local auth/secret flow | Windows start/status, safe configuration, password/session and recovery decisions |
| Market | Synthetic instruments/chart, watchlist, browser-stream status | Approved SSI instruments/history/quality via loopback API; upstream connection owned by local service |
| Portfolio | Manual/CSV holdings, browser persistence, fixture valuation | Durable local ledger, deterministic backtest and simulated paper sessions after accounting/market/fill decisions |
| Data quality | Fixture source-age/loading/error states | Source, as-of, coverage, gap, provisional/closed, stale/partial/unavailable throughout market and simulation flows |
| News | Synthetic fixture page | Independent engine and later reviewed integration; not a terminal MVP dependency |
| Model Lab | Mock form/adapter | Deferred; no training, runtime download or result-sync requirement in V1 |

Current `/terminal/*` routes belong to prototype, including news-first redirect. They are not a decision to prioritize news in V1. The product sitemap is target-only until implementation updates routing.

## Accepted frontend choices

[RT-ADR-013 through 018](../02-architecture/decisions.md#frontend-adrs-locked-2026-10-17) already select dark default with light semantic tokens, accent `#21684e`, Inter/JetBrains Mono with fallbacks, TanStack Query/React state, Lightweight Charts and Tailwind/CSS variables. Do not reopen these as undecided choices or install already-present dependencies to satisfy this plan.

Fonts must follow the [local delivery policy](design-tokens.md#font-families); current remote HTML fonts remain an implementation gap. Use existing primitives and [component inventory](component-inventory.md) before adding abstractions. Contrast and accessibility are requirements, not measurements already passed.

## Behavior to design before building V1 screens

- Configure credentials through a reviewed local service flow for the exact authorized purpose; never put SSI secrets in browser assets/storage/logs.
- Market requests use loopback API and explicit production source approval. Default fixtures stay labeled; access probes never silently supply product data.
- Backtest setup records approved snapshot, universe, coverage, strategy/capital/currency and cost/fill assumptions. Results record engine/config versions and simulation labels.
- Paper UI exposes source/session/freshness, simulated orders/fills and explicit stop; no real-order action. Handle gaps/restart per simulator policy before claiming live state.
- Distinguish browser visibility, UI lock, upstream connectivity and local-service stop using [V1 lifecycle](states-lifecycle.md). Tab-hidden and lock/paper policy are pending, not inherited prototype timers.
- Preview settings reset, managed-data deletion, secret removal and restore separately; user-owned copies remain outside implicit cleanup.

## Layout, accessibility và acceptance

Desktop local research is the primary context; responsive behavior must preserve readable data, source/quality labels and keyboard access. Do not define a news-first or mobile-training flow as V1 priority. Use color plus text/icon, table alternatives for charts, stable focus, reduced motion and explicit loading/refresh/error/empty/partial states.

Before implementation release, review setup/lock behavior, permitted market-data access, partial valuation, reproducible backtest reports, interrupted paper sessions, failed local writes and recovery. Validate actual UI/contrast after implementation; this docs change adds no test-result or production-readiness claim.

## Decisions still open

Local password/profile/key recovery; V1 process/API/persistence contract; supported SSI fields/classes; calendar/accounting/cost/fill rules; live session behavior on hidden/locked UI; backtest execution/cancel/recovery. Track them through the [roadmap](../../task/next-plan.md) and ADRs before dependent implementation. No new wire schema, routes or runtime is selected here.

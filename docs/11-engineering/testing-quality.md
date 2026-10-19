# Testing và quality

**Trạng thái:** prototype regression coverage đang chạy local và trong CI; production integration/quant suites vẫn là yêu cầu tương lai.

## Checks hiện có

- Frontend: `npm run test:web`, `npm run lint`, `npm run typecheck`, `npm run build`, `npm run security:env-boundaries`, `npm run fixtures:check`, `npm run test:tooling`.
- Vitest/jsdom covers routing + fixture rendering, portfolio valuation/CSV/persistence, mocked WebSocket lifecycle, Model Lab mock labeling, data age, refresh success/failure and stale data preservation.
- GitHub Actions runs frontend, FastAPI/OpenAPI drift, research inspection, Go gateway and fixture ingestion checks. Changes to `main` require PR review and required status checks.

## Scenarios đã có regression tests

- Portfolio: complete/partial/missing prices, zero cost basis, candles out of order/open, strict decimals, unsupported assets, CSV BOM/CRLF/quotes/header/row widths, atomic import, overlapping FileReader results, corrupt storage, partial persisted rows and quota write failure.
- Stream: fake WebSocket subscription, malformed/valid messages, no-message stale timeout, reconnect backoff, visibility pause/resume, StrictMode and teardown.
- Refresh: initial loading vs background refresh, cache data during refresh, error with previous data, source timestamp age and retry controls.
- Model Lab: placeholder result remains `simulated`/`mock` and configuration does not change mock metrics.

## Chưa được kiểm chứng

Database constraints, source rights, real feed gaps/duplicates/backfill, browser CSP and performance, actual worker runtime/cancel, walk-forward quant validation, contrast ratios, deployment, monitoring and recovery. CI fixture tests do not approve a market/news source or prove profitability.

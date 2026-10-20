# Success metrics

**Trạng thái:** khung đo lường; đã có fixture simulator/tests; chưa có tích hợp SSI thật, baseline thị trường thật hoặc pilot người dùng.

## Local setup and privacy

- Clean Windows clone can install/start/stop using documented steps; record failures and time to first localhost screen.
- Verify market credentials, market payloads, portfolio and research results remain local; no unexpected outbound calls/telemetry.
- Local backup/export/restore/reset and password behavior succeed on a clean profile.

## SSI data quality

- Entitled endpoint/feed availability and history depth by instrument/interval.
- Coverage completeness, missing ranges, duplicates/revisions, timestamp/session mapping, stale duration and reconnect recovery.
- Request/stream quota usage and stop/retry behavior against the actual user plan.
- Do not publish a data quality score without recording the exact account entitlement, source version, period and excluded data.

## Portfolio simulator

- Backtest replay is deterministic for the same snapshot/config/engine version.
- No-lookahead fixtures and market calendar/fees/lot/tick assumptions pass defined scenarios.
- Paper feed gaps, stop/restart and simulated-fill audit produce safe, explainable states.
- Report coverage, fees, taxes/slippage assumptions, drawdown and simulated trade count; no profitability/alpha claims without validated data and evaluation.

## News và phạm vi hoãn

News quality metrics (coverage, correction handling and entity-linking precision) được định nghĩa trong workstream news độc lập trước khi tích hợp. Model Lab benchmark/runtime metrics được hoãn; không phải tiêu chí V1.

Set numeric targets after a reproducible baseline and pilot. Every threshold needs owner, test setup, dataset version, reason and date; do not tune acceptance thresholds after inspecting final test output.

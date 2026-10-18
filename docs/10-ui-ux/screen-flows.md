# Screen flows

**Trạng thái:** target UI follows local-first scope; current prototype screens are fixtures/mock.

## Local setup and password

First run guides the user to configure SSI FastConnect Data without pasting credentials into source code or browser fields. Exact local secret-store flow is pending. Password-only local login/lock has no email account; reset and encryption behavior must be stated before implementation. Show provider status without echoing key values.

## Market research

Market screens show Vietnamese instruments/reference data supported by the user's SSI entitlement. Identify venue/board, instrument class, source/feed, interval, session/timezone, last observed time, closed/provisional state, coverage gaps, partial/stale/unavailable status and adjustments/revisions when known. Do not present fixtures or fallback sources as SSI data. REST/history is the initial/recovery source; streaming only appears after local connection and reconciliation.

## Portfolio

Users create a local portfolio and run historical backtests or paper live sessions. Backtest setup shows source snapshot, data range/coverage, strategy, capital/currency and costs/fill assumptions. Paper live shows feed freshness and makes every order/fill visibly simulated. Stop or pause safely on feed gap, stale data or market/session state. Never show a real-order action or ask for trading API credentials.

## News and Model Lab

Current news fixture screen is placeholder; project-built international/Vietnam news engine is separate and integrated later. Model Lab is outside first MVP; remove/defer mock metrics rather than implying actual analysis capability.

## Local data lifecycle

Explain where files are stored and how to export/backup/reset. Logout/lock behavior must be consistent with the approved local password and secret-storage design. No portfolio/news/data payload is uploaded by default.

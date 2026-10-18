# User journeys

**Trạng thái:** target for local-first V1; current app still shows fixtures and mocks.

## Clone and start locally

Clone the repo on Windows, follow the setup guide, start the local web/API processes and open localhost. First-run flow explains local data paths, password-only access and SSI credential setup without exposing keys in source/browser/logs. Exact one-command launcher and recovery flow remain to be designed.

## Configure SSI and inspect market data

User configures their own SSI FastConnect Data service. App validates configuration safely, reports which REST/stream capabilities are entitled and shows supported instruments/fields. The user explores historical/reference data and, after enabling an entitled stream, sees source, session, last update, closed/provisional state, coverage gaps and stale/partial/unavailable status. No undocumented fallback source is used.

## Backtest a portfolio

User chooses a local portfolio, market/instrument universe, historical snapshot and date range, strategy/rules, capital/currency and fee/slippage/fill assumptions. Preview shows available rows and gaps. Run produces a reproducible simulated report with snapshot and engine versions. Portfolio accounting and market-specific mechanics need decisions before this journey is implementable.

## Paper live session

User starts a paper session using live SSI Data feed. The app reconciles against available history, then simulates orders/fills locally. Feed disconnect, stale data, gap, closed market or app restart pauses or marks state unknown according to explicit policy. Every outcome is labeled simulated; nothing reaches SSI Trading.

## News and Model Lab

News engine is built separately for international and Vietnam sources, then integrated in a later phase through a source-governed contract. Model Lab is deferred outside V1; current mock result is not a product capability.

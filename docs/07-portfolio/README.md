# Portfolio — backtest và paper trading

**Trạng thái:** portfolio simulation is in first MVP scope. Current UI is fixture/localStorage prototype only; local persistence, backtesting and paper engine are not implemented.

V1 portfolio is a local research ledger for Vietnamese instruments. It supports:

1. **Backtesting:** replay historical data with an explicit portfolio, signal/strategy rules, fee/slippage assumptions and data availability. Results must be reproducible and show data coverage/gaps.
2. **Paper live trading:** consume an entitled/reconciled SSI live feed and simulate orders/fills locally. It never sends real orders, never connects to FastConnect Trading and never asks for broker trading credentials.

Data/config/ledger/results stay on the user's machine. There is no account/workspace cloud isolation or public sharing in V1. A local password screen is requested; recovery and encryption decisions are pending.

## Documents

1. [Portfolio simulator contract](ledger-and-valuation.md): local portfolios, backtest and paper lifecycle; financial rules still to be completed.
2. [Import, local storage and ownership](imports-and-ownership.md): CSV/backup/delete direction; not yet an implementation schema.

## Contracts still needed

- Supported assets/markets (HOSE/HNX/UPCOM; DER/BOND inclusion), lots, tick sizes, sessions, auctions, holidays, price limits and corporate actions.
- Starting capital/reporting currency (likely VND but not yet confirmed), cash/settlement rules, commissions, taxes, slippage and fee schedule provenance.
- Backtest strategy boundary and fill model; no lookahead, survivorship or use of revised data before it became available.
- Paper order types, partial fills, queue/liquidity approximation, behavior during feed gaps and restart/recovery.
- CSV schema and storage encryption/backup/export/reset policy.

See [SSI market research](../03-market-research/vn-equities.md) and [roadmap](../../task/next-plan.md). Binance Spot/USDT ledger specifics previously in this folder are superseded and must not be used as V1 assumptions.

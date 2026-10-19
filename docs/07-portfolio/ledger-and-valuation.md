# Portfolio simulator contract

**Trạng thái:** product scope accepted; detailed accounting, market and simulation rules are not yet decided. The former Binance/USDT weighted-average ledger design is superseded, not an active contract.

Portfolio state is stored locally and independent from SSI account/trading balances. Use exact decimal arithmetic for money, price, quantity, tax and fees. Every record has local portfolio ID, instrument identity, event time, recorded/available time, source/assumptions and schema version. Do not represent an estimated value as a broker-reported balance.

## Backtesting

Backtest replays an immutable historical snapshot and a versioned strategy/rule configuration. It must record the SSI source/snapshot manifest, instrument universe, data availability cutoff, timezone/session calendar, starting capital, fill model, fees, taxes, slippage and engine version. Corrected data creates a new run/version; it does not silently rewrite old results.

The engine must prevent lookahead: a decision at time `t` can use only data whose source availability is at or before `t`. Missing/partial data stays missing and affects coverage. Backtests must account for Vietnam market sessions, auctions, price bands, lot/tick sizes, suspended/delisted instruments and corporate actions once those rules are specified. Do not claim realistic returns until the relevant market mechanics are implemented and tested.

## Paper live trading

Paper live trading consumes an entitled SSI Data feed and local market state, then simulates user-created orders/fills. It has no route or credential for real order execution. Each simulated order/fill must record `simulated=true`, market event time, local received time, feed identity, fill-model version, price source, fee assumptions and any stale/gap condition. Stream updates do not prove executable liquidity; the simulator must state its approximation and must not silently fill at a stale/indicative price.

App restart must preserve a consistent paper ledger or recover to a clear interrupted/unknown state. During missing feed, market halt, closed session or local service failure, block or explicitly pause simulated orders according to a policy the user can see.

## Decisions before implementation

- Portfolio base/reporting currency and VND cash/settlement behavior.
- Supported asset classes and board/instrument identity.
- Trade, cash, tax, fee, transfer and corporate-action event types.
- Average-cost vs other accounting method; realized/unrealized P&L and treatment of dividends/rights.
- Historical and live fill models: order types, tick/lot rounding, queue/depth assumptions, partial fills, slippage and price limits.
- Strategy interface/backtest UX and whether users define strategies through forms, built-ins or code (arbitrary code is not assumed).
- Valuation source/freshness and handling of suspended, delisted, stale or missing instruments.

No defaults should be inferred from prior USDT examples. See [product scope](../01-product/vision-and-scope.md), [SSI source gate](../03-market-research/source-register.md) and [MVP roadmap](../../task/next-plan.md).

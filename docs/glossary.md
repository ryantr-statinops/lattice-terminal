# Glossary — Research Terminal

**Trạng thái:** definitions for local-first Vietnam research product; some capabilities are not implemented.

| Term | Standard definition |
|---|---|
| Asset | Economic asset/security category; distinct from a trading instrument or ticker |
| Instrument | Tradable/listed product identified by venue, board/market type, instrument class, native symbol and lifecycle |
| Venue / board | Exchange and board/market label such as HOSE, HNX, UPCOM; DER/BOND require distinct product semantics |
| Candle / OHLC | Time-bucketed open/high/low/close and volume/value with source, interval, session/time fields and closed/provisional state |
| Quote / live price | Provider observation for display/simulation with source and event/receive times; not proof of executable fill |
| Paper order/fill | Local simulated order/fill record; never submitted to a broker |
| Backtest | Deterministic historical replay against a versioned snapshot, assumptions and simulator version |
| Article / event | Source article/evidence and a related interpreted event; retains revisions and confidence |
| `published_at` | Source-declared publication time; may be missing or wrong |
| `first_seen_at` | First time the local engine observed an item; not backdated during backfill |
| `available_at` | Conservative time at which the data could have been known under documented evidence/policy |
| `updated_at` | Correction/update time; does not overwrite prior availability history |
| Dataset snapshot | Versioned local data set with manifest, source revisions, coverage and rights reference |
| SSI FastConnect Data | SSI market-data product; separate from FastConnect Trading |
| Local profile | User-owned data/config boundary on one installation; profile count and password protection are pending design |
| Portfolio | Local ledger plus backtest/paper simulation state; not an SSI/broker account |
| Model Lab | Later experiment/model runtime, outside first MVP |
| News engine | Separate future project for international and Vietnamese news, to integrate later |

## Invariants

- No venue/board/asset-class mixing without explicit normalization rules; tickers alone are not identities.
- Store instants in UTC; UI defaults to Asia/Ho_Chi_Minh with timezone shown.
- Preserve provider timestamp/value and source availability separately from local receive time.
- Missing/unsupported/stale/partial data is not zero and must not be forward-filled into a fictitious bar.
- A live quote does not prove a backtest price or paper fill; paper output is always labeled simulated.
- Credentials and all user data remain local in V1; localhost is not a security boundary or encryption.
- Source flags `documented`, `access-tested`, `rights-confirmed` and `approved` require distinct evidence.
- No FastConnect Trading credentials or real order routes in V1.

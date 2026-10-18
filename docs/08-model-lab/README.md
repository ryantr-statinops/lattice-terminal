# Model Lab

**Trạng thái:** explicitly deferred outside the first MVP by product decision 2026-10-18. Current form/results are mock UI. There is no training runtime.

The first MVP still needs portfolio backtesting, but that is a bounded simulator capability owned by [Portfolio](../07-portfolio/README.md). It does not imply strategy training, model selection, feature lab, arbitrary Python, Pyodide or experiment management.

The documents in this folder preserve candidate feature/runtime/evaluation ideas for a later phase. They currently describe Binance, browser workers and hosted experiment ownership in places; those assumptions are not active requirements and must be reconsidered after SSI local data and portfolio MVP stabilize.

Future Model Lab work must use entitled, versioned local snapshots; prevent lookahead/leakage; record runtime and data provenance; and keep user code execution out of scope unless separately reviewed. See [roadmap](../../task/next-plan.md).

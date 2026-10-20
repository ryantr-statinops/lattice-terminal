# Component inventory

**Tóm tắt:** Bảng dưới ghi nhận component đã có trong repo; không phải danh sách capability production đã được nghiệm thu.


| apps/web/src | Responsibility |
|---|---|
| App.tsx | Auth, routes, lock, theme |
| Market.tsx | Synthetic explorer/watchlist/candles/table |
| Quant.tsx / Plot.tsx | Indicators / lazy local 2D charts |
| Workspace.tsx | Sidebar tree/editor/results, buffers, save/run/history/SSE |
| CodeEditor.tsx | Local Monaco/workers, search and AST entry diagnostics |
| BacktestWorkspace.tsx | Separate detailed-tape Train/Test configuration |
| StrategiesWorkspace.tsx | Callback program / allocation / explicit replay |
| Assets.tsx | Named funds, budgets, Manual, interrupted-book reconciliation |
| Portfolio.tsx | Flows/NAV/positions, settled trade/CSV preview/apply/export |
| Settings.tsx | Evidence / CLI guidance |
| theme.ts | Dark/light preference and chart/editor updates |

No file tabs, debugger, embedded shell/package installer, AI training or 3D renderer. Keyboard/a11y/dense-layout and report visualization needs further polish. [Verification](../13-rebuild/progress.md) is separate from inventory.

Basic side-by-side Backtest report comparison is implemented via RunComparison.tsx, with run/code/data/rule provenance and unavailable metrics. It is not a statistical significance test.

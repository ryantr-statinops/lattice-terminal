# Component inventory

**Summary:** This inventory lists components present in the repository; it does not certify production capabilities.


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
| Providers.tsx | Multi-provider hub, latency ping probes and data routing policy |
| terminal/ | Interactive xterm.js terminal drawer and command shortcuts |
| quant/SurfacePlot3D.tsx | 3D parameter surface optimization visualization |
| theme/ | Semantic palettes, validated preferences, browser store, packaged fonts |
| appearance/ | Presets, font and date/time region controls, grouped colors, contrast, preview and reset |
| ui/ | Shell/login, controls, panels, semantic tables, feedback, dialogs and pane resize |
| workspace/ | File tree, toolbar, history/output, isolated SSE lifecycle |

No file tabs, debugger, embedded shell/package installer, AI training or 3D renderer. Terminal styling, scoped keyboard interactions and async dialogs are implemented; richer report visualization and broader assistive-technology coverage remain. [Verification](../13-rebuild/progress.md) is separate from inventory.

Basic side-by-side Backtest report comparison is implemented via RunComparison.tsx, with run/code/data/rule provenance and unavailable metrics. It is not a statistical significance test.

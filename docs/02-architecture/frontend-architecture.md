# Frontend architecture

**Tóm tắt:** Dùng chung bố cục editor, nhưng Backtest và Strategy không dùng chung contract thực thi. File được quản lý bằng sidebar, không bằng hàng tab.


App.tsx provides current routes. TanStack Query manages server state; React state manages editor controls. Browser calls Go `/api/v1`; direct internal runner endpoints are not proxied.

Workspace.tsx shares presentation, not the Backtest/Strategy execution contract. Separate wrappers supply different configuration/SDKs. Sidebar files, center Monaco, right logs/results/history, resizable panes; no file tabs. In-memory buffers survive route changes, not browser shutdown. Saves and frozen runs differ.

Monaco/worker and Plotly 2D load lazily/local. Market candles use tree-shaken Apache ECharts modules with local Canvas rendering, Vietnamese date labels, crosshair OHLC tooltips and inside zoom; no TradingView attribution logo is used. AST syntax/entry diagnostics exist; no full Python language server, debugger, package installer or terminal. Large lazy editor/Plotly chunks remain a bundle-size concern.

Dark-only Appearance uses versioned browser preferences and semantic CSS variables. IBM Plex Mono/JetBrains Mono are bundled locally. Shared UI components handle dialogs, controls, tables and feedback; feature components retain API ownership. Charts/editor consume the same palette without recreating their view on theme changes. Keyboard/resize and dense-layout interactions are implemented; broader accessibility review and richer reports remain work. [Inventory](../10-ui-ux/component-inventory.md).

Basic side-by-side Backtest report comparison is implemented via RunComparison.tsx, with run/code/data/rule provenance and unavailable metrics. It is not a statistical significance test.

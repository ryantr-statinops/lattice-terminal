# Stack / Toolchain

| Layer | Current choice |
|---|---|
| Web | React 19 / TS 6 / Vite 8 / Tailwind 4 / Router 7 / TanStack Query 5 |
| Go | 1.27.2 / net/http / modernc SQLite / decimal / Argon2id |
| Python | 3.12 / FastAPI / Uvicorn / Pydantic |
| Analytics | NumPy / pandas / TA-Lib; tested exposed indicators |
| Data | Python Parquet/PyArrow, DuckDB in-memory reads |
| Charts | Apache ECharts 6.1.0 candles / Plotly basic 2D reports |
| Editor | Monaco 0.57 ESM/local workers; DOMPurify 3.4.17 override |
| Secrets | Windows Credential Manager CLI |
| Tools | Node 22.23.1 / npm 10.9.8 / uv 0.11.28 |

Exact versions: package-lock.json, go.mod/go.sum, services/engine/uv.lock. Setup uses locks. ECharts is registered from only the candlestick, grid, tooltip, axis pointer, inside zoom and Canvas renderer modules; its Apache license notices are in [third-party notices](../../third-party-notices/echarts/README.md). Plotly basic has no 3D renderer; surfaces/artifact extensions are later work. SciPy/statsmodels/vectorbt are not mandatory dependencies. Fonts use system fallbacks, no CDN.

# Stack / Toolchain

| Layer | Current choice |
|---|---|
| Web | React 19 / TS 6 / Vite 8 / Tailwind 4 / Router 7 / TanStack Query 5 |
| Go | 1.27.2 / net/http / modernc SQLite / decimal / Argon2id |
| Python | 3.12 / FastAPI / Uvicorn / Pydantic |
| Analytics | NumPy / pandas / TA-Lib; tested exposed indicators |
| Data | Python Parquet/PyArrow, DuckDB in-memory reads |
| Charts | Lightweight Charts 4.2 candles / Plotly basic 2D |
| Editor | Monaco 0.57 ESM/local workers; DOMPurify 3.4.17 override |
| Secrets | Windows Credential Manager CLI |
| Tools | Node 22.23.1 / npm 10.9.8 / uv 0.11.28 |

Exact versions: package-lock.json, go.mod/go.sum, services/engine/uv.lock. Setup uses locks. SciPy/statsmodels/vectorbt are not mandatory dependencies. Plotly basic has no 3D renderer; surfaces/artifact extensions are later work. Fonts use system fallbacks, no CDN.

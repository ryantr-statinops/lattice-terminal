# Research Terminal

Open-source, free research infrastructure for Vietnamese users. The V1 direction is to clone this repository and run it locally on Windows, opening the web interface on `localhost`. Market data is intended to come from the user's own SSI FastConnect Data configuration. The current code is still a synthetic-fixture prototype; it is not an operational market terminal and must not be used for investment decisions.

## Product direction

- All configuration, SSI credentials, market data, portfolio records and research outputs stay on the user's machine.
- SSI scope covers applicable FastConnect Data REST, reference-data and streaming capabilities, subject to the user's service entitlement and confirmed usage terms. No FastConnect Trading integration or real-order execution is planned.
- Portfolio MVP target is historical backtesting and paper live trading.
- A separate project news engine for international and Vietnamese sources is planned for later integration.
- Model Lab runtime is outside the first MVP.

## Current prototype

- Market, candles, news and portfolio views use synthetic fixtures or browser-local prototype state.
- The Binance WebSocket control is legacy prototype behavior; it only shows connection state and does not update chart or portfolio.
- Model Lab shows mock UI/results. SSI integration, local login, persistent local storage, backtesting and paper-trading engine are not implemented.

## Run the current frontend prototype

Requirements: Node 22.23.1/npm 10.9.8, Go 1.27.2, Python 3.11–3.13 and uv 0.11.28. These are the current scaffold versions, not a packaged V1 installer.

```powershell
npm ci
npm run dev
```

Open http://127.0.0.1:5173/terminal/news. Routes include `/terminal/market`, `/terminal/news`, `/terminal/portfolio`, `/terminal/model-lab` and `/terminal/account`. To start the fixture API and gateway, see [API](services/api/README.md) and [gateway](services/gateway/README.md).

The frontend proxies `/api` to gateway port 8080; the gateway defaults to API port 8000. Synthetic fixtures are in [data/fixtures](data/fixtures/README.md). Do not enter SSI credentials in the current prototype.

## Checks

```powershell
npm run security:env-boundaries
npm run fixtures:check
npm run test:tooling
npm run test:web
npm run lint
npm run typecheck
npm run build
```

API, OpenAPI drift, research and Go checks run in GitHub Actions. The repository protects `main`; changes go through pull requests.

## Documentation

- [Documentation index](docs/README.md).
- [Product vision and scope](docs/01-product/vision-and-scope.md).
- [SSI FastConnect Data research](docs/03-market-research/vn-equities.md).
- [Current roadmap](task/next-plan.md).

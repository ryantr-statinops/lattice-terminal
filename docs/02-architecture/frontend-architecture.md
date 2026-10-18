# Frontend architecture — Research Terminal

**Status note (2026-10-18):** this file documents the current React fixture implementation and earlier hosted/crypto design. SSI local-first V1 needs a loopback API and must not use direct Binance browser streams or expose SSI credentials. Treat those references below as legacy until revised during implementation.

## Stack (RT-ADR-001, RT-ADR-018)

- React 19 + Vite 8 + TypeScript 6 + Tailwind CSS 4
- React Router 7 (client-side routing)
- TanStack Query 5 (server state) — RT-ADR-016
- Lightweight Charts 4 (financial time series) — RT-ADR-017

## Routing

Routes defined in `apps/web/src/main.tsx`:

| Path | Component | Layout |
|------|-----------|--------|
| `/` | redirect → `/terminal/news` | — |
| `/terminal/market` | `MarketPage` | `AppLayout` |
| `/terminal/news` | `NewsPage` | `AppLayout` |
| `/terminal/portfolio` | `PortfolioPage` | `AppLayout` |
| `/terminal/model-lab` | `ModelLabPage` | `AppLayout` |
| `/terminal/account` | `AccountPage` | `AppLayout` |
| `*` | redirect → `/terminal/news` | — |

Layout: `AppLayout` provides header (nav + theme toggle), footer, skip link. Pages render inside `<Outlet />`.

## State management (RT-ADR-016)

- **Server state:** TanStack Query (`useQuery` with staleTime 30s, gcTime 5min, retry 1, no refetch on focus).
- **Local UI state:** React `useState` (selected instrument, interval, filter, watchlist only, stream enabled).
- **Shareable state:** URL search params (planned; not yet implemented).
- **Global client state:** None (Zustand not introduced; RT-ADR-016 requires demonstrated need).

## Data fetching

- API client: `apps/web/src/lib/api.ts` (`apiFetch<T>`, `apiUrl`).
- Base URL from `VITE_API_BASE_URL` (empty → relative `/api` via Vite proxy).
- Error handling: throw `Error` with server message; components catch via `isError`.
- Loading: `isLoading` → skeleton; `isFetching` (background) → refresh hint.

## Query keys

| Domain | Key | Stale time |
|--------|-----|------------|
| Market instruments | `["market", "instruments"]` | 30s |
| Market candles | `["market", "candles", instrumentId, interval]` | 30s |
| News articles | `["news", "articles", instrumentId]` | 30s |

## WebSocket (Phase 6)

- `useBinanceStream(symbol, interval, enabled)` in `features/market/stream.ts`.
- Public Binance kline stream, no API key.
- Reconnect with exponential backoff (cap 30s).
- Hidden tab grace: mark stale if hidden > 30s.
- Stale detection: no message for 60s while live.
- Only closed candles (`k.x === true`) are considered valid data.

## Web Worker (Phase 7 — planned)

- `workerAdapter.ts` defines `WorkerAdapter` interface.
- Current implementation: `createNoopAdapter()` (synthetic result).
- Future: real Web Worker + Pyodide, lazy-loaded on Run.
- Worker must be terminated on unmount; progress split: download/runtime vs training.

## Local storage

| Key | Purpose | Owner |
|-----|---------|-------|
| `rt-theme` | Dark/light theme | `lib/theme.ts` |
| `rt:watchlist` | Watchlist instrument IDs | `features/market/watchlist.ts` |
| `rt:portfolio` | Holdings + updatedAt | `features/portfolio/storage.ts` |

## File structure

```
apps/web/src/
  main.tsx              Entry point (QueryClientProvider, Router, axe dev)
  App.tsx               (legacy, unused — candidate for removal)
  styles.css            Tailwind v4 + CSS variables (dark/light)
  lib/
    api.ts              API client
    queryClient.ts      TanStack Query client config
    theme.ts            Theme hook + applyTheme
    utils.ts            cn() utility
  components/
    layout/             Container, AppLayout
    ui/                 Button, Dialog, StatusBadge
  features/
    market/             MarketPage, CandleChart, api, watchlist, stream
    news/               NewsPage, api
    portfolio/          PortfolioPage, ManualEntryForm, CsvImport, types, storage
    model-lab/          ModelLabPage, types, workerAdapter
    account/            AccountPage
```

## Build & dev

- Dev: `npm run dev` → Vite on 127.0.0.1:5173
- Proxy: `/api` → Go Gateway 8080 → FastAPI 8000
- Build: `npm run build` → `dist/`
- Typecheck: `npm run typecheck`
- Lint: `npm run lint` (eslint apps/web/src)

# Frontend architecture — Kestrel Terminal

**Trạng thái:** tài liệu mô tả frontend prototype hiện tại; route, query và storage dưới đây không phải API/UI contract V1. V1 yêu cầu browser chỉ gọi local loopback API; SSI secrets và upstream stream thuộc local service sau khi source gates được duyệt.

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

## Streaming prototype

- Prototype hiện có hook kết nối stream upstream từ browser; không dùng thiết kế này làm mẫu cho V1.
- Hook chỉ hoạt động khi được bật và tab đang hiển thị. Khi tab bị ẩn, hook cleanup kết nối và timer ngay, đặt trạng thái về `idle`; không có grace period 30 giây.
- Khi đang hoạt động, hook đánh dấu `stale` nếu quá 60 giây không có message (hoặc không có message sau khi kết nối); bộ kiểm tra chạy mỗi 15 giây.
- Reconnect dùng exponential backoff, tối đa 30 giây.
- Prototype chỉ kiểm tra message có timestamp dạng number, close dạng string và cờ `x` dạng boolean. Cả `true` lẫn `false` đều được chấp nhận để cập nhật trạng thái stream; hook hiện không chuyển candle vào chart hoặc portfolio.
- Đây là trạng thái kết nối prototype, không phải xác nhận chất lượng dữ liệu hay quy tắc candle V1.

## Model Lab mock (deferred)

- `workerAdapter.ts` defines `WorkerAdapter` interface.
- Current implementation: `createNoopAdapter()` (synthetic result).
- Runtime thực không thuộc MVP đầu tiên.
- `terminate()` là interface method của mock; chưa có worker thật để terminate/download/train. Runtime review được hoãn cùng Model Lab.

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
- Build: `npm run build` từ root delegates web workspace → `apps/web/dist/`
- Typecheck: `npm run typecheck`
- Lint: `npm run lint` (eslint apps/web/src)

## V1 implementation gaps

Current routes/storage describe the prototype. The product [sitemap](../01-product/sitemap.md) is a target, not a second implemented router. SSI connection ownership, local auth, durable data store and portfolio simulator are pending. HTML still requests remote fonts as documented in [font delivery](../10-ui-ux/design-tokens.md#font-families); no code migration is performed by these docs.

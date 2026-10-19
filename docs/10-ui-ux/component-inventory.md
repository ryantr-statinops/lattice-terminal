# Component inventory — Research Terminal

Danh sách này ghi nhận frontend prototype hiện tại và các ý tưởng planned; ✅ Có nghĩa là tồn tại trong code, không đồng nghĩa đã đáp ứng V1 hoặc production-ready.

## Layout

| Component | Path | Trạng thái |
|-----------|------|------------|
| `Container` | `components/layout/Container.tsx` | ✅ Có |
| `AppLayout` | `components/layout/AppLayout.tsx` | ✅ Có (header, nav, footer, theme toggle) |

## UI primitives

| Component | Path | Trạng thái | Notes |
|-----------|------|------------|-------|
| `Button` | `components/ui/button.tsx` | ✅ Có | Variants: default, outline |
| `Dialog` | `components/ui/dialog.tsx` | ✅ Có | Portal, backdrop, close |
| `StatusBadge` | `components/ui/StatusBadge.tsx` | ✅ Có | Tones: neutral/success/warning/danger/info |

## Feature components

### Market
| Component | Path | Trạng thái |
|-----------|------|------------|
| `MarketPage` | `features/market/MarketPage.tsx` | ✅ Có |
| `CandleChart` | `features/market/CandleChart.tsx` | ✅ Có (Lightweight Charts) |
| `useInstruments` / `useCandles` | `features/market/api.ts` | ✅ Có |
| `useWatchlist` | `features/market/watchlist.ts` | ✅ Có |
| Browser stream hook | `features/market/stream.ts` | ✅ Prototype only; không phải SSI V1 adapter |

### News
| Component | Path | Trạng thái |
|-----------|------|------------|
| `NewsPage` | `features/news/NewsPage.tsx` | ✅ Có |
| `useArticles` | `features/news/api.ts` | ✅ Có |

### Portfolio
| Component | Path | Trạng thái |
|-----------|------|------------|
| `PortfolioPage` | `features/portfolio/PortfolioPage.tsx` | ✅ Có |
| `ManualEntryForm` | `features/portfolio/ManualEntryForm.tsx` | ✅ Có |
| `CsvImport` | `features/portfolio/CsvImport.tsx` | ✅ Có |
| `usePortfolio` | `features/portfolio/storage.ts` | ✅ Có |

### Model Lab (deferred; mock prototype)
| Component | Path | Trạng thái |
|-----------|------|------------|
| `ModelLabPage` | `features/model-lab/ModelLabPage.tsx` | ✅ Có |
| Types | `features/model-lab/types.ts` | ✅ Có |
| Worker adapter | `features/model-lab/workerAdapter.ts` | ✅ Có (noop) |

### Account
| Component | Path | Trạng thái |
|-----------|------|------------|
| `AccountPage` | `features/account/AccountPage.tsx` | ✅ Có (placeholder) |

## Planned components (not yet implemented)

| Component | Purpose | Phase |
|-----------|---------|-------|
| `InstrumentCard` | Reusable asset card (extract from MarketPage) | Phase 2 polish |
| `EmptyState` | Shared empty state | Phase 2 polish |
| `ErrorState` | Shared error + retry | Phase 2 polish |
| `LoadingSkeleton` | Shared skeleton | Phase 2 polish |
| `FormField` | Label + input + error | Phase 4 polish |
| `FileInput` | CSV file picker | Phase 4 (done inline) |
| `HoldingsTable` | Extract from PortfolioPage | Phase 4 polish |
| `Tooltip` | Provenance/source info | Phase 3 polish |
| `Tabs` | Interval switcher (extract) | Phase 2 polish |
| `Chart` wrapper | Lightweight Charts wrapper | Phase 6 (done inline) |
| `ThemeToggle` | Extract from AppLayout | Polish |
| `Toast` / `Alert` | Error/success/stale notifications | Phase 6 |
| `Watchlist` panel | Dedicated watchlist view | Phase 2 polish |

## Component guidelines

- Use Tailwind utility classes mapped to tokens (`text-fg`, `bg-surface`, `border-border`).
- Never hardcode hex; use CSS variable or Tailwind token (RT-ADR-018).
- All interactive elements: visible focus ring (`focus-visible:outline-2 outline-ring`).
- Reduced motion: respect `prefers-reduced-motion`.
- Color not sole indicator: up/down use text/icon in addition to color.
- Components accept `className` prop for composition (use `cn()` utility).

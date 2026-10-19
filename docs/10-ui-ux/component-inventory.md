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
| `PartialBadge` / `StaleBadge` / `RefreshingIndicator` | `components/ui/PartialBadge.tsx`, `StaleBadge.tsx`, `RefreshingIndicator.tsx` | ✅ Có | Fixture data-quality indicators; không chứng minh SSI quality |

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

## Candidate extractions — not approved implementation tasks

Reusable empty/error/loading UI, form fields, holdings table, instrument cards and a watchlist panel may be extracted if V1 flows need them. Existing inline file input/interval/theme controls are not missing functionality merely because they lack a separate component. `CandleChart` already exists; do not create a duplicate chart wrapper to satisfy an old phase checklist.

No phase numbers or completion claims are assigned here. New components require a product need and inspection of existing primitives. V1 setup/auth, SSI quality and backtest/paper UI remain design gaps rather than approved component names.

## Component guidelines

- Use Tailwind utility classes mapped to tokens declared in `apps/web/src/styles.css` (for example `text-foreground`, `bg-secondary`, `border-border`). `text-fg`, `bg-surface`, and `text-accent` are design-target names, not current stylesheet mappings; add and review the mapping before using them.
- Never hardcode hex; use CSS variable or Tailwind token (RT-ADR-018).
- All interactive elements: visible focus ring (`focus-visible:outline-2 outline-ring`).
- Reduced motion: respect `prefers-reduced-motion`.
- Color not sole indicator: up/down use text/icon in addition to color.
- Components accept `className` prop for composition (use `cn()` utility).

# Frontend plan — Research Terminal

**Status note (2026-10-18):** this plan was written for the previous news-first/Binance/Model Lab direction. It is historical design material, not the current MVP contract. Use [product vision](../01-product/vision-and-scope.md), [local screen flows](screen-flows.md) and [roadmap](../../task/next-plan.md) for current scope; several pages/components below are deferred or need redesign.

Tài liệu này xây dựng kế hoạch frontend hoàn chỉnh cho Research Terminal, tham chiếu quy trình và best practices từ các tài liệu tương tự (trading terminal design, data-dense dashboards, fintech design system). Đây là plan, không phải spec đã lock; mỗi mục cần review trước khi implement.

## 0. Nguyên tắc tổng quát (từ các tài liệu tương tự)

- **Content over chrome** (hypeterminal): UI elements recede, data dominates. Trading terminal đọc giá/P&L ở tốc độ glance.
- **Scannable data** (Lollypop): prices, P&L, positions readable at a glance; clear status positive/negative.
- **Dark by default** (Pixel Show): data-dense tools ship dark first, light là toggle. Semantic colors phải khác nhau theo theme (không dùng cùng hex).
- **Two fonts, not one** (Pixel Show): sans cho prose/UI, mono cho số (tabular numbers).
- **Motion tối giản** (Pixel Show): 3 durations (120/200/350ms) + 1 easing; không stagger/bounce trong trading UI.
- **Token-driven** (fintech design system): mọi styling derive từ tokens, không ad-hoc CSS.
- **Atomic design** (fintech design system): primitives → molecules → organisms → templates → pages.
- **Documentation first-class** (fintech design system): docs là deliverable, không phải afterthought.

---

## 1. Process (tham chiếu Lollypop: Discover → Define → Design → Deliver)

### Phase A — Discover
- Behavioral research: retail trader VN intraday vs swing, news-first workflow.
- System-level data mapping: portfolio states, live market feeds, execution events, news provenance.
- Authority clarification (UIReady): instruments/markets supported, delayed vs real-time, entitlements, order types, pre-trade risk, desktop density, mobile scope, multi-window, regulatory audit, recovery objectives.
- **Output:** user personas (intraday/swing/learner), journey maps, data flow diagram.

### Phase B — Define
- Information architecture: routes, navigation hierarchy, content priority.
- Component inventory: atoms → molecules → organisms.
- Token taxonomy: color, typography, spacing, motion, elevation.
- **Output:** sitemap, component list, token spec draft.

### Phase C — Design
- Token-based design system (dark + light), reusable components, chart modules.
- Reusable components + Storybook/preview.
- Responsive: desktop (dense), tablet, mobile (news/portfolio/report first).
- **Output:** Figma/design spec + token JSON + component code.

### Phase D — Deliver
- Production-ready specs: loading states, stale-data guardrails, latency handling, partial-fill logic, instant confirmation.
- Accessibility: keyboard, focus, semantic labels, screen-reader tables, reduced motion.
- **Output:** implemented components + tests + docs.

---

## 2. Design Tokens

### 2.1 Color (tham chiếu Pixel Show + hypeterminal)

**Nguyên tắc:** dark by default; semantic colors khác nhau theo theme (không dùng cùng hex); color + text/icon (không chỉ màu).

**Surfaces (dark default):**
```
--bg-void:        #0a0a0a   (page background)
--bg-primary:     #111111   (main surface)
--bg-secondary:   #161616   (panel)
--bg-surface:     #1c1c1c   (card/elevated)
--bg-hover:       #222222
--bg-active:      #2a2a2a
```

**Surfaces (light):**
```
--bg-void:        #fafbf9
--bg-primary:     #ffffff
--bg-secondary:   #f4f6f5
--bg-surface:     #eef1ef
--bg-hover:       #e8ece9
--bg-active:      #e0e5e1
```

**Text:**
```
--fg:             100% opacity (primary data, prices, P&L)
--fg-muted:       ~60% (labels, timestamps)
--fg-subtle:      ~40% (hints, disabled, metadata)
```

**Semantic (dark / light — khác hex):**
```
--color-up:       dark #22c55e  / light #16a34a   (profit, gain)
--color-down:     dark #ef4444  / light #dc2626   (loss)
--color-warning:  dark #f59e0b  / light #d97706
--color-info:     dark #3b82f6  / light #2563eb
--color-neutral:  dark #6b7280  / light #4b5563
```

**Borders:**
```
--border-subtle:  1px solid rgba(255,255,255,0.06)  (dark)
--border-default: 1px solid rgba(255,255,255,0.10)
--border-strong:  1px solid rgba(255,255,255,0.16)
```

**Accent (brand):**
```
--color-accent:   #21684e (giữ từ code hiện tại, cần review)
```
→ Quyết định: giữ xanh lá hiện tại hay chuyển Royal Blue? Cần ADR.

### 2.2 Typography (tham chiếu Pixel Show + hypeterminal)

**Hai font:**
```
--font-sans:  "Inter", "system-ui", sans-serif        (UI, prose, labels)
--font-mono:  "JetBrains Mono", "Fira Code", "SF Mono", Menlo, monospace  (numbers, prices, tables)
```

**Type scale (rem):**
```
--text-2xs: 0.625rem  (10px)  metadata, hints
--text-xs:  0.75rem   (12px)  labels, timestamps, secondary data
--text-sm:  0.875rem  (14px)  body, table cells
--text-base:1rem      (16px)  primary content
--text-lg:  1.125rem  (18px)  section headers
--text-xl:  1.25rem   (20px)  page titles
--text-2xl: 1.5rem    (24px)  hero numbers
```

**Weights:**
```
400 normal   body, data
500 medium   labels, nav
600 semibold prices, key values
700 bold     headers, alerts
```

**Tabular numbers:** `font-variant-numeric: tabular-nums` cho mọi số trong bảng/chart.

### 2.3 Spacing (tham chiếu hypeterminal: 8px base, tighter cho terminal)

```
--space-0.5: 2px   icon padding, tight gaps
--space-1:   4px   inline spacing
--space-1.5: 6px   dense component padding
--space-2:   8px   default padding
--space-3:   12px  component gaps
--space-4:   16px  section padding
--space-6:   24px  major section breaks
--space-8:   32px  panel margins
```

### 2.4 Motion (tham chiếu Pixel Show)

```
--duration-fast:   120ms   button press, toggle
--duration-normal: 200ms   drawer open, modal
--duration-slow:   350ms   page-level route change
--ease-out:        cubic-bezier(0.16, 1, 0.3, 1)
```
- Không bounces trong trading UI (spring chỉ cho marketing site).
- Không stagger list animations trên table render.
- `prefers-reduced-motion: reduce` → disable tất cả transitions/animations.

### 2.5 Elevation

```
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05)
--shadow-md: 0 4px 6px rgba(0,0,0,0.10)
--shadow-lg: 0 10px 15px rgba(0,0,0,0.15)
```
(Dark mode: tăng opacity hoặc dùng border thay shadow.)

---

## 3. Component Architecture (Atomic Design — tham chiếu fintech design system)

### Atoms (primitives)
Button, Input, Select, Checkbox, Radio, Badge, Icon, Spinner, Skeleton, Tooltip, Link, Text, Heading, Divider, Avatar.

### Molecules
FormField (label + input + error), SearchBar, PriceDisplay (value + change + %), StatusBadge (live/stale/reconnecting), IntervalSwitcher (15m/1h/1d), EmptyState, ErrorState, LoadingState, Toast.

### Organisms
InstrumentCard, CandleTable, CandleChart, NewsCard, NewsFeed, HoldingsTable, PortfolioSummary, ModelLabForm, ModelLabResults, Watchlist, AppHeader, AppFooter, TabNav.

### Templates
TerminalLayout (header + nav + main + footer), MarketTemplate, NewsTemplate, PortfolioTemplate, ModelLabTemplate, AccountTemplate.

### Pages
MarketPage, NewsPage, PortfolioPage, ModelLabPage, AccountPage.

---

## 4. Layout & Information Density (tham chiếu hypeterminal + Lollypop)

### Visual hierarchy levels (4 levels)
1. **Maximum** — live prices, P&L totals: `text-sm/base`, `font-semibold`, `--fg`, signal colors.
2. **High** — order details, position sizes: `text-xs/sm`, `font-medium`, `--fg`.
3. **Normal** — labels, descriptions: `text-xs`, `font-normal`, `--fg-muted`.
4. **Low** — timestamps, hints, metadata: `text-2xs/3xs`, `font-normal`, `--fg-subtle`.

### Component density (tham chiếu hypeterminal)
| Component | Padding | Gap |
|-----------|---------|-----|
| Button (sm) | 4px 8px | — |
| Button (default) | 6px 12px | — |
| Input | 6px 8px | — |
| Table row | 4px 8px | — |
| Card | 12px | 8px |
| Panel | 16px | 12px |

### Responsive breakpoints
- **Desktop (>1024px):** dense workspace, multi-panel.
- **Tablet (640–1024px):** 2-column, collapsible panels.
- **Mobile (<640px):** news/portfolio/report first; training mobile chỉ sau benchmark.

### Dark mode
- Default dark; light toggle persisted in localStorage.
- Semantic colors khác hex theo theme (Pixel Show lesson).

---

## 5. State & Lifecycle (đã có trong states-lifecycle.md, tinh chỉnh)

Bổ sung từ Lollypop/UIReady:
- **Stale-data guardrails:** mark stream stale, buffer trong bound, request snapshot, resume sau khi continuous.
- **Latency handling:** reconnecting with backoff, unavailable fallback, no silent proxy bypass.
- **Partial data:** quality flag, exclude incomplete bars from features.
- **Loading states:** skeleton cho data, spinner cho actions, progress cho worker download vs training (tách biệt).
- **Error states:** error summary, retry, cancel, view-only fallback.

---

## 6. Accessibility (tham chiếu design-accessibility.md + Lollypop)

- Color + text/icon (không chỉ màu cho tăng/giảm).
- Keyboard navigation, focus ring rõ (`--color-ring`).
- Semantic labels, error summaries.
- Screen-reader-friendly tables (caption, scope, thead/tbody).
- `prefers-reduced-motion` respect.
- Price updates không làm focus nhảy hoặc screen reader đọc mỗi tick.
- Chart có table/summary thay thế.
- Number formatting vi-VN cho display; chuẩn cho CSV/API.
- Contrast ratio ≥ 4.5:1 (text), ≥ 3:1 (large text/UI).

---

## 7. Implementation status (map với project phases)

| Phase | Frontend deliverable | Tokens/Components needed |
|-------|---------------------|--------------------------|
| **Foundation (implemented)** | Routing shell, shared layout, theme, fixture API, states and badges | Container, Button, Dialog, StatusBadge |
| **Market view (fixture)** | BTC/ETH cards, candle table/chart, interval switcher and watchlist | Card, Table, Tabs, CandleChart |
| **News view (fixture)** | Article cards, asset filters and provenance timestamps | ArticleCard, FilterChips |
| **Portfolio (local prototype)** | Manual/CSV import, localStorage holdings and partial-aware P&L | ManualEntryForm, CsvImport, PartialBadge |
| **Quality and data states (prototype)** | Loading/error/retry, source-age stale and refresh states; contrast still unmeasured | LoadingSkeleton, StaleBadge, RefreshingIndicator |
| **Stream (connection status only)** | Opt-in WebSocket lifecycle/reconnect; no chart or portfolio updates | StatusBadge |
| **Model Lab (mock only)** | Config form and explicitly simulated result; no training/backtest | ModelLabForm, mock adapter |

---

## 8. Deliverables checklist (tài liệu cần tạo)

- [ ] `docs/10-ui-ux/design-tokens.md` — palette + typography + spacing + motion + elevation (lock)
- [ ] `docs/10-ui-ux/component-inventory.md` — danh sách components + props + states
- [ ] `docs/10-ui-ux/screen-flows.md` — cập nhật cho idea mới (đã có target, cần refine)
- [ ] `docs/10-ui-ux/states-lifecycle.md` — đã có, cần bổ sung stale-data guardrails
- [ ] `docs/10-ui-ux/accessibility.md` — đã có (design-accessibility.md), cần refine
- [ ] `docs/02-architecture/frontend-architecture.md` — routing, state management, data fetching, worker adapter
- [ ] `docs/09-api/frontend-data-contracts.md` — API client contract, error handling, loading states
- [ ] Storybook setup (optional, sau khi có ≥5 components)

---

## 9. Quyết định cần lock (ADR)

1. **Dark mode default?** — Recommend: dark default, light toggle (Pixel Show lesson).
2. **Accent color:** giữ xanh lá `#21684e` hay chuyển Royal Blue? — Cần ADR.
3. **Font:** Inter + JetBrains Mono vs system fonts? — Recommend: Inter + JetBrains Mono.
4. **State management:** useState + fetch vs React Query vs Zustand? — Cần ADR.
5. **Chart library:** lightweight-charts vs recharts vs custom? — Cần ADR.
6. **CSS approach:** Tailwind tokens vs CSS variables vs styled-components? — Recommend: Tailwind + CSS variables (đã có).

---

## 10. Nguồn tham chiếu

- hypeterminal design-hierarchy.md — visual hierarchy, typography, spacing, component density.
- Pixel Show data-dense dashboards — dark mode, two fonts, motion system, semantic colors per theme.
- Lollypop trading app design — Discover/Define/Design/Deliver process, transaction flow, stale-data states.
- UIReady financial trading terminal — system design, feed session, gap detection, bounded rendering.
- Melinda Trami fintech design system — atomic design, token infrastructure, Storybook, TypeScript APIs.
- Carbon Design System, Material Design 3 — enterprise design system reference.
- GOV.UK Design Guide — documentation-as-first-class reference.

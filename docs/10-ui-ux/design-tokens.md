# Design tokens — Research Terminal

Tokens derived from RT-ADR-013..018. Components must use semantic tokens, never hardcoded hex.

## Theme (RT-ADR-013)
- **Default:** dark. Light supported via semantic token swap.
- Toggle persisted in `localStorage` key `rt-theme` (`dark` | `light`).
- Apply via `data-theme` attribute on `<html>`; CSS variables switch under `[data-theme="light"]`.

## Color tokens (RT-ADR-014)

### Surfaces
```
--bg-void:        dark #0a0a0a  / light #fafbf9
--bg-primary:     dark #111111  / light #ffffff
--bg-secondary:   dark #161616  / light #f4f6f5
--bg-surface:     dark #1c1c1c  / light #eef1ef
--bg-hover:       dark #222222  / light #e8ece9
--bg-active:      dark #2a2a2a  / light #e0e5e1
```

### Text
```
--fg:             dark 100%     / light #182923
--fg-muted:       dark ~60%     / light #57685e
--fg-subtle:      dark ~40%     / light #8a9a90
```

### Accent (brand) — RT-ADR-014
```
--color-accent:   #21684e   (same both themes; review contrast on light)
--color-accent-foreground: #ffffff
```

### Market signals (separate from accent) — RT-ADR-014
```
--color-up:       dark #22c55e  / light #16a34a
--color-down:     dark #ef4444  / light #dc2626
--color-warning:  dark #f59e0b  / light #d97706
--color-info:     dark #3b82f6  / light #2563eb
--color-neutral:  dark #6b7280  / light #4b5563
```
Rule: color + text/icon, never color alone (accessibility).

### Borders
```
--border-subtle:  dark rgba(255,255,255,0.06) / light #d7e0da
--border-default: dark rgba(255,255,255,0.10) / light #c4d0c8
--border-strong:  dark rgba(255,255,255,0.16) / light #a7b8ae
```

### Focus
```
--color-ring:     var(--color-accent)
```

## Typography (RT-ADR-015)

### Font families
```
--font-sans: "Inter", "system-ui", -apple-system, "Segoe UI", sans-serif
--font-mono: "JetBrains Mono", "Fira Code", "SF Mono", Menlo, monospace
```
V1 serves bundled, license-reviewed font assets from local runtime or uses system fallbacks; no runtime CDN font request. `font-display: swap` applies if bundled webfonts are selected. This permits local UI rendering without a font network dependency, not offline SSI data access.

**Prototype gap:** `apps/web/index.html` currently links Google Fonts/preconnect. Those links are existing code behavior and do not satisfy this V1 policy. This docs change does not bundle fonts or modify the HTML; a later implementation change must remove the runtime external requests.

### Type scale (rem)
```
--text-2xs: 0.625rem  (10px)  metadata, hints
--text-xs:  0.75rem   (12px)  labels, timestamps, secondary data
--text-sm:  0.875rem  (14px)  body, table cells
--text-base:1rem      (16px)  primary content
--text-lg:  1.125rem  (18px)  section headers
--text-xl:  1.25rem   (20px)  page titles
--text-2xl: 1.5rem    (24px)  hero numbers
```

### Weights
```
400 normal   body, data
500 medium   labels, nav
600 semibold prices, key values
700 bold     headers, alerts
```

### Rules
- `font-variant-numeric: tabular-nums` on all numeric data in tables/charts.
- UI text uses `--font-sans`; prices/quantities/timestamps use `--font-mono`.

## Spacing (8px base, tighter for terminal)

```
--space-0.5: 2px
--space-1:   4px
--space-1.5: 6px
--space-2:   8px
--space-3:   12px
--space-4:   16px
--space-6:   24px
--space-8:   32px
```

## Motion (RT-ADR-018 — minimal)

```
--duration-fast:   120ms   button press, toggle
--duration-normal: 200ms   drawer open, modal
--duration-slow:   350ms   page-level route change
--ease-out:        cubic-bezier(0.16, 1, 0.3, 1)
```
- No bounces in trading UI (spring only for marketing site).
- No staggered list animations on table render.
- `prefers-reduced-motion: reduce` → disable all transitions/animations.

## Elevation

```
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05)
--shadow-md: 0 4px 6px rgba(0,0,0,0.10)
--shadow-lg: 0 10px 15px rgba(0,0,0,0.15)
```
Dark mode: increase opacity or use borders instead of shadows.

## Breakpoints

```
--bp-mobile:  640px   (max-width)
--bp-tablet:  1024px  (max-width)
--bp-desktop: 1025px  (min-width)
```

## Component guidelines (RT-ADR-018)

- Components use Tailwind utility classes mapped to tokens (`text-fg`, `bg-surface`, `border-border`).
- Never hardcode hex in components; use CSS variable or Tailwind token.
- Semantic color usage: `text-up`/`text-down` for market signals; `text-accent` for brand actions.
- All interactive elements: visible focus ring (`focus-visible:outline-2 outline-ring`).
- Reduced motion: respect `prefers-reduced-motion`.

## State definitions (loading/refreshing/stale/error/empty/partial)

| State | Visual treatment | Component responsibility |
|-------|-----------------|--------------------------|
| **Loading** | Skeleton placeholders matching final layout | Show skeleton; no spinner for data fetch |
| **Refreshing** | Subtle progress indicator (top bar or inline) | Keep existing data visible; show refresh hint |
| **Stale** | Muted styling + "stale" badge with valuation time | Display data with stale label; limit P&L claims |
| **Error** | Error summary + retry button; keep last good data if available | Show error state; offer retry |
| **Empty** | Empty state with explanation + CTA (e.g., "No holdings yet") | Show illustration + action |
| **Partial data** | Quality flag badge; exclude incomplete bars from features | Show available data with partial flag |

### Implementation rules
- TanStack Query `isLoading` → Loading (skeleton).
- TanStack Query `isFetching` (background) → Refreshing (keep data, show hint).
- TanStack Query `isError` → Error (retry).
- Custom `isStale` flag (from API or client) → Stale badge.
- Empty array → Empty state.
- Partial data flag from API → Partial badge, exclude from features.

## Chart cleanup (RT-ADR-017)

TradingView Lightweight Charts components must:
- Store chart instance in `useRef`.
- Create chart in `useEffect` with empty dependency array.
- Return cleanup function that calls `chart.remove()` and unsubscribes all series.
- Remove event handlers (`subscribeCrosshairMove`, etc.) in cleanup.
- Handle resize via `ResizeObserver`, disconnect in cleanup.
- Never create chart in render body.

Example pattern:
```tsx
useEffect(() => {
  const chart = createChart(containerRef.current, options);
  const series = chart.addCandlestickSeries();
  // subscribe data...
  const ro = new ResizeObserver(() => chart.applyOptions({ width: containerRef.current.clientWidth }));
  ro.observe(containerRef.current);
  return () => {
    ro.disconnect();
    chart.remove();
  };
}, []);
```

## Accessibility checklist (verification)

- [ ] Keyboard navigation: all interactive elements reachable via Tab.
- [ ] Focus visibility: `focus-visible` outline on all focusable elements.
- [ ] Contrast: ≥4.5:1 for text, ≥3:1 for large text/UI components (test both themes).
- [ ] Reduced motion: `prefers-reduced-motion: reduce` disables transitions/animations.
- [ ] Screen reader: semantic HTML, ARIA labels where needed, table captions.
- [ ] Color not sole indicator: up/down use icon/text in addition to color.
- [ ] Number formatting: vi-VN display, standard for CSV/API.

## CSS approach (RT-ADR-018)

- Tailwind v4 with `@theme inline` for token mapping.
- CSS variables defined in `:root` (dark) and `[data-theme="light"]`.
- Components use Tailwind classes referencing tokens (`bg-primary`, `text-fg`, `border-border`).
- No hardcoded hex in component files (enforced by lint rule if added).
- Tailwind config in `apps/web/src/styles.css` (v4 CSS-first config).

# Design tokens / Current

Dark default, light toggle in header. HTML data-theme and kestrel.theme preference. Accent #21684e is separate from market up/down colors. Current CSS exposes --accent/--surface/--border/--muted with semantic classes; it does not expose the old prototype's generated --color-* inventory.

Font stacks request Inter/system-ui/sans-serif and JetBrains Mono/monospace; use system fallback if not locally installed. No runtime CDN. Packaging fonts later requires license review.

Charts and Monaco switch light/dark locally. Semantic token consolidation, full contrast/keyboard/resize review remain polish work; an intended token is not a declared utility. Plotly basic does not provide 3D surfaces.

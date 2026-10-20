# Terminal UI redesign

Implement the approved terminal-black design directly on main, one reviewable task per commit. Do not push; publish a local review report and screenshots first. Existing routes, sidebar layout, file/editor/output workspace and all backend contracts remain authoritative.

## Visual contract

IBM Plex Mono (default), JetBrains Mono alternative; packaged local fonts. UI 12/13/14px, default 13px; editor 12–18px. Flat panels, 1px separators, neutral controls, compact tables, no decorative cards. Desktop and tablet retain the current layout. Financial decimals remain strings. Source, fixture and unavailable labels stay visible.

## Appearance

Terminal Black, Graphite and Midnight presets. Editable semantic roles for surfaces, text, borders, interactions, financial states and four chart series. Changes apply and persist immediately in versioned browser storage, independently of authentication. Invalid storage falls back safely. Warn on poor contrast; preserve chart/editor state when restyling. Settings contains Appearance before source evidence. Remove light mode.

## Delivery

Follow approved tasks 01–45: documentation; fonts; tokens; preference model/store; primitives; Appearance; shell/login; chart/editor adapters; individual business screens/dialogs; workspace extraction/interaction; responsive and accessibility review; documentation. Include relevant tests in each task. Additional fixes receive separate commits. Keep commits buildable; do not amend, squash or include unrelated work.

## Acceptance

Typecheck, lint, web regression tests and production build. Exercise Appearance persistence/reset/storage errors, dialog keyboard and pending behavior, workspace buffers/run switching/SSE/resize, decimal and CSV invariants. Review all screens at desktop/tablet widths, loading/error/empty states and Vietnamese fonts. Record exact verification and limitations in the final review report; do not claim unexecuted checks passed.

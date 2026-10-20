# Terminal design tokens

Accepted 2026-10-20. Dark-only presets and immediate local customization replace the earlier green/light theme. Source of truth: [tokens](../../apps/web/src/theme/tokens.ts), [preferences](../../apps/web/src/theme/preferences.ts), [store](../../apps/web/src/theme/store.ts).

## Typography and spacing

IBM Plex Mono is the default; JetBrains Mono is optional. Both are packaged locally through pinned Fontsource 5.3.0 packages, with Latin, extended Latin and Vietnamese WOFF2 subsets, weights 400/500/600 and italic. Licenses are in [IBM notices](../../third-party-notices/ibm-plex-mono/LICENSE) and [JetBrains notices](../../third-party-notices/jetbrains-mono/LICENSE). No runtime CDN.

UI size 12/13/14px (13 default); editor 12–18px (13 default), ligatures off. Page title 16px; panel title 13px. Spacing 4/8/12/16px; control minimum 28px; table rows approximately 24px, growing when text wraps. Flat panels, 1px separators, 0–2px corners. Decimal strings are formatted without conversion to Number.

## Color roles

| Group | Roles | Terminal Black |
|---|---|---|
| Surfaces | canvas / panel / raised / input | #000000 / #0B0B0B / #151515 / #101010 |
| Borders | border / borderStrong | #2C2C2C / #555555 |
| Text | text / secondary / muted | #EEEEEE / #B8B8B8 / #929292 |
| Interaction | accent / focus / hover | #4DB5FF / #8BD0FF / #202020 |
| Selection | selection / selectionText | #383838 / #FFFFFF |
| Semantic | positive / negative / warning / info | #00D17B / #FF4D4F / #FFD000 / #4DB5FF |
| Chart | series1 / series2 / series3 / series4 | #E6E6E6 / #4DB5FF / #FFD000 / #B99AFF |

Graphite and Midnight override surfaces and interaction shades; other roles inherit Terminal Black. Editor syntax, completion/hover surfaces, chart grid/tooltips, notices and disabled states derive from these roles. Editing a color changes the preset label to Custom. Individual reset uses the current preset, or Terminal Black when Custom.

## Appearance storage

Settings → Appearance auto-applies valid changes and writes `kestrel.appearance.v1`. Invalid or obsolete data uses safe defaults; old `kestrel.theme` light/dark preferences no longer control presentation. Preferences apply before React renders, survive session lock and synchronize between tabs. Storage failure retains in-session settings with an explicit notice.

HEX drafts are editable until complete; only six-digit HEX colors apply. Low contrast warns without rejecting customization. Reset-all requires confirmation. Preset text colors are tested at AA contrast against all preset surfaces. Charts update without reinitializing their view; Monaco retains models and per-file view state.

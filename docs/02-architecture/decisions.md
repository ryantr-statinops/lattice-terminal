# Architecture decisions

**Trạng thái:** quyết định mục tiêu, chưa triển khai; thay thế ADR rental trong Git history.

| ID | Quyết định | Trạng thái |
|---|---|---|
| RT-ADR-001 | React/Vite/React Router/TypeScript/Tailwind; UI tiếng Việt | Accepted |
| RT-ADR-002 | Go Gateway + FastAPI là target domain boundary | Superseded as product target; current scaffold only. Local process architecture to be selected |
| RT-ADR-003 | Go ingestion theo lịch, độc lập phiên người dùng | Superseded for hosted scheduler; local ingestion jobs remain a possible implementation |
| RT-ADR-004 | Browser Web Worker training/backtest; Pyodide là phương án spike đầu tiên | Deferred with Model Lab; portfolio backtest is a separate MVP capability |
| RT-ADR-005 | Provider/instrument universe and intervals of the early prototype | Superseded by Vietnam-market direction; not a V1 provider decision |
| RT-ADR-006 | Browser-owned public prototype stream | Superseded; any SSI stream must be owned by an approved local service and reconciled |
| RT-ADR-007 | PostgreSQL cho metadata/ledger; object storage cho snapshots/artifacts qua interface | Superseded by local-only storage direction; exact format/engine pending |
| RT-ADR-008 | Managed Auth, không tự lưu/hash password | Superseded by requested password-only local login; local security/recovery design pending |
| RT-ADR-009 | Early prototype portfolio accounting assumptions | Superseded; Vietnam instruments, backtest and paper live are the target; contract pending |
| RT-ADR-010 | Experiment/results private theo owner; browser output là client-computed | Deferred with Model Lab and hosted accounts |
| RT-ADR-011 | Vercel web/HTTP APIs sau kiểm chứng; ingestion chạy riêng | Superseded; clone-and-run local on Windows, no hosted runtime |
| RT-ADR-012 | Multi-market research scope | Superseded: Vietnam + SSI FC Data is selected direction; exact markets/instruments remain gated |
| RT-ADR-013 | Dark mode default; light theme qua semantic tokens | Accepted (frontend) |
| RT-ADR-014 | Accent `#21684e`; semantic accent tokens + market up/down colors riêng | Accepted (frontend) |
| RT-ADR-015 | Inter (UI) + JetBrains Mono (numeric/terminal) với fallback stacks | Accepted (frontend) |
| RT-ADR-016 | TanStack Query (server state) + React state (local UI) + URL params (shareable); không Zustand nếu chưa có nhu cầu chứng minh | Accepted (frontend) |
| RT-ADR-017 | TradingView Lightweight Charts cho financial time series; kiểm tra deps/component hiện có trước migrate | Accepted (frontend) |
| RT-ADR-018 | Tailwind CSS + CSS variables; semantic tokens, không hardcode theme colors trong components | Accepted (frontend) |

## Current direction decisions (2026-10-18)

| ID | Quyết định | Trạng thái |
|---|---|---|
| RT-ADR-019 | Open-source/free local-first V1, clone repo và chạy localhost trên Windows; không cần installer/hosted backend | Accepted product direction; launcher/process details pending |
| RT-ADR-020 | SSI FastConnect Data là provider direction; dùng REST/reference/stream capabilities phù hợp sau entitlement/rights gates; không dùng FastConnect Trading | Accepted direction; account, terms, quota, fields and retention not yet verified; network use remains blocked |
| RT-ADR-021 | Dữ liệu, config, credentials, portfolio và research output ở máy người dùng | Accepted requirement; secret store, encryption, storage format, backup/delete remain pending |
| RT-ADR-022 | Password-only local login | Accepted UX requirement; local profile model, password hashing, recovery and at-rest protection pending |
| RT-ADR-023 | Portfolio MVP includes historical backtest and paper live trading only; no real orders | Accepted product scope; fills, fees, taxes, market sessions and corporate actions pending design |
| RT-ADR-024 | News engine for international and Vietnam sources is a separate workstream, integrated later | Accepted sequencing; source rights/engine requirements pending |
| RT-ADR-025 | Model Lab runtime is outside first MVP | Accepted scope |
| RT-ADR-026 | Cân nhắc storage engine local cho market data và ledger | Proposal only; format, concurrency and recovery not evaluated |
| RT-ADR-027 | Cân nhắc launcher/process supervision Windows | Proposal only; runtime process topology and shutdown not selected |
| RT-ADR-028 | Cân nhắc Windows secret storage for SSI credentials | Proposal only; threat model and recovery not reviewed |

## Spike và quyết định tiếp theo

Các việc kế tiếp: xác minh user's SSI service entitlement and terms; chốt market/feed scope and field semantics; thiết kế local secret/persistence/password recovery; định nghĩa portfolio backtest/paper contracts; chốt local process launcher/setup. Model Lab/Pyodide, hosted auth/database/storage và cloud deployment không nằm trong first MVP.

ADR tiếp theo ghi owner, ngày, alternatives, rationale, evidence, impact và trigger xem lại. Không đổi tên thư mục repo/domain deploy trong docs.

## Frontend ADRs (locked 2026-10-17)

### RT-ADR-013 — Dark mode default
- **Quyết định:** Dark by default; light theme supported through semantic design tokens.
- **Rationale:** Data-dense tools ship dark first (Pixel Show). Semantic tokens cho phép switch theme mà không đổi hex trong components.
- **Impact:** Cần token system với dark/light variants; components chỉ dùng token, không hardcode.
- **Trigger xem lại:** user research cho thấy light-first demand cao.

### RT-ADR-014 — Accent color
- **Quyết định:** Keep `#21684e`; define semantic accent tokens và separate market up/down colors.
- **Rationale:** Giữ palette hiện tại (đang dùng trong styles.css), tránh migration. Market up/down dùng semantic colors riêng (--color-up/--color-down) khác accent.
- **Impact:** Cần tách accent (brand) khỏi up/down (market signal).
- **Trigger xem lại:** rebrand hoặc accessibility contrast failure.

### RT-ADR-015 — Typography
- **Quyết định:** Inter cho UI, JetBrains Mono cho numeric/terminal data, với fallback stacks.
- **Rationale:** Two-font split (Pixel Show): tabular numbers cần mono, prose/UI cần sans. Fallback stacks đảm bảo offline/CI.
- **Impact:** Cần load fonts (self-hosted hoặc CDN với fallback). Components dùng `--font-sans` / `--font-mono`.
- **Trigger xem lại:** font loading performance issue.

### RT-ADR-016 — State management
- **Quyết định:** TanStack Query (server state) + React state (local UI) + URL params (shareable); không Zustand nếu chưa có nhu cầu chứng minh.
- **Rationale:** Tách rõ server cache vs local UI vs shareable state. Tránh thêm dependency chưa cần.
- **Impact:** Cần thêm `@tanstack/react-query` khi implement data fetching (Phase 2). URL params cho filters (instrument, interval).
- **Trigger xem lại:** demonstrated need cho global client state (e.g., complex cross-component UI state).

### RT-ADR-017 — Charts
- **Quyết định:** Prefer TradingView Lightweight Charts cho financial time series. Inspect existing deps/components trước khi migrate; tránh migration không cần thiết.
- **Rationale:** Lightweight Charts tối ưu cho candlestick time series, bundle nhỏ. Hiện chưa có chart component nào, nên không có migration cost.
- **Impact:** Thêm dependency khi implement candle chart (Phase 2). Components phải cleanup subscriptions/event handlers.
- **Trigger xem lại:** bundle size hoặc feature gap (e.g., cần indicator overlays không support).

### RT-ADR-018 — CSS approach
- **Quyết định:** Tailwind CSS + CSS variables; semantic tokens, không hardcode theme colors trong components.
- **Rationale:** Đã dùng Tailwind + CSS vars. Lock để tránh drift. Components dùng token classes (`text-primary`, `bg-surface`) không hex.
- **Impact:** Cần migrate hardcoded hex (nếu có) sang tokens. Document token usage.
- **Trigger xem lại:** Tailwind v4 breaking changes hoặc design tooling change.

## Local Architecture ADRs (2026-10-19)

### RT-ADR-026 — Local storage engine (proposal)
- **Trạng thái:** chưa chọn engine hoặc physical schema.
- **Cần đánh giá:** workload, process ownership, atomic writes, migration, backup/restore, encryption and cross-language support.

### RT-ADR-027 — Windows process supervision (proposal)
- **Trạng thái:** launcher, process count, health checks and shutdown behavior chưa được chọn.
- **Cần đánh giá:** clean clone setup, loopback binding, child-process cleanup and diagnostic output.

### RT-ADR-028 — Windows secret storage (proposal)
- **Trạng thái:** chưa chọn Windows facility hoặc vault design.
- **Cần đánh giá:** threat model, backup/recovery, profile isolation, process access and secret rotation before accepting credentials.

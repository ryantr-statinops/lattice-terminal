# Architecture decisions

**Trạng thái:** quyết định mục tiêu, chưa triển khai; thay thế ADR rental trong Git history.

| ID | Quyết định | Trạng thái |
|---|---|---|
| RT-ADR-001 | React/Vite/React Router/TypeScript/Tailwind; UI tiếng Việt | Accepted |
| RT-ADR-002 | Go Gateway + FastAPI là target domain boundary | Superseded as product target; current scaffold only. Local process architecture to be selected |
| RT-ADR-003 | Go ingestion theo lịch, độc lập phiên người dùng | Superseded for hosted scheduler; local ingestion jobs remain a possible implementation |
| RT-ADR-004 | Browser Web Worker training/backtest; Pyodide là phương án spike đầu tiên | Deferred with Model Lab; portfolio backtest is a separate MVP capability |
| RT-ADR-005 | Binance Spot BTCUSDT/ETHUSDT; candles 15m/1h/1d | Superseded by Vietnam-market direction; Binance code/docs are prototype legacy |
| RT-ADR-006 | Browser public Binance WebSocket không key, theo tab hoạt động | Superseded; SSI stream must be owned by local service and reconciled |
| RT-ADR-007 | PostgreSQL cho metadata/ledger; object storage cho snapshots/artifacts qua interface | Superseded by local-only storage direction; exact format/engine pending |
| RT-ADR-008 | Managed Auth, không tự lưu/hash password | Superseded by requested password-only local login; local security/recovery design pending |
| RT-ADR-009 | Portfolio spot long/cash, weighted-average cost, base USDT; manual/CSV | Superseded; Vietnam instruments, backtest and paper live are the target; contract pending |
| RT-ADR-010 | Experiment/results private theo owner; browser output là client-computed | Deferred with Model Lab and hosted accounts |
| RT-ADR-011 | Vercel web/HTTP APIs sau kiểm chứng; ingestion chạy riêng | Superseded; clone-and-run local on Windows, no hosted runtime |
| RT-ADR-012 | Funding/OI, cổ phiếu Mỹ, FX, Việt Nam | Superseded: Vietnam + SSI FC Data is selected direction; exact markets/instruments remain gated |
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
| RT-ADR-026 | Cơ sở dữ liệu local: DuckDB (nến/tick time-series OLAP) + SQLite (sổ cái portfolio/orders ACID) | Accepted architecture decision |
| RT-ADR-027 | Quản lý tiến trình Windows cục bộ: Go/PowerShell launcher 1 lệnh khởi động | Accepted architecture decision |
| RT-ADR-028 | Bảo mật thông tin nhạy cảm SSI: Windows DPAPI / Windows Credential Manager | Accepted security decision |

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

### RT-ADR-026 — Local storage engine
- **Quyết định:** Kiến trúc lưu trữ lai (Hybrid Storage): **DuckDB** lưu trữ dữ liệu chuỗi thời gian (Nến OHLCV, Tick Trades, Snapshots) + **SQLite** lưu trữ danh mục tài sản, cấu hình, và sổ lệnh giả lập (Portfolio Ledger, Paper Orders, Local Profiles).
- **Rationale:** Dữ liệu nến và tick đòi hỏi tốc độ truy vấn phân tích (OLAP) và nén dữ liệu dạng cột vượt trội (DuckDB xử lý hàng triệu nến trong vài mili-giây, hỗ trợ đọc trực tiếp file Parquet/DuckDB local). Ngược lại, số dư tài khoản và lệnh giao dịch đòi hỏi tính toàn vẹn giao dịch (ACID transactional) đơn giản và không có overhead (SQLite). Cả hai đều là file-based cục bộ, không cần cài đặt database server riêng biệt.
- **Impact:** Thêm DuckDB driver cho Golang/Python; SQLite file `lattice_ledger.db` và DuckDB file `lattice_market.duckdb` lưu tại thư mục dữ liệu local của người dùng.
- **Trigger xem lại:** Kích thước file dữ liệu vượt quá 50GB hoặc vấn đề khóa file đồng thời giữa các tiến trình.

### RT-ADR-027 — Windows process supervision and launcher
- **Quyết định:** Cung cấp script launcher duy nhất (hỗ trợ `launcher.ps1` và command `go run ./cmd/lattice-terminal`) để khởi động và giám sát đồng bộ cả 3 thành phần: React Web UI, Go Market/Gateway Service, và Python Local Engine.
- **Rationale:** Trải nghiệm người dùng desktop là "Clone & Run". Không yêu cầu người dùng phải tự mở 3 cửa sổ terminal riêng biệt. Launcher quản lý vòng đời, kiểm tra cổng mạng loopback, và tự động dọn dẹp tiến trình con khi người dùng nhấn Ctrl+C.
- **Impact:** Cần viết `scripts/launch.ps1` chuẩn hóa và health-check endpoint cho từng service.
- **Trigger xem lại:** Yêu cầu đóng gói thành file `.exe` cài đặt độc lập (Single-file Desktop executable).

### RT-ADR-028 — Windows secret storage for SSI credentials
- **Quyết định:** Sử dụng **Windows DPAPI (Data Protection API)** hoặc **Windows Credential Manager** để mã hóa và lưu trữ `ConsumerID`, `ConsumerSecret`, và Access Token của người dùng.
- **Rationale:** Ứng dụng chạy trên Windows của người dùng. Tuyệt đối không lưu plaintext credentials vào file `.env` hay lưu trong trình duyệt `localStorage`. DPAPI tận dụng khóa bảo mật gắn liền với tài khoản đăng nhập Windows của người dùng, đảm bảo các phần mềm độc hại không có quyền người dùng không thể đọc trộm khóa.
- **Impact:** Service local Go/Python gọi Windows API để mã hóa/giải mã khóa khi khởi động phiên làm việc.
- **Trigger xem lại:** Mở rộng hỗ trợ hệ điều hành macOS/Linux.

# Technology stack

**Trạng thái:** target đã đổi sang local-first; implementation stack V1 chưa khóa. Code hiện là React/Vite + Go Gateway + FastAPI fixture scaffold.

| Lớp | Hướng V1 | Trạng thái |
|---|---|---|
| Web UI | React, Vite, TypeScript; chạy và mở tại localhost | Scaffold đang có |
| Local API / process | Local process nghe loopback để cung cấp market, portfolio và simulator contracts | Cần chốt giữ Go Gateway + FastAPI hay hợp nhất; không bind public network mặc định |
| SSI adapter | FastConnect Data REST + streaming trong local process; secret không vào browser | Capability documented, entitlement/terms chưa duyệt; chưa implement |
| Local storage | Dữ liệu/config/portfolio/backtest artifacts trên máy user | Format, encryption, backup, migration và delete policy cần ADR |
| Credentials | ConsumerID/ConsumerSecret chỉ được dùng từ backend process local | Chưa chọn OS secret store / encrypted local vault; không lưu plaintext trong repo hoặc browser storage |
| News | Engine độc lập cho nguồn quốc tế và Việt Nam; tích hợp terminal ở phase sau | Chưa chọn stack/hosting/storage; không thuộc market MVP ban đầu |
| Portfolio simulation | Backtest + paper live trading, no broker order routing | Cần thiết kế engine, exchange/session/fee/corporate-action models |
| Model Lab | Ngoài MVP đầu tiên | Deferred; không kéo Pyodide/runtime vào V1 |

V1 hướng clone-and-run trên Windows; không cần desktop shell, installer, managed auth, hosted database, object store hoặc cloud job runner. Chưa chốt số process hay launcher; phải đánh giá vận hành và khởi chạy local trước implementation.

Không dự kiến cloud LLM dependency cho MVP. Phần mềm miễn phí không bảo đảm SSI data service miễn phí; entitlement và chi phí theo tài khoản vẫn chưa xác minh. Font runtime dùng assets local hoặc system fallback. Secret storage cần threat model cho Windows profile, backups, logs, crashes và export; localhost không thay thế authentication/encryption.

Các packages/tool versions đang trong lockfiles; scaffold versions trong root README mô tả prototype hiện tại, không phải cam kết V1 runtime. Thay đổi stack phải cập nhật ADR và setup guide cùng implementation.

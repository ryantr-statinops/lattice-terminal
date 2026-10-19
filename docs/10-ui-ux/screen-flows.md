# Screen flows

**Trạng thái:** luồng UX mục tiêu theo local-first; prototype hiện tại dùng fixtures/mocks và chưa thực hiện đầy đủ các luồng này.

## Local setup and password

First run hướng dẫn cấu hình SSI FastConnect Data qua local service, không đưa credentials vào source/browser. Secret-store flow và password/session design chưa được chọn; chỉ nhận credentials thật qua flow đã review cho đúng scope (authorized probe hoặc approved production use). Password-only login là UX requirement; chưa quyết định nó khóa UI hay tham gia encryption. Không tự hứa vault unlock, recovery hoặc hiển thị secret.

## Market research

Market screens show Vietnamese instruments/reference data supported by the user's SSI entitlement. Identify venue/board, instrument class, source/feed, interval, session/timezone, last observed time, closed/provisional state, coverage gaps, partial/stale/unavailable status and adjustments/revisions when known. Do not present fixtures or fallback sources as SSI data. REST/history is the initial/recovery source; streaming only appears after local connection and reconciliation.

## Portfolio

Luồng mục tiêu cho phép tạo portfolio local, chạy historical backtest và paper live sessions sau khi data source/market assumptions được duyệt. Backtest setup nêu snapshot, range/coverage, strategy, capital/currency và cost/fill assumptions. Paper live thể hiện freshness và mọi order/fill là simulated. Khi feed có gap/stale hoặc session state không rõ, không tạo simulated fill; pause/resume là control mục tiêu nhưng điều kiện tự động pause, lệnh đang chờ, checkpoint và quy tắc resume còn pending trong simulator contract. Prototype hiện chưa có simulator; không hiển thị real-order action hay yêu cầu trading credentials.

## News and deferred model capability

News fixture screen là placeholder. News engine quốc tế/Việt Nam là workstream riêng; terminal chỉ tích hợp sau khi source policy và contract được duyệt. Model Lab ngoài MVP đầu tiên; không trình bày mock metrics như kết quả phân tích thật.

## Local data lifecycle

Explain managed application/browser/secret-store locations once selected. Preview settings reset, data deletion, secret removal and restore as distinct actions; report failures and user-owned backups/exports outside scope. Password reset is not implicit data deletion or key recovery. Follow the [storage inventory](../04-data/storage-and-retention.md#storage-inventory-and-deletion-boundaries). No project upload is enabled by default.

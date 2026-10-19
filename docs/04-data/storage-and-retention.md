# Storage, retention và quyền dữ liệu

**Trạng thái:** local-only là product requirement; storage format, encryption, backup, migration và retention windows cần quyết định. Không có persistence production được xác nhận.

V1 giữ credentials, user config, market snapshots, portfolio, backtest artifacts và paper-trading ledger trên máy người dùng. Không có cloud sync, remote database, object storage hay dịch vụ project nhận payload. App clone/run không đồng nghĩa tất cả dữ liệu đã được mã hóa; password login không thay thế encryption-at-rest.

Trước SSI network integration, phải xác minh service entitlement và terms cho đúng endpoint/fields/use case: local access, caching/retention, export, research/backtest/derived use, display, attribution và deletion. REST historical, reference and streaming rights/limits có thể khác nhau. Giữ source policy evidence và terms version/hash trong local manifests; không lưu ConsumerID/Secret hoặc account identifiers trong manifest.

News engine sẽ là workstream riêng. Chỉ tích hợp fields/content mà source-specific terms cho phép; link/metadata không mặc nhiên cấp quyền full-text, image, translation, ML hoặc retention. News storage/retention contract được chốt ở workstream đó.

## Local data safety requirements

- Secret không nằm trong repository, `.env` được commit, browser localStorage/sessionStorage, URLs, logs, screenshots, telemetry hoặc crash dumps. Chọn Windows secret store/encrypted vault trước khi xin credentials.
- Phân biệt source payload, normalized records, derived research, portfolio simulation data và logs; từng loại cần retention/export/delete policy riêng.
- Publish snapshots atomically sau schema/quality/source gates. Incomplete write không thay snapshot cũ; manifest giữ provenance, checksums, coverage, version và policy reference.
- Local backups/export phải bảo護 secrets independently; docs/setup phải giải thích backup, restore, reset password và delete workspace. Không giả định Windows profile backup tự an toàn.
- Khi permission revoked/terms expire: dừng adapter, chặn serving/export bị ảnh hưởng, đánh dấu local snapshots restricted và đưa ra delete/review procedure. Immutable versioning không có nghĩa được giữ dữ liệu khi terms yêu cầu xóa.
- Local server chỉ bind loopback; không bật network sharing, telemetry hoặc auto-upload mặc định.

Đến khi rights gate pass: chỉ dùng synthetic fixtures, không gọi SSI, không cache/persist market payload thật. [Source register](../03-market-research/source-register.md) sở hữu evidence/approval; data docs không tự nâng source status.

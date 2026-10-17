# Development workflow

**Trạng thái:** fixture prototype workflow đã có; real-data providers và production services vẫn là target.

Từ repository root, cài JS dependencies bằng `npm ci`. Frontend checks: `npm run security:env-boundaries`, `npm run fixtures:check`, `npm run test:tooling`, `npm run test:web`, `npm run lint`, `npm run typecheck` và `npm run build`. API dùng frozen uv lock/pytest và export vào `packages/contracts/openapi.json`; Go dùng `go -C services/gateway test ./...` và `go -C services/ingestion test ./...`.

Local fixture mode không gọi sàn/news provider hoặc dùng credentials, trừ khi người dùng bật Binance connection-health stream trong Market. Stream hiện không cập nhật chart hoặc portfolio. Không dùng fixtures làm bằng chứng nguồn đã được phê duyệt.

OpenAPI/client schema phải thay cùng implementation. Worker/config/artifact schemas cần versioning khi runtime được triển khai. Money dùng decimal contract; browser quotes chỉ phục vụ hiển thị, không chứng minh fill.

Mỗi thay đổi nhỏ cần có commit, phạm vi và verification. Repo bảo vệ `main`: push thay đổi qua PR và chờ required CI checks. Không force-push; rollback bằng `git revert` sau khi xem xét contract/dữ liệu bị ảnh hưởng. Không commit private CSV, raw news lớn, credential hoặc model binaries.

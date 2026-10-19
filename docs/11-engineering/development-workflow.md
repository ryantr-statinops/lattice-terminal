# Development workflow

**Trạng thái:** fixture prototype workflow đã có; real-data providers và production services vẫn là target.

Từ repository root, cài JS dependencies bằng `npm ci`. Frontend checks: `npm run security:env-boundaries`, `npm run fixtures:check`, `npm run test:tooling`, `npm run test:web`, `npm run lint`, `npm run typecheck` và `npm run build`. API dùng frozen uv lock/pytest và export vào `packages/contracts/openapi.json`; Go dùng `go -C services/gateway test ./...` và `go -C services/ingestion test ./...`.

Current fixture mode should be treated as offline synthetic development. The Binance connection-health control is legacy prototype behavior and does not implement the SSI local data boundary; do not use it as V1 evidence or ask users to enter SSI credentials into the current UI. SSI calls remain blocked until the source register gate passes. Fixtures do not prove source access/rights.

Local API/OpenAPI schema must change with implementation. Market adapters, local secrets and portfolio simulator need versioned contracts. Money uses exact decimal rules; a stream quote is an input to paper simulation, not proof of an actual fill. Model Lab Worker/runtime remains deferred.

Mỗi thay đổi nhỏ cần có commit, phạm vi và verification. Repo bảo vệ `main`: push thay đổi qua PR và chờ required CI checks. Không force-push; rollback bằng `git revert` sau khi xem xét contract/dữ liệu bị ảnh hưởng. Không commit private CSV, raw news lớn, credential hoặc model binaries.

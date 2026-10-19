# Development workflow

**Trạng thái:** fixture prototype workflow đã có; real-data providers và production services vẫn là target.

Từ repository root, cài JS dependencies bằng `npm ci`. Frontend checks: `npm run security:env-boundaries`, `npm run fixtures:check`, `npm run test:tooling`, `npm run test:web`, `npm run lint`, `npm run typecheck` và `npm run build`. API dùng frozen uv lock/pytest và export vào `packages/contracts/openapi.json`; Go dùng `go -C services/gateway test ./...` và `go -C services/ingestion test ./...`.

Current fixture mode is offline synthetic development. Browser streaming is prototype behavior, not SSI integration; do not enter SSI credentials into the current UI. Product SSI calls remain blocked. Bounded access tests need separate authorization under the [probe policy](../03-market-research/source-register.md#access-probes-and-operating-states); neither fixtures nor a successful probe prove production/storage rights.

Local API/OpenAPI schema must change with implementation. Market adapters, local secrets and portfolio simulator need versioned contracts. Money uses exact decimal rules; a stream quote is an input to paper simulation, not proof of an actual fill. Model Lab Worker/runtime remains deferred.

Mỗi thay đổi nhỏ cần có commit, phạm vi và verification. Repo bảo vệ `main`: thay đổi sản phẩm thường đi qua PR và required CI checks. Không force-push; rollback bằng `git revert` sau khi xem xét contract/dữ liệu bị ảnh hưởng. Không commit private CSV, raw news lớn, credential hoặc model binaries.

# Testing & quality gates

**Tóm tắt:** Chỉ ghi nhận kết quả đã chạy. Test fixture không chứng minh quyền SSI, tính đúng của luật thật hoặc kết quả CI trên remote.


- npm run typecheck / lint / test:web / build.
- go -C services/gateway test ./...
- uv run --project services/engine pytest
- node scripts/check-docs.mjs: relative Markdown paths/headings.
- node scripts/contracts.mjs: Go response DTO/route drift.
- uv run --project services/engine python scripts/export-engine-contracts.py --check
- On Windows, run `npm ci`, `uv sync --project services/engine --frozen`, create `.cache/bin`, build with `go -C services/gateway build -o ../../.cache/bin/kestrel.exe ./cmd/kestrel`, then run `uv run --project services/engine python scripts/smoke-windows.py`.

Coverage includes decimal/idempotent/concurrent finance, immutable snapshots, interruptions, source gates, causal indicators, detailed quote time/freshness, separate contracts, worker timeout, backup integrity/path bounds, CSV and missing valuation. Frontend tests are components/contracts, not full browser automation.

Windows smoke covers auth/routes/Market/Quant/research artifacts/Train-Test, wrong-kind rejection, Manual/Strategy, lock, CSV, >200 SSE events, stop/restart and backup/restore/new profile. CI config exists; local results don't prove remote CI ran because changes aren't pushed.

No test authorizes SSI or proves real-market fills. Actual provider pagination/gaps, calendars/actions/settlement and rights need evidence and new tests. Exact outcomes/warnings: [progress](../13-rebuild/progress.md).

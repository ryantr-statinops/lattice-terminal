# Current repository structure

```text
apps/web/src/                    React routes, charts, editors and books
services/gateway/cmd/             launcher / maintenance / schema generator
services/gateway/internal/        API, auth, host, secrets, SQLite, workspace, recovery
services/engine/kestrel_engine/   internal API, data, indicators, replay, workers
test/web/                         Vitest suites grouped by UI feature
test/engine/                      Python regression suites and shared path fixtures
test/scripts/                     Node script tests
test/integration/                 cross-service tests
services/gateway/**/_test.go      Go tests kept beside their packages
data/fixtures/                    synthetic instruments/candles/quote tape
contracts/                        generated response/market schemas, routes, internal OpenAPI
scripts/                          smoke, contract and consistency checks
docs/                             requirements, evidence, current/deferred status
```

Local credentials are configured in the ignored repository `.env`; application data defaults to ignored repository `data/` and can be relocated by `KESTREL_DATA_DIR`. Compose mounts these same paths. Build caches/environments are ignored. Former services/api, services/ingestion, old feature folders and browser training workers are not current runtime. Git history preserves them; do not reinstall their dependencies or revive their contracts.

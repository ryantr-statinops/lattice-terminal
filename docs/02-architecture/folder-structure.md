# Current repository structure

```text
apps/web/src/                React routes, charts, editors and books
services/gateway/cmd/        launcher / maintenance / schema generator
services/gateway/internal/  API, auth, host, secrets, SQLite, workspace, recovery
services/engine/kestrel_engine/  internal API, data, indicators, replay, workers
services/engine/tests/      Python regression tests
data/fixtures/              synthetic instruments/candles/quote tape
contracts/                  generated response/market schemas, routes, internal OpenAPI
scripts/                    Windows setup/start/stop, smoke and consistency checks
docs/                       requirements, evidence, current/deferred status
```

User data defaults to `%LOCALAPPDATA%/KestrelTerminal`, outside source. Build caches/environments are ignored. Former services/api, services/ingestion, old feature folders and browser training workers are not current runtime. Git history preserves them; don't reinstall their dependencies or revive their contracts.

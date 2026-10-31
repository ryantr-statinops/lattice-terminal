# Repository Guidelines

## Project Structure & Module Organization

This is a local-first Vietnamese equity research terminal:

- `apps/web/`: React, TypeScript, and Vite user interface.
- `services/gateway/`: Go HTTP gateway and application APIs under `internal/`; Go tests stay beside their packages.
- `services/engine/`: Python engine package in `kestrel_engine/`.
- `test/`: centralized web, Python, and Node test suites. Web tests are grouped by feature; Python tests live in `engine/`; script tests live in `scripts/`. `integration/` is for cross-service tests.
- `data/fixtures/`: synthetic test and preview data. `data/` is local runtime data; do not commit generated data.
- `packages/`, `contracts/`, `docs/`, and root `scripts/`: shared contracts, documentation, and repository checks.

## Build, Test, and Development Commands

Run `npm ci` to install JavaScript dependencies. `npm run dev` starts Vite; follow `README.md` for full-stack Docker Compose setup.

Run relevant checks before submitting:

- Web: `npm run lint`, `npm run typecheck`, `npm run test:web`, `npm run build`.
- Node scripts: `npm run test:dev-ai`.
- Python engine: `uv run --project services/engine pytest -c services/engine/pyproject.toml test/engine`.
- Go gateway: `go -C services/gateway test ./...`.
- Repository checks: `node scripts/check-docs.mjs`, `node scripts/contracts.mjs`, and `npm run check`.

## Coding Style & Naming Conventions

React components use PascalCase; hooks and TypeScript functions use camelCase. Use `*.test.ts[x]` for Vitest, `test_*.py` for pytest, `*.test.mjs` for Node, and `*_test.go` for Go. Go code uses `gofmt`; Python uses `snake_case`. Preserve module boundaries and update shared contracts when API shapes change.

## Testing Guidelines

Vitest discovers `test/web/**/*.test.{ts,tsx}`; use the `@web/` alias for imports from `apps/web/src/`. Pytest fixtures in `test/engine/conftest.py` provide stable repository paths. Keep Go tests in their source package when they need access to unexported internals. Add focused coverage for behavior changes and run that layer's checks.

## Commit & Pull Request Guidelines

Use concise Conventional Commit subjects, such as `feat(scope):`, `fix(scope):`, `test(scope):`, and `docs(scope):`. Pull requests should describe impact, link issues when available, include screenshots for UI changes, and list checks run. Call out contract, configuration, or data handling changes.

## Security & Configuration

Use `.env.example` for setup. Never commit credentials, `.env`, generated data, or provider secrets. Treat the app as fixture-only unless a provider passes documented source and rights gates; live order routing is not implemented.

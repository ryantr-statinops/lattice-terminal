# Local API contracts

**Trạng thái:** V1 should use loopback APIs between the local web UI and local service. Current Go Gateway/FastAPI contracts are fixture scaffold and older hosted/multi-account target; they do not describe an implemented user API.

The V1 API must not require a remote business service, managed auth or cloud database. SSI credentials are used only by a local adapter and must never be sent from browser to SSI. The browser talks to an allowlisted localhost origin; the local process owns upstream auth, source quota and data normalization.

The docs below preserve prior contracts and need revision during implementation:

1. [Auth and HTTP conventions](auth-and-http.md) — hosted JWT behavior is superseded.
2. [Capability contracts](capabilities.md) — workspace/experiment endpoints are not V1 requirements.
3. [Dataset, experiment and event contracts](datasets-experiments-events.md) — Model Lab is deferred.

V1 endpoint families likely include local health/config validation, instrument/reference data, historical market data/coverage, stream session state and portfolio/backtest/paper simulation. Exact routes and password/session protections must be designed with the local runtime; do not expose a public network listener by default.

# Local API contracts

**Trạng thái:** V1 should use loopback APIs between the local web UI and local service. Current Go Gateway/FastAPI contracts are fixture scaffold and older hosted/multi-account target; they do not describe an implemented user API.

The V1 API must not require a remote business service, managed auth or cloud database. SSI credentials are used only by a local adapter and must never be sent from browser to SSI. The browser talks to an allowlisted localhost origin; the local process owns upstream auth, source quota and data normalization.

Các trang bên dưới là contract/prototype tham khảo; không định nghĩa wire schema V1 đã chốt:

1. [Auth and HTTP conventions](auth-and-http.md) — hosted JWT behavior is superseded.
2. [Capability contracts](capabilities.md) — workspace/experiment endpoints are not V1 requirements.
3. [Legacy dataset, experiment, and event contracts](../_archive/api-legacy/datasets-experiments-events.md) — archived; Model Lab is deferred.

Nhóm capability dự kiến gồm local health/config validation, instrument/reference data, historical market data/coverage, stream session state và portfolio/backtest/paper simulation. Exact routes và password/session protections phải được thiết kế cùng local runtime; không mở public network listener mặc định.

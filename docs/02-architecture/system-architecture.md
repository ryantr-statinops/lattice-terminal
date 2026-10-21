# System architecture

**Tóm tắt:** Go sở hữu API, jobs và sổ cái SQLite; Python xử lý dữ liệu, phân tích và worker. Hai dịch vụ chỉ giao tiếp qua loopback có xác thực.


Implemented fixture topology; no enabled SSI upstream transport.

Docker Compose packages the Go gateway and Python engine in one Linux container while keeping them as separate supervised processes. The browser-facing port is published only on host loopback. The host-selected `KESTREL_DATA_DIR` bind mount supplies `/data`; stopping the container preserves it. The optional development override runs Vite in a separate container and publishes both Vite and gateway only on host loopback. A three-terminal local debug mode can run Python, Go and Vite as separate host processes against the same `.env` and data directory; do not run it alongside Compose.

```mermaid
flowchart LR
 UI[React localhost] -->|cookie /api/v1| GO[Go gateway]
 GO --> SQL[(SQLite metadata / ledger)]
 GO -->|loopback internal bearer| PY[Python FastAPI]
 PY --> W[Trusted-code worker processes]
 PY --> PQ[(Parquet snapshots / artifacts)]
 PY --> D[DuckDB in-memory queries]
 GO -->|persisted SSE| UI
```

Go owns auth, workspace/code snapshots, jobs/events/artifact registry and finance transactions. Python never writes Go SQLite. Manual fills/cursor commit atomically; Strategy events commit individually and require inspection after interruption. No inferred missing fills.

Parquet publication uses temporary directories/checksums/completed manifests. DuckDB is per-query, not a shared writable process database. Offline backup snapshots SQLite through VACUUM INTO and checksums managed files.

Native Windows uses Job Objects; the Linux Compose runtime uses Unix process groups and container init/shutdown handling for descendants. Host/Origin/internal auth defend service boundaries, not a sandbox against the host/container user. [Security](../11-engineering/security-privacy.md).

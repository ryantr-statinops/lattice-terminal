# Local runtime / Scheduling

## Docker Compose runtime

Docker Compose is the recommended local launch path on Windows/macOS (Docker Desktop) and Linux (Docker Engine plus Compose plugin). The regular Compose service runs the Go gateway and Python engine in one Linux container. It publishes only `127.0.0.1:8080`; the gateway binds inside the container, while Host/Origin checks continue to expect the browser's localhost origin. Health becomes ready only after the gateway and engine are ready.

Before start, copy `.env.example` to `.env`, create the absolute host directory in `KESTREL_DATA_DIR`, and choose ownership. Linux/macOS deployments should set `KESTREL_UID`/`KESTREL_GID` to the directory owner; Docker Desktop can use the defaults. Data is bind-mounted at `/data`, outside the checkout. `docker compose down` preserves it. Routine shutdown must not use `down -v`.

```sh
docker compose up --build
# Open http://127.0.0.1:8080
docker compose down
```

The development override mounts the checkout read-only and gives dependencies separate named volumes. Vite hot reload is published only at `127.0.0.1:5173`; changes to Go/Python need a service rebuild/restart. Installing/building dependencies requires network access. Fixture runtime assets are local; Compose does not promise offline live market data. Closing the browser does not stop jobs; stopping the container interrupts active jobs and restart marks them interrupted without automatic resume.

## Native development path

For debugging, the root README documents a three-terminal host workflow for Python engine, Go gateway and Vite. It uses the same `.env` and data directory as Compose. Stop Compose before starting it, and stop the three host processes before returning to Compose.

## SSI and news boundaries

Compose does not enable SSI access. The OS-keyring export and read-only secret mount are plumbing only; application consumption is not implemented and source gates remain blocked. Any future use requires approved capability-specific rights, endpoint, quota and implementation. A mounted secret file is plaintext on the host during use, and deleting it is not secure erase. Built-in upstream networking is gated; trusted Python scripts have the host/container user permissions and are not sandboxed.

News has an independent operating model; terminal Compose's networking or lifecycle policy does not define it. No hosted runtime, cloud scheduler, telemetry or automatic upload is enabled.

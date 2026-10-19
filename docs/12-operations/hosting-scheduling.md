# Local setup, jobs and network boundaries

**Trạng thái:** V1 direction is clone-and-run on Windows; current setup only starts the fixture frontend/API and is not yet the full product runtime.

V1 does not use Vercel, hosted APIs, managed auth, shared database/object storage, cloud scheduler or remote relay. The browser interface runs on localhost and local services bind to loopback only. Exact one-command startup, process supervisor, Windows supported versions and shutdown behavior remain implementation decisions.

Product SSI access is opt-in after entitlement, terms, quota and exact use/storage rights are approved. Before production approval, a bounded access probe needs a separate record under the [probe policy](../03-market-research/source-register.md#access-probes-and-operating-states); no probe is authorized here. History refresh/backfill is explicit and bounded; no hidden scheduler/service in MVP. Eligible live/paper sessions stop when their local service stops.

News engine quốc tế/Việt Nam là workstream độc lập trong định hướng hiện tại; scheduler và operating model của engine chưa quyết định. Không cài như remote service hoặc bật trong terminal trước integration approval.

## Run and support requirements

- Setup documentation must show required tool versions, clone/configure/start/stop/update/backup/reset flows and local ports.
- Bind APIs to loopback; do not enable LAN access by default. Restrict browser origins and request sizes.
- Keep ConsumerID/Secret out of source, frontend bundles, command-line arguments where observable, URLs and logs. Choose Windows secret storage before enabling real credentials.
- Network requests use bounded timeouts/concurrency and account-specific quota. Stop on auth, terms/policy and hard quota failures; never proxy restrictions.
- Do not send telemetry, crash data, market payloads or portfolio data to project services by default.
- Dependency/security updates are pulled from source by the operator; avoid auto-updating parser/runtime behavior while a backtest is running.

Hosted deployment or multi-user sharing requires a future product/architecture decision and fresh data-rights review; it is outside V1.

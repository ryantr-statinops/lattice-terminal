# Constraints & invariants / Bất biến

## Runtime and ownership

Docker Compose local runtime on Windows/macOS/Linux, loopback UI, no hosted backend, telemetry or automatic upload. Browser calls Go `/api/v1`; Go calls authenticated local Python inside the container. Only `127.0.0.1:8080` is published by default. Fonts/editor/assets are local/system fallback, no runtime CDN. Building needs network; real SSI would require upstream access, so local-first does not promise an offline live market.

Default data is repository `data/` configured by `.env`; deleting source can delete data. Separate [storage boundaries](04-data/storage-and-retention.md#storage-inventory-and-deletion-boundaries) cover app/browser/OS secrets/backups/exports. No secure-erase claim.

## Security and programs

One local username/password comes from ignored repository `.env`. The Argon2id verifier exists only in memory; edit `.env` and restart to change credentials. HttpOnly SameSite cookie, 30-minute session lifetime (including active SSE) and explicit lock. Password locks a session, not disk encryption. SSI secrets use the OS keyring via CLI; Compose secret export is a temporary plaintext host file, mounted read-only, and is not consumed by the current app. No browser/Git/log credentials or guaranteed all-RAM zeroization.

Trusted Python runs with the container user's filesystem/network permissions in a separate process, **not a sandbox**. Built-in networking remains capability-gated. Lock, closing browser tabs or switching files does not stop jobs; service stop interrupts them. Restart/restore never auto-runs Strategy/Paper.

Research, Backtest and Strategy have distinct contracts/files/history. Train/Test means ordered research/evaluation without optimization or AI training. Freeze code/helpers/params/dependency lock at Run; record data/rule versions. SDK historical views are causal, but authors must audit trusted code for lookahead outside the SDK.

## Sources and simulation

SSI FastConnect Data only; no real orders/Trading, margin, short or leverage. Independent flags: documented/access-tested/rights-confirmed/approved. A separately authorized scoped probe may collect access evidence before production approval; no implicit storage/display/research/export rights. No live SSI transport/calls in this build.

Unknown metrics/prices/warm-up remain unavailable, never fake zeros. Detailed synthetic LO quote replay uses fictional effective rules. Real sessions, tick/lot, price limits, auctions, costs, corporate actions and settlement availability need [evidence](07-portfolio/vn-market-rules.md). No OHLC/daily-open fallback.

## Capital and scope

VND decimal accounting, weighted-average cost; transactional independent Manual/Strategy allocations. Portfolio counts allocation cash once. Backtest capital never touches funds. Stop/reconcile does not liquidate positions or release unsettled obligations. Settled tracking records remain distinct from simulated fills.

News is independent. Model Lab/optimization, factor research, 3D surfaces, derivatives and ETFs are later work. [Remaining gates](13-rebuild/progress.md).

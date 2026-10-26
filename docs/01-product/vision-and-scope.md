# Vision & scope / Tầm nhìn

**Tóm tắt:** Kestrel Terminal là terminal nghiên cứu tài sản Việt Nam chạy local. Bản hiện tại dùng fixture; provider thật chỉ được bật theo capability, quyền dữ liệu và model mô phỏng đã xác minh.


Kestrel Terminal is a local-first research terminal for Vietnamese markets, run on the user's machine. Main journey: **Market → Quant → Backtest → Portfolio**, with separate Strategies and Assets sections. Provider integrations cover all documented asset classes offered by selected Vietnamese brokers and data vendors; each dataset is independently gated.

## Accepted

Vietnamese brokers and data vendors, including free and paid sources. Ingest every selected-provider dataset with a distinct asset/data contract. Broker account sync is read-only and displayed separately from local funds. Research, historical Backtest and paper Strategy have distinct files/contracts/run histories. Strategy supports live-feed and paper-replay signals. Local notifications provide a persistent inbox, unread badge and toast; optional Telegram delivery targets one private chat. Gmail integration is out of scope.

One local password-locked profile; local persistence; no hosted accounts, telemetry, real broker orders, margin, short or leverage. Backtest and paper use local funds/allocations. Ingested assets may be researched and signaled; simulation is available only when a matching rule pack and fill model exist. Paper replay notifications stay local unless Telegram delivery is explicitly enabled. [Constraints](../CONSTRAINTS.md).

## Current versus target

Synthetic daily data/Quant, detailed replay, funds and settled CSV are implemented. Provider transports, data rights, complete asset models, real corporate actions and settlement remain gated until verified. [Progress](../13-rebuild/progress.md) records verification and limits; this is not production-ready.

News remains an independent workstream. Train/Test is not training. AI training and optimization remain deferred.

# Vision & scope / Tầm nhìn

**Tóm tắt:** Kestrel Terminal là terminal nghiên cứu cổ phiếu Việt Nam chạy local trên Windows. Bản hiện tại dùng fixture; nguồn SSI thật và mô phỏng thị trường thật còn bị chặn.


Kestrel Terminal is a free MIT local-first research terminal for Vietnamese equities, run from source on Windows. Main journey: **Market → Quant → Backtest → Portfolio**, with separate Strategies and Assets sections.

## Accepted

HOSE/HNX/UPCoM stocks first; actual SSI coverage is gated. Research, historical Backtest and paper Strategy have distinct files/contracts/run histories. Sidebar file trees, center editor, right results/logs; no file tabs. Assets manages named VND funds and independent concurrent Manual/Strategy allocations.

One local password-locked profile; local persistence; no cloud accounts, telemetry, real orders, margin/short/leverage. [Constraints](../CONSTRAINTS.md).

## Current versus target

Synthetic daily data/Quant, detailed replay, funds and settled CSV are implemented. SSI transport/rights/coverage/rules, real corporate actions and settlement remain unavailable. [Progress](../13-rebuild/progress.md) records verification and limits; this is not production-ready.

News is independent. Train/Test is not training. Later: factor research → parameter surfaces/3D → derivatives → ETFs. AI training and optimization remain deferred.

# Ledger & valuation

**Tóm tắt:** Phân bổ vốn bằng transaction, giữ sổ riêng từng allocation và không đếm vốn hai lần. NAV/P&L không khả dụng khi còn vị thế thiếu giá.


Go alone writes SQLite finance state. VND values are decimal strings/arithmetic; cost basis is weighted average.

Paper funds grant independent Manual/Strategy allocations transactionally; concurrent commitments cannot exceed available parent cash. Flows/transfers/budgets have idempotency keys. Backtest capital never touches funds. Orders reserve buy cash or settled sell shares; fills validate order/time/side/limit/remaining/cost. Duplicate financial events do not post twice.

Manual fills/cursor commit together. Strategy events commit individually, so crash review is required. Stop/reconcile cancels open remainder without liquidating positions or releasing unsettled obligations.

## Portfolio

NAV = parent cash + allocation cash + reserved + unsettled + marked position value. Do not add allocation net-contributed capital again. Total P&L = NAV minus net fund flows; transfers offset across funds. Realized/unrealized split and return-series analytics are not implemented.

Marks show last-observed source/as-of and may be stale. Missing any position price leaves fund NAV/P&L null; known subtotal is not NAV. Current immediate synthetic settlement is fictional. Real availability-time settlement, corporate actions, auctions and production rules remain [blocked](vn-market-rules.md).

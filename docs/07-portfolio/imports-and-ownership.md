# Settled tracking records / CSV

**Tóm tắt:** Preview CSV trước khi ghi toàn bộ giao dịch đã thanh toán; lỗi bất kỳ dòng nào làm rollback. Sửa lịch sử bằng quỹ tracking mới và nhập lại theo thời gian.


Tracking funds accept user-confirmed settled trades, separate from paper fills. They do not query broker balances. Portfolio supports manual entry and UTF-8 CSV preview/import/export.

```csv
trade_id,event_time,instrument_id,side,quantity,price,fee,tax,settled
example-1,2026-10-01T02:00:00Z,HOSE:REGULAR:equity:SYN01,buy,1,100,0,0,true
```

Exact header, max 2 MiB/5,000 validated rows. IDs use safe ASCII identifiers, not formula prefixes. Explicit offset/UTC time; positive quantity/price, explicit nonnegative fee/tax and settled=true. Costs are user assertions, not verified market defaults.

Preview checks syntax; Apply recomputes hash and validates cash/settled shares in one transaction. Any failure rolls back all rows. Stable trade IDs prevent duplicates; changed content with same ID fails. New rows cannot predate existing history. Correct/reorder via a new tracking fund and chronological reimport, not silent edits.

Export includes recorded trades only. Transaction price is not inferred as a current valuation mark. Missing price stays unavailable. User-created copies require separate cleanup.

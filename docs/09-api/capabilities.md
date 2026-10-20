# Capabilities / Current state

| Capability | Implemented fixture | Remaining gate |
|---|---|---|
| Auth/files/jobs/ledger | Local Windows services | Not a hostile-code sandbox |
| Daily / Quant | Synthetic Parquet / indicators | SSI transport/rights/calendar |
| Intraday/reconnect | Offline reconciler/subscriptions | No actual SSI transport |
| Backtest | Detailed synthetic Train/Test | Real detailed data/rules/actions |
| Strategy/Manual | Explicit replay, separate books | Live feed/real settlement |
| Portfolio/CSV | Local books/last marks/settled records | Not broker accounting |
| Backup/restore | Offline ZIP/new root/no auto-resume | Size/schema bounds |
| News/Model Lab/3D | Separate/deferred design | Not implemented |

Flags remain independent. Scoped probe authorization does not approve production/retention. No live calls occurred. [SSI evidence](../13-rebuild/ssi-evidence.md).

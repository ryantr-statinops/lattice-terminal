# Runtime lifecycle / States

**Tóm tắt:** Khóa giao diện, ẩn tab hay đổi file không dừng job. Stop dịch vụ, crash và restore cần trạng thái interrupted và xử lý rõ ràng.


| Event | Job / paper behavior |
|---|---|
| File switch, browser hidden/closed | Continues with local services; view changes only |
| UI lock / expiry | Requires login to view; jobs continue |
| Explicit job Stop | Worker tree stops; cancelled terminal state; inspect/reconcile book |
| Completed Strategy replay | Cancel open remainder, preserve positions/cash, book stopped |
| Service stop/crash | Active jobs interrupted; no inferred missing fills |
| Restart/restore | No auto-resume; restored paper books interrupted |
| Market gap/stale | No fills from unavailable/unreconciled observations |

Run states: queued/running/stopping (reserved transition)/completed/failed/cancelled/interrupted. Current Stop requests cancel; don't assume instantaneous completion. Timeout fails with reason. Unknown metrics aren't zeros.

Train/Test is chronological evaluation, not model training. Model Lab/browser training workers/remote result synchronization are deferred. Workers are local Python processes, not browser Web Workers.

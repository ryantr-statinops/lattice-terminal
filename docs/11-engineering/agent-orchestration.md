# Agent orchestration
**Trạng thái:** quy trình thực hiện.

Coordinator khóa glossary, ADR, shared contracts, dependency board, integration và commits. Tối đa ba subagent hoạt động cùng lúc; mỗi assignment có task IDs, inputs accepted revision, paths độc quyền, exclusions, outputs, checks, exit và handoff.

## Waves
1. Product owner closes SSI entitlement/source gates, instrument classes, local security/persistence and portfolio simulation assumptions.
2. Implement local Windows runtime and offline SSI adapter contracts/fixtures; no live calls before source gate.
3. Integrate approved SSI historical/reference data, then stream reconciliation; implement portfolio backtest and paper simulation.
4. Release/recovery review; standalone news engine and Model Lab stay separate/deferred.
5. Review docs/code consistency, test relevant quality gates, commit small changes and send through PR.

Subagent không git add/commit/switch, không sửa ngoài ownership, không đổi shared contract âm thầm. Khi cần thay schema/decision, báo coordinator để dừng dependent work và cập nhật owner document.

Handoff ghi files, assumptions, external evidence, checks/results, unresolved questions, risks và next dependency. Coordinator review rồi cập nhật status, không coi agent báo xong là nghiệm thu tự động. Commit chỉ tài liệu thuộc task hiện tại; không git add .; không push nếu chưa được yêu cầu.

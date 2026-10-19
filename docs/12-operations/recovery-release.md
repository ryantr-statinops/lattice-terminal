# Recovery và release gates

**Trạng thái:** local release direction; recovery has not been rehearsed and no real SSI data is approved/loaded.

## Recovery requirements

- Back up local database/files with schema and manifest versions; test restore on a clean Windows profile.
- Incomplete writes must not replace prior valid snapshot/portfolio state. Recovery reports state and the last consistent version.
- User can export supported data and locally delete/reset the installation's workspace. Define how secrets are cleared/rotated in the SSI account separately.
- App update/migration must preserve user data or provide a verified backup/rollback path.
- Interrupted live/paper session restores as interrupted/unknown until the feed and ledger reconcile; never infer unseen fills.
- Snapshot revisions preserve provenance and source policy. If source permission expires/revokes, stop affected access and apply the documented restrict/delete action.
- Password recovery/reset and encryption-key recovery must be explicit; a lost password must not cause silent data loss or implied provider password reset.

## Release checklist

- [ ] SSI REST/stream access and rights gates approved separately for exact account, endpoints, fields, geography, local retention and research/paper use.
- [ ] Local secret management, loopback binding, password protection, storage encryption/recovery, export/delete and no-telemetry behavior reviewed.
- [ ] SSI schema mapping, history/stream reconciliation, timestamp/session rules, quality and partial/unavailable states tested.
- [ ] Backtest anti-lookahead, market calendar/mechanics, fees/taxes/slippage and reproducibility reviewed.
- [ ] Paper mode has no real-order route or trading credentials; simulated fills are clearly labeled and recover safely after restart/gaps.
- [ ] Windows clone/start/stop/update/recovery guide verified; supported toolchain and ports documented.
- [ ] Accessibility and Vietnamese source/freshness/session/partial labels reviewed.
- [ ] News engine remains independently scoped and is not silently integrated into terminal MVP; Model Lab remains deferred.

If a gate is missing, keep that capability disabled or fixture-only; do not present it as complete by editing copy.

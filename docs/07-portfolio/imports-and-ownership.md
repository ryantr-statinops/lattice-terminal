# Portfolio data, import and local ownership

**Trạng thái:** local-only requirement accepted; import and persistence contracts pending.

Portfolio files belong to the local installation/user profile. V1 does not upload them or scope them by hosted account/workspace/JWT. Local password login is an access-control request, not proof that disk data is encrypted. The storage and secret design must define profile isolation, encryption, backup, export, delete and password recovery before real personal data is persisted.

## CSV direction

CSV import/export is a candidate local workflow, not yet a locked schema. Before implementation, define:

- UTF-8 header/version and canonical instrument identity (venue, board, market type, instrument class, native symbol).
- Decimal separator, quantity/price scale, currency, fees/taxes and timezone requirements.
- Event types for initial cash/positions, simulated orders/fills, deposits/withdrawals, dividends/corporate actions and corrections.
- Duplicate/idempotency rules and row-level preview/errors.
- Atomic import: either all accepted rows are committed or none are; do not silently discard/rewrite rows.
- Export format plus manifest for source, snapshot, strategy, simulation assumptions and application version.

Không áp dụng tự động giả định định danh/fee/account ownership của prototype cho instrument Việt Nam.

## Local lifecycle

Target storage preserves versioned events/outputs and supports integrity-checked backup/restore. Settings reset, portfolio deletion, local-secret removal and restore need distinct scope under the [storage inventory](../04-data/storage-and-retention.md#storage-inventory-and-deletion-boundaries); exporting does not make copies automatically deletable. Do not log secrets, unapproved raw payloads or private transaction content. Ordinary deletion is not secure erase.

If multiple local profiles are supported, switching profile must isolate portfolio, data, preferences and caches. Whether V1 has one local profile or multiple password-protected profiles is open. See [storage and retention](../04-data/storage-and-retention.md).

## Acceptance direction

- Bad schema/timezone/decimal/identity is reported before import.
- Duplicate imports are detectable and safe to retry.
- Failed/partial import does not corrupt existing portfolio state.
- Export then import preserves event order, decimal values, source references and simulation labels.
- No transaction/credential content is sent to a remote service.
- Wrong password/recovery/reset behavior is defined and does not silently expose or erase local data.

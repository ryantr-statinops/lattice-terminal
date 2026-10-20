# Limits & diagnostics

Fixture-only. Actual SSI quotas are unverified; offline scopes describe endpoint/purpose/field/quota/expiry/rights, but no real transport consumes them.

Worker output has count/size/table/timeout bounds. Python user logs are private run events; native child stderr is discarded. Go persists events/states/artifact references. kestrel.exe -diagnostics prints an allowlisted schema/product/source-mode summary, not raw paths/files/payloads/tokens/accounts; it is not a full crash report.

Backup limits: 256 MiB/file, 2 GiB total, 50,000 files. CSV: 2 MiB/5,000 valid rows. Workspace: per-file/snapshot bounds. Large history memory/storage pressure and retention policy need further work; no silent automatic purge.

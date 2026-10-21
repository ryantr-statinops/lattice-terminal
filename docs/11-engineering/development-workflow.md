# Development workflow

Locked Node/npm/Go/uv, Python 3.12. Docker Compose is the primary local workflow; optional three-terminal debugging instructions are in the root README. Go owns SQLite; Python owns Parquet; frontend calls Go. Stop the running app before rebuilding or sharing the data directory.

One reviewed commit per approved rebuild milestone on main; preserve the original tag/history. No automatic push/remote rename/PR requirement for this rebuild. Inspect diff and relevant checks before commit.

No real credentials or SSI probe without separate scoped authorization. Tests use temporary roots, never reset/delete the user's default data. Contract changes need regeneration/drift checks and consumer integration review. No package installation during user-program Run. Update docs with actual state, not assumed completion.

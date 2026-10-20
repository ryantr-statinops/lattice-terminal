# Rebuild checkpoint — 2026-10-19

Status: **resumed on 2026-10-20** at the user's request.

## Git

- Branch: `main`, 20 local rebuild commits ahead of `origin/main`; nothing pushed.
- Latest commit: `5d92ae1` — `feat: add Assets budgets and atomic manual paper replay`.
- Original baseline tag: `archive/pre-kestrel-rebuild-2026-10-19`.

## Work remaining

- Parts 1–20 have implementation commits. These implement offline/synthetic workflows; they do not establish production readiness.
- Part 21 adds Portfolio UI/API, transaction-consistent fund valuation, last-observed price provenance, explicit missing NAV/P&L, and settled tracking-trade entry/CSV preview/import/export. Allocation cash is counted once. Imports are atomic and idempotent; backdated additions are rejected. CSV identifiers exclude spreadsheet formulas.
- Part 21 checks: Go store/API tests, frontend typecheck, lint and production build passed. Browser acceptance and full recovery checks remain in part 22.
- Part 22 (recovery and release) has not started. Backup/restore, interrupted-session recovery, final security review, clean-clone Windows verification, UI checks, contract checks and documentation reconciliation remain.

## Resume constraints

- Continue on `main`, one commit per remaining part; do not push.
- Preserve unfinished files and existing Git history.
- SSI remains unapproved and fixture-only; no live calls or real credentials have been used.
- Real source transport, coverage, exchange rules and supported production fill models still require evidence and implementation. Do not describe synthetic completion as production approval.
- Local test services started during implementation have been stopped.

Continuing with recovery and release / Tiếp tục recovery và nghiệm thu.

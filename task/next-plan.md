# MVP roadmap

## Product direction — recorded 2026-10-18

Research Terminal is open-source/free research infrastructure for Vietnamese users. V1 is cloned from the repository and run locally on Windows with a localhost web UI; no installer or hosted service is required. All config, SSI credentials, data, portfolio and research output stay on the user's machine. SSI FastConnect Data is the market provider direction; aim to use all applicable REST/reference/stream capabilities after endpoint entitlement and terms are verified. Do not use FastConnect Trading or real orders.

Portfolio MVP includes historical backtesting and paper live trading. The project's own international/Vietnam news engine is a separate workstream and will be integrated later. Model Lab is outside the first MVP.

## Current implementation stage

The repository is still a fixture prototype: React/Vite UI, Go Gateway and FastAPI read synthetic data; portfolio only has local prototype state; Model Lab is a mock. There is no SSI adapter, local secret vault, password login, persistent local store, backtest engine or paper live simulator. Binance code/contracts/stream controls are legacy prototype material. The docs now record the new product direction, but several detailed UI/API/Model Lab docs still require migration before they can serve as implementation contracts.

SSI official docs were reviewed for capability. Nine REST APIs and stream groups F, X/X-Quote, B, R, MI and OL are documented. The user's account entitlement, prices, actual numeric quotas, coverage/history depth, fixed-IP requirement and permission for local storage/research/display are not verified. `SSI-FC-DATA-REST` and `SSI-FC-DATA-STREAM` remain `documented=true`, `access-tested=false`, `rights-confirmed=false`, `approved=false`; no SSI calls or real payload persistence are allowed while blocked. See [SSI research](../docs/03-market-research/vn-equities.md) and [source register](../docs/03-market-research/source-register.md).

## Work sequence to MVP

1. **Complete product decisions:** confirm first-release instrument classes/markets, which stream groups to expose, local profile count/password recovery, storage/encryption/backup, portfolio currency and simulation mechanics. Keep unconfirmed items visibly pending.
2. **SSI entitlement and terms gate:** user checks FastConnect Data service registration/account plan with SSI. Record endpoint/feed entitlement, price, history/resolution coverage, quota/concurrency, fixed-IP/token requirements, service expiry and terms for local access, retention/export, backtest/derived use, display and deletion. Keep credentials private; do not paste them into docs/issues/chat. Do not proceed with real payload until this scope is sufficient.
3. **Windows local foundation:** choose local process topology/one-command startup, loopback API, local password/profile model, Windows secret storage, persistent data format, encryption/recovery/export/delete and no-telemetry defaults. This is needed before collecting user secrets or personal records.
4. **Offline SSI adapter contract:** build endpoint-specific domain types, parser/normalizer and synthetic fixtures for documented SSI response shapes. Version timestamp/session/identity mappings and validate decimal values, duplicate/revised/out-of-order records, partial responses, market closures and coverage. Tests must not contact SSI.
5. **Authorized historical integration:** after gates 2–3, add bounded REST/reference calls for entitled data, explicit history ranges and checkpoints; publish immutable local snapshots with manifest, provenance, checksums and partial/gap reporting. Add retry limits and stop safely on auth/policy/quota errors.
6. **Local market UI and streaming:** serve snapshots from loopback API. Add entitled SSI stream groups needed by the chosen scope; reconcile against REST/history on startup/reconnect. Mark stale, partial and unavailable states; never patch gaps with synthetic bars.
7. **Portfolio backtesting:** decide VN instrument/session/lot/tick/price-band/corporate-action behavior, capital/currency, fees/taxes/slippage and fill model. Build deterministic replay on snapshot versions with lookahead prevention and reproducible reports.
8. **Paper live trading:** simulate local orders/fills from reconciled live data, with explicit fill assumptions, pause-on-gap behavior and restart recovery. Confirm no real-order code path or trading credential can be configured.
9. **MVP release readiness:** Windows setup/upgrade/recovery guide; security and local storage review; source/status labels; quality gates; test against entitlement-approved feeds; verify all information stays local and app works without network except explicitly started SSI features.
10. **Later workstreams:** build the standalone news engine and integrate through a source-governed local contract. Model Lab, hosted sync and real execution remain deferred unless scope is explicitly changed.

## Immediate questions for product review

1. **Universe:** should V1 use equities on HOSE/HNX/UPCOM only, or include SSI-documented DER and BOND instruments from the start? “Use all” is recorded as the goal, but the relevant asset classes need explicit confirmation.
2. **SSI feeds:** use every entitled group (`F`, `X`/`X-Quote`, `B`, `R`, `MI`, `OL`) in first release, or stage them after historical/reference data? Some groups are only relevant to specific instrument classes.
3. **Local login:** one password-protected local profile, or multiple profiles on one installation? Should losing the password allow reset (with data loss) or require a recovery key?
4. **Paper execution:** which simulated order types and fill assumptions are required in V1 (market-only is the simplest starting point); should offline/gap conditions block new simulated orders?
5. **Portfolio:** confirm VND as base currency, and whether V1 requires fees/tax, dividends/corporate actions, and CSV import/export.
6. **Open-source license:** confirm repository license choice; “open source/free” is a product direction, but no license choice is recorded in these docs yet.

## Process

Repo policy protects `main`: work on a review branch, keep commits small, open a PR and wait for required checks. Do not push real user/SSI data or credentials. Review product decisions before turning pending items into hard implementation defaults.

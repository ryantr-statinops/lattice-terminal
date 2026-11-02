---
name: repo-orientation
description: Orient yourself in the Kestrel Terminal repository before explaining its architecture, locating a feature, or planning repository work. Use when asked how the project is organized or where a change belongs.
---

# Repository orientation

Use this workflow to build a current, evidence-based map of the repository before answering architecture or change-location questions.

1. Read the root `AGENTS.md` and `README.md` for repository rules, project boundaries, and supported startup paths.
2. For current implementation status or limitations, read `docs/13-rebuild/progress.md`. For product or service boundaries, follow the relevant links from `docs/README.md`.
3. Inspect the source files that answer the specific question. Treat documentation as a guide and confirm implementation details in code when they matter.
4. Summarize the relevant paths, service ownership, and applicable checks. Link files directly when answering.

## Project constraints

- This is a local-first Vietnamese equity research terminal.
- The default development path is fixture-only. Synthetic simulation results do not establish real-market execution behavior.
- SSI access, entitlements, data rights, and market-rule evidence remain gated; do not infer approval from offline tests or implemented adapters.
- Live order routing is not implemented. Do not describe paper simulation as real trading.

Keep the investigation scoped to the question. Do not run the full test suite just to explain repository structure.

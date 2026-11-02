# Agent helper scripts

Place deterministic, local utilities for agent workflows here when they have a stable interface and are useful independently of one skill.

For each utility, document its purpose, inputs, outputs, required runtime, and invocation. Keep it scoped to the repository, avoid network/provider access unless separately approved by the documented gates, and never embed credentials. Add focused automated coverage when the utility is implemented.

If a script only supports one skill, keep it in that skill's `scripts/` directory instead.

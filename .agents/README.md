# Repository agent resources

This directory contains versioned instructions and workflows for agents working in this repository.

## Layout

- `skills/<skill-name>/SKILL.md`: one focused, reusable workflow per skill. Optional `scripts/`, `references/`, and `assets/` belong inside the skill when they are only useful to that workflow.
- `../tools/agent/scripts/`: deterministic utilities that are useful independently of one skill.
- `../tools/agent/mcp/`: source code for purpose-built MCP servers.

`AGENTS.md` at the repository root remains the source of shared project rules. Skills explain how to perform repeatable jobs; they should not copy the full repository guide.

## Boundaries

- Keep skills small, with a clear `name` and a description that says when the workflow applies.
- Prefer instructions first. Add a script when a workflow needs deterministic behavior or a local executable.
- Add an MCP server only for a concrete agent-facing capability that benefits from a typed interface. Do not expose a second way to do something already available through ordinary repository tools without a clear benefit.
- Start with read-only MCP capabilities. Validate inputs, restrict access, sanitize outputs, and require human confirmation for sensitive writes.
- Keep secrets, local credentials, generated runtime data, and provider payloads out of this directory and Git.
- Treat the application as fixture-only. Do not add live provider calls or real order routing without the documented source, rights, and product gates.

## Current contents

- `skills/repo-orientation/`: repository map and first-read workflow.
- `skills/commit-workflow/`: plan reviewable implementation tasks, commits, checks, and remote delivery. Copied from [Orbit-System-Manager](https://github.com/ryantr-statinops/Orbit-System-Manager/tree/main/.agents/skills/commit-workflow).

See [`../tools/agent/README.md`](../tools/agent/README.md) for guidance on scripts and MCP server code. MCP client configuration is managed separately from server source; this repository currently has a root `.mcp.json` for existing development integrations.

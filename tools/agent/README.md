# Agent tooling

This directory is for executable support code used by repository agents. Keep it separate from agent instructions in `.agents/` and from product runtime services.

## Layout

- `scripts/`: deterministic local utilities with a clear command-line interface.
- `mcp/`: purpose-built MCP server source, grouped by server.

Put a helper under a skill's own `scripts/` directory when it only supports that skill. Put it here when it has independent reuse or a stable repository-wide interface.

Do not add wrappers around ordinary shell, Git, or repository search capabilities without a concrete benefit. Keep credentials and generated application data out of this tree.

See [`mcp/README.md`](mcp/README.md) before adding an MCP server and [`scripts/README.md`](scripts/README.md) before adding a standalone utility.

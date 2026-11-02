# MCP servers for repository agents

This directory holds source code for MCP servers that expose a concrete, typed capability to an agent. It does not configure a client or automatically register a server.

## Before adding a server

1. State the user workflow and why an MCP interface is better than an existing API, CLI, or ordinary repository tool.
2. Prefer read-only capabilities first. Do not expose live SSI requests, provider-secret access, or real-order actions; the project has not passed the required source, rights, and product gates.
3. Give each server its own directory, dependency manifest, run instructions, and focused tests. Define narrow tool names and input/output schemas.
4. Validate every input, enforce least privilege, bound execution time and output size, sanitize returned data, and avoid logging secrets or private payloads.
5. For a stdio server, write protocol messages to stdout only and send diagnostics to stderr.
6. Document how the intended client connects to the server. Keep machine-specific paths and credentials out of committed configuration.

MCP client configuration is managed separately. The repository currently has a root `.mcp.json` containing development integrations; inspect its consumer and avoid duplicating those entries when adding a server.

No project-specific MCP server is implemented here yet. Add one only after its capability and data boundary are clear.

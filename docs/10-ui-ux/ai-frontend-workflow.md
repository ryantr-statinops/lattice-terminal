# OMP frontend workflow

Development tooling only: Agentation supplies visual feedback, Context7 supplies library documentation, and Chrome DevTools supplies browser diagnostics. These tools do not change backend APIs, source gates, or product data contracts.

## Setup

Use the repository's Node 22 and npm 10 versions, install with `npm ci`, and ensure `omp --version` works in the same terminal. Install OMP separately; the project does not change its model, credentials, or global settings. Chrome DevTools requires Google Chrome. Packages are pinned in the manifests and lockfile.

Start everything from the repository root:

```powershell
npm run dev:ai
```

The launcher checks OMP, local server entrypoints and ports 5173/4747. It starts Vite, waits up to 30 seconds, then opens interactive OMP. Open `http://127.0.0.1:5173`. Vite logs append to `.cache/dev-ai/vite.log`; OMP retains the terminal. It discovers all three stdio servers from the root `.mcp.json` and owns their lifecycle. Chrome opens on its first browser tool call, not on MCP connection.

Exit OMP with `/exit`, or use Ctrl+C to interrupt/exit according to OMP's interactive behavior. When OMP exits, or the launcher receives a termination signal, the launcher cleans up its own child processes. It never terminates pre-existing port owners. Do not start a second Agentation server alongside OMP.

This command does not start the gateway, engine or Docker. Product screens still require the normal backend setup; a working dev server does not imply authenticated product flows are available.

## Ordinary development and credentials

For ordinary `npm run dev`, copy [the web env example](../../apps/web/.env.example) to `apps/web/.env.local` and choose:

```dotenv
VITE_ENABLE_AGENTATION=true
```

Restart Vite after changing it. `false` or an absent variable hides the toolbar. `dev:ai` overrides the flag to `true` only in its child environment, without modifying local files. Production never imports the toolbar, even if the flag is true.

Context7 can use an inherited API key if required by account limits:

```powershell
$env:CONTEXT7_API_KEY = '<your key>'
npm run dev:ai
```

OMP/MCP credentials belong in the launching shell or the agent's credential storage. The launcher does not load secrets from dotenv files. Never store secrets in `.mcp.json`, committed examples or `VITE_*` variables, which are browser-visible. Existing provider/model selection remains authoritative.

## Feedback loop

1. Open Agentation's toolbar in the app, select an element or area and add a concrete change request.
2. In OMP, ask: “Read pending Agentation feedback for this project's current page, list the requests, then implement the requested changes.” Match the page/session URL; do not process unrelated sessions.
3. Ask OMP to use existing tokens/components, check affected behavior, and resolve feedback only after verification. A connected MCP does not automatically start an agent watch loop.
4. Use Context7 for a specific library/API question, stating the installed version. Check official documentation if that version is unavailable. Queries go to Context7's service.
5. Use Chrome DevTools for console/network failures, screenshots or performance analysis. Screenshots may be saved under `.cache/dev-ai/`; filesystem access is scoped to the repository. Browser actions use a separate Chrome profile by default, so do not assume the user's existing logged-in tab is shared.

Agentation supplies text context; Chrome supplies screenshots. Its feedback mode intentionally intercepts page interactions while selecting elements. Leave feedback mode before testing ordinary application behavior. Check keyboard focus, dialogs, Monaco, terminal controls and panel resizing when reviewing changes.

## Troubleshooting and adding servers

- In OMP, use `/mcp list` to inspect connections and `/mcp reload` after configuration changes. Root `.mcp.json` is a supported fallback; higher-priority or user-disabled definitions can shadow it. Avoid duplicate names across configurations.
- Missing dependencies: run `npm ci`. Missing/broken OMP: verify `omp --version` outside the launcher. Sandbox access failures can look like missing modules; distinguish those from a broken host installation.
- Occupied ports: identify the existing owner and stop it yourself, or exit an earlier OMP session. The launcher refuses to reuse or kill it.
- No annotations: check the toolbar flag, Agentation connection to `http://localhost:4747`, `/mcp list`, and the selected page/session. Registering MCP alone does not enable the toolbar.
- Context7 authentication/quota failures: supply a valid shell credential and restart OMP. Chrome errors: verify Chrome is installed and inspect MCP diagnostics.
- Add future servers as additional `mcpServers` entries. Pin local packages, use root-relative entrypoints and launch OMP from the repository root. The launcher explicitly preflights the current three package entrypoints; extend that check when adding another required server.

Chrome usage statistics and CrUX queries are disabled in the checked-in configuration. No React Grab, cloud annotation storage or webhook is configured.

## Verification record

Checked on Windows, Node 22.23.1, OMP 18.12.6:

- Baseline and final typecheck, lint, 23 web test files / 53 tests, and production build passed. Existing jsdom canvas/scroll warnings and large bundle warnings remain.
- Seven launcher tests cover missing OMP, occupied ports without killing their owners, readiness timeout, Vite failure, OMP exit, descendant cleanup, paths with spaces, inherited toolbar flag, and SIGINT handlers before/after readiness.
- Real interactive `npm run dev:ai` opened OMP with the existing Gemini selection and reported connections to all three MCP servers. `/exit` completed successfully.
- MCP SDK handshake/list-tools passed for Agentation (9 tools), Context7 (2), and Chrome DevTools (32). A synthetic annotation posted over Agentation HTTP was read and resolved through MCP; this verifies transport, not a human annotation session driven by the model.
- Context7 returned React library matches and lazy/Suspense documentation. Chrome launched headlessly, read console/network and saved a screenshot inside the repository.
- Chrome smoke checks used browser-only auth/config fixtures, with no backend started and no real credentials. Sidebar collapsed from 205px to 56px, keyboard resizing reached 213px, terminal drawer toggled, both density values persisted, and StrictMode produced one toolbar host.
- A separate development browser run with the flag set to `false` produced zero toolbar hosts.
- Production JavaScript scan found no Agentation module or `localhost:4747` reference.

Not certified by these checks: full authenticated backend workflows, real terminal process execution, Monaco editing with active feedback selection, native dialog keyboard behavior with feedback enabled, annotation reconnect after a server restart, a model autonomously processing feedback, or physical Ctrl+C behavior across every terminal host. Launcher signal handling is covered by automated tests; the real interactive smoke used `/exit`. Local screenshots and raw tool outputs are ignored artifacts in `.cache/dev-ai/`, not permanent test fixtures.

References: [Agentation installation](https://www.agentation.com/install), [Context7](https://github.com/upstash/context7), [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp), [OMP MCP configuration](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md).

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
foreach ($tool in @('go','node','npm','uv')) { if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Missing $tool; see README toolchain versions" } }
if ((node --version) -ne 'v22.23.1') { throw 'Node 22.23.1 required' }
if ((npm --version) -ne '10.9.8') { throw 'npm 10.9.8 required' }
if ((go version) -notmatch 'go1\.27\.2\s') { throw 'Go 1.27.2 required' }
if ((uv --version) -notmatch '^uv 0\.11\.28(?:\s|$)') { throw 'uv 0.11.28 required' }
npm ci
if ($LASTEXITCODE) { throw 'npm ci failed' }
uv sync --project services/engine --python 3.12 --frozen
if ($LASTEXITCODE) { throw 'Python environment setup failed' }
npm run build
if ($LASTEXITCODE) { throw 'Web build failed' }
New-Item -ItemType Directory -Force .cache/bin | Out-Null
go -C services/gateway build -o ../../.cache/bin/kestrel.exe ./cmd/kestrel
if ($LASTEXITCODE) { throw 'Gateway build failed' }

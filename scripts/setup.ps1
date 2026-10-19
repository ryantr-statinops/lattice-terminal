$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
foreach ($tool in @('go','node','npm','uv')) { if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Missing $tool; see README toolchain versions" } }
npm ci
if ($LASTEXITCODE) { throw 'npm ci failed' }
uv sync --project services/engine --python 3.12 --frozen
if ($LASTEXITCODE) { throw 'Python environment setup failed' }
npm run build
if ($LASTEXITCODE) { throw 'Web build failed' }
New-Item -ItemType Directory -Force .cache/bin | Out-Null
go -C services/gateway build -o ../../.cache/bin/kestrel.exe ./cmd/kestrel
if ($LASTEXITCODE) { throw 'Gateway build failed' }

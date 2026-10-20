param([string]$DataDir = '')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$binary = Join-Path $taskRoot '.cache/bin/kestrel.exe'
$arguments = @('-root', $taskRoot, '-print-data-dir')
if ($DataDir) { $arguments += @('-data', $DataDir) }
$DataDir = & $binary @arguments
if ($LASTEXITCODE) { throw 'Cannot resolve configured data directory' }
$state = Get-Content -LiteralPath (Join-Path $DataDir 'runtime.json') -Raw | ConvertFrom-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8080/api/v1/runtime/stop' -Headers @{Authorization = "Bearer $($state.stop_token)"} | Out-Null

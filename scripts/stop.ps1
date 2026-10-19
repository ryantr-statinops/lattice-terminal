param([string]$DataDir = '')
$ErrorActionPreference = 'Stop'
if (-not $DataDir) { $DataDir = Join-Path $env:LOCALAPPDATA 'KestrelTerminal' }
$state = Get-Content -LiteralPath (Join-Path $DataDir 'runtime.json') -Raw | ConvertFrom-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8080/api/v1/runtime/stop' -Headers @{Authorization = "Bearer $($state.stop_token)"} | Out-Null

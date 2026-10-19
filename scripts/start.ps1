param([switch]$Dev, [string]$DataDir = '')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$binary = Join-Path $taskRoot '.cache/bin/kestrel.exe'
if (-not (Test-Path -LiteralPath $binary)) { throw 'Run scripts/setup.ps1 first' }
$arguments = @('-root', $taskRoot)
if ($Dev) { $arguments += '-dev' }
if ($DataDir) { $arguments += @('-data', $DataDir) }
& $binary @arguments
if ($LASTEXITCODE) { throw "Kestrel exited with $LASTEXITCODE" }

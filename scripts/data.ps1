param([Parameter(Mandatory)][ValidateSet('backup','restore')][string]$Action, [Parameter(Mandatory)][string]$Archive, [string]$DataDir = '')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$binary = Join-Path $taskRoot '.cache/bin/kestrel.exe'
$arguments = @('-root', $taskRoot, "-$Action", $Archive)
if ($DataDir) { $arguments += @('-data', $DataDir) }
& $binary @arguments
if ($LASTEXITCODE) { throw "Kestrel $Action failed" }

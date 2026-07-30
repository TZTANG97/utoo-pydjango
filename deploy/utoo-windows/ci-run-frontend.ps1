# GitLab CI entry: build qd_web_front then publish static (ASCII-only for WinPS 5.1)
$ErrorActionPreference = 'Stop'
try {
	[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
	$OutputEncoding = [Console]::OutputEncoding
} catch { }
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
$root = Get-UtooCiProjectRoot
Set-Location $root
Write-Host ("[ci] project root: {0}" -f $root)

$buildScript = Join-Path $root 'deploy\utoo-windows\ci-build-frontend.ps1'
$deployScript = Join-Path $root 'deploy\utoo-windows\ci-deploy-windows.ps1'
if (-not (Test-Path -LiteralPath $buildScript)) { throw ("Missing build script: {0}" -f $buildScript) }
if (-not (Test-Path -LiteralPath $deployScript)) { throw ("Missing deploy script: {0}" -f $deployScript) }

& $buildScript
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $deployScript
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'ci-run-frontend.ps1: OK'

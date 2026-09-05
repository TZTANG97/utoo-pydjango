# Build utoo-web-front then publish static to /var/www/utoo-web (P5)
$ErrorActionPreference = 'Stop'
try {
	[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
	$OutputEncoding = [Console]::OutputEncoding
} catch { }
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
$root = Get-UtooCiProjectRoot
Set-Location $root

$buildScript = Join-Path $root 'deploy\utoo-windows\ci-build-utoo-frontend.ps1'
$deployScript = Join-Path $root 'deploy\utoo-windows\ci-deploy-windows.ps1'
if (-not (Test-Path -LiteralPath $buildScript)) { throw ("Missing: {0}" -f $buildScript) }
if (-not (Test-Path -LiteralPath $deployScript)) { throw ("Missing: {0}" -f $deployScript) }

& $buildScript
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$env:QD_MALL_DEPLOY_PHASE = 'static_utoo'
$env:QD_MALL_DEPLOY_SERVICE = 'utoo_frontend'
& $deployScript
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'ci-run-utoo-frontend.ps1: OK'
exit 0

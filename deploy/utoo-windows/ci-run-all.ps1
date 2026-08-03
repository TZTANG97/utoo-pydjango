# GitLab CI: one-click full deploy (optimized). ASCII-only for WinPS 5.1.
# Backend: one libs_services (4 services synced + parallel remote pip/restart) -> gateway
# Frontend: build + static sync via ci-run-frontend.ps1 (reliable under LocalSystem runner)
$ErrorActionPreference = 'Stop'
try {
	[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
	$OutputEncoding = [Console]::OutputEncoding
} catch { }
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
$root = Get-UtooCiProjectRoot
Set-Location $root
Write-Host ("[ci] project root: {0}" -f $root)

$target = ($env:UTOO_DEPLOY_TARGET | ForEach-Object { "$_" }).Trim()
if ([string]::IsNullOrWhiteSpace($target)) { $target = 'dev' }
$env:UTOO_DEPLOY_TARGET = $target

$deployScript = Join-Path $root 'deploy\utoo-windows\ci-deploy-windows.ps1'
$frontendScript = Join-Path $root 'deploy\utoo-windows\ci-run-frontend.ps1'
if (-not (Test-Path -LiteralPath $deployScript)) { throw ("Missing deploy script: {0}" -f $deployScript) }
if (-not (Test-Path -LiteralPath $frontendScript)) { throw ("Missing frontend runner: {0}" -f $frontendScript) }

function Invoke-UtooDeployStep {
	param(
		[Parameter(Mandatory)][string]$Name,
		[Parameter(Mandatory)][string]$Phase,
		[Parameter(Mandatory)][string]$Service,
		[Parameter(Mandatory)][string]$ScriptPath,
		[string]$Kind = 'deploy'
	)
	$stepStart = Get-Date
	Write-Host ''
	Write-Host ('========== deploy {0} (phase={1}) ==========' -f $Name, $Phase) -ForegroundColor Cyan
	$env:UTOO_DEPLOY_PHASE = $Phase
	$env:UTOO_DEPLOY_SERVICE = $Service
	$global:LASTEXITCODE = 0
	try {
		& $ScriptPath
		$stepExit = 0
		if ($null -ne $LASTEXITCODE) { $stepExit = [int]$LASTEXITCODE }
	} catch {
		$elapsedFail = ((Get-Date) - $stepStart).TotalSeconds
		Write-Host ('[all] step FAILED: {0} after {1:N1}s' -f $Name, $elapsedFail) -ForegroundColor Red
		throw ("Step failed: {0}: {1}" -f $Name, $_.Exception.Message)
	}
	if ($stepExit -ne 0) {
		$elapsedFail = ((Get-Date) - $stepStart).TotalSeconds
		Write-Host ('[all] step FAILED: {0} exit={1} after {2:N1}s' -f $Name, $stepExit, $elapsedFail) -ForegroundColor Red
		throw ("Step failed: {0} (exit={1})" -f $Name, $stepExit)
	}
	$elapsedOk = ((Get-Date) - $stepStart).TotalSeconds
	# Frontend build alone is often >3s; backend phases must not "instant OK".
	$minSec = 3
	if ($Kind -eq 'frontend') { $minSec = 3 }
	if ($elapsedOk -lt $minSec) {
		throw ("Step suspiciously fast: {0} finished in {1:N2}s — deploy likely did not run" -f $Name, $elapsedOk)
	}
	Write-Host ('[all] step OK: {0} ({1:N1}s)' -f $Name, $elapsedOk) -ForegroundColor Green
}

$allStart = Get-Date

Invoke-UtooDeployStep -Name 'libs_services' -Phase 'libs_services' -Service 'all' -ScriptPath $deployScript
Invoke-UtooDeployStep -Name 'gateway' -Phase 'gateway' -Service 'gateway' -ScriptPath $deployScript
# ci-run-frontend.ps1 sets phase/static itself via env from caller — set before invoke
$env:UTOO_DEPLOY_PHASE = 'static'
$env:UTOO_DEPLOY_SERVICE = 'frontend'
Invoke-UtooDeployStep -Name 'frontend' -Phase 'static' -Service 'frontend' -ScriptPath $frontendScript -Kind 'frontend'

$totalSec = ((Get-Date) - $allStart).TotalSeconds
Write-Host ''
Write-Host ('ci-run-all.ps1: OK (target={0}, total={1:N1}s)' -f $target, $totalSec)
exit 0

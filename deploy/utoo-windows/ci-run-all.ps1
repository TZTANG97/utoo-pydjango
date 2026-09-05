# GitLab CI: one-click UTOO product deploy (P5).
# Mid-tier NEVER from this repo. Only: utoo_biz -> utoo_gateway -> utoo-web-front.
$ErrorActionPreference = 'Stop'
try {
	[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
	$OutputEncoding = [Console]::OutputEncoding
} catch { }
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
$root = Get-UtooCiProjectRoot
Set-Location $root
Write-Host ("[ci] project root: {0}" -f $root)

$target = ($env:QD_MALL_DEPLOY_TARGET | ForEach-Object { "$_" }).Trim()
if ([string]::IsNullOrWhiteSpace($target)) {
	$target = ($env:UTOO_DEPLOY_TARGET | ForEach-Object { "$_" }).Trim()
}
if ([string]::IsNullOrWhiteSpace($target)) { $target = 'dev' }
$env:QD_MALL_DEPLOY_TARGET = $target
$env:UTOO_DEPLOY_TARGET = $target

$deployScript = Join-Path $root 'deploy\utoo-windows\ci-deploy-windows.ps1'
$frontendScript = Join-Path $root 'deploy\utoo-windows\ci-run-utoo-frontend.ps1'
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
	$env:QD_MALL_DEPLOY_PHASE = $Phase
	$env:QD_MALL_DEPLOY_SERVICE = $Service
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
	$minSec = 3
	if ($elapsedOk -lt $minSec) {
		throw ("Step suspiciously fast: {0} finished in {1:N2}s — deploy likely did not run" -f $Name, $elapsedOk)
	}
	Write-Host ('[all] step OK: {0} ({1:N1}s)' -f $Name, $elapsedOk) -ForegroundColor Green
}

$allStart = Get-Date
Write-Host '[all][P5] mid-tier skipped (deploy from mall_qingdao_pydjango platform/* only)' -ForegroundColor Yellow
Invoke-UtooDeployStep -Name 'utoo_biz' -Phase 'service' -Service 'utoo_biz' -ScriptPath $deployScript
Invoke-UtooDeployStep -Name 'utoo_gateway' -Phase 'utoo_gateway' -Service 'utoo_gateway' -ScriptPath $deployScript
Invoke-UtooDeployStep -Name 'utoo_frontend' -Phase 'static_utoo' -Service 'utoo_frontend' -ScriptPath $frontendScript -Kind 'frontend'

$totalSec = ((Get-Date) - $allStart).TotalSeconds
Write-Host ''
Write-Host ('ci-run-all.ps1: OK (target={0}, total={1:N1}s)' -f $target, $totalSec)
exit 0

# GitLab CI: one-click full deploy (6 steps in order). ASCII-only for WinPS 5.1.
# Order: order -> payment -> admin_asset -> admin_platform -> gateway -> frontend
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

$steps = @(
	@{ Name = 'order'; Phase = 'service'; Service = 'order'; Kind = 'deploy' },
	@{ Name = 'payment'; Phase = 'service'; Service = 'payment'; Kind = 'deploy' },
	@{ Name = 'admin_asset'; Phase = 'service'; Service = 'admin_asset'; Kind = 'deploy' },
	@{ Name = 'admin_platform'; Phase = 'service'; Service = 'admin_platform'; Kind = 'deploy' },
	@{ Name = 'gateway'; Phase = 'gateway'; Service = 'gateway'; Kind = 'deploy' },
	@{ Name = 'frontend'; Phase = 'static'; Service = 'frontend'; Kind = 'frontend' }
)

$allStart = Get-Date
$i = 0
foreach ($step in $steps) {
	$i++
	$stepStart = Get-Date
	Write-Host ''
	Write-Host ('========== [{0}/{1}] deploy {2} (phase={3}) ==========' -f $i, $steps.Count, $step.Name, $step.Phase) -ForegroundColor Cyan
	$env:UTOO_DEPLOY_PHASE = [string]$step.Phase
	$env:UTOO_DEPLOY_SERVICE = [string]$step.Service
	# Reset so a stale native exit code cannot mask a pure-PS success/failure.
	$global:LASTEXITCODE = 0
	try {
		if ($step.Kind -eq 'frontend') {
			& $frontendScript
		} else {
			& $deployScript
		}
		$stepExit = 0
		if ($null -ne $LASTEXITCODE) { $stepExit = [int]$LASTEXITCODE }
	} catch {
		$elapsedFail = ((Get-Date) - $stepStart).TotalSeconds
		Write-Host ('[all] step FAILED: {0} after {1:N1}s' -f $step.Name, $elapsedFail) -ForegroundColor Red
		throw ("Step failed: {0}: {1}" -f $step.Name, $_.Exception.Message)
	}
	if ($stepExit -ne 0) {
		$elapsedFail = ((Get-Date) - $stepStart).TotalSeconds
		Write-Host ('[all] step FAILED: {0} exit={1} after {2:N1}s' -f $step.Name, $stepExit, $elapsedFail) -ForegroundColor Red
		throw ("Step failed: {0} (exit={1})" -f $step.Name, $stepExit)
	}
	$elapsedOk = ((Get-Date) - $stepStart).TotalSeconds
	# Guard against "instant OK" that never entered deploy (should be tens of seconds+ each).
	if ($elapsedOk -lt 3) {
		throw ("Step suspiciously fast: {0} finished in {1:N2}s — deploy likely did not run" -f $step.Name, $elapsedOk)
	}
	Write-Host ('[all] step OK: {0} ({1:N1}s)' -f $step.Name, $elapsedOk) -ForegroundColor Green
}

$totalSec = ((Get-Date) - $allStart).TotalSeconds
Write-Host ''
Write-Host ('ci-run-all.ps1: OK (target={0}, steps={1}, total={2:N1}s)' -f $target, $steps.Count, $totalSec)
exit 0

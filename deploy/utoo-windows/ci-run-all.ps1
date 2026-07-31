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

$i = 0
foreach ($step in $steps) {
	$i++
	Write-Host ''
	Write-Host ('========== [{0}/{1}] deploy {2} (phase={3}) ==========' -f $i, $steps.Count, $step.Name, $step.Phase) -ForegroundColor Cyan
	$env:UTOO_DEPLOY_PHASE = [string]$step.Phase
	$env:UTOO_DEPLOY_SERVICE = [string]$step.Service
	if ($step.Kind -eq 'frontend') {
		& $frontendScript
	} else {
		& $deployScript
	}
	if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) {
		throw ("Step failed: {0} (exit={1})" -f $step.Name, $LASTEXITCODE)
	}
	Write-Host ('[all] step OK: {0}' -f $step.Name) -ForegroundColor Green
}

Write-Host ''
Write-Host ('ci-run-all.ps1: OK (target={0}, steps={1})' -f $target, $steps.Count)

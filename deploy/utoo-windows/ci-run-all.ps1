# GitLab CI: one-click full deploy (optimized). ASCII-only for WinPS 5.1.
# Backend: one libs_services (4 services synced + parallel remote pip/restart) -> gateway
# Frontend: npm build overlaps with backend; then static sync only.
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
$frontendBuildScript = Join-Path $root 'deploy\utoo-windows\ci-build-frontend.ps1'
if (-not (Test-Path -LiteralPath $deployScript)) { throw ("Missing deploy script: {0}" -f $deployScript) }
if (-not (Test-Path -LiteralPath $frontendBuildScript)) { throw ("Missing frontend build: {0}" -f $frontendBuildScript) }

function Invoke-UtooDeployStep {
	param(
		[Parameter(Mandatory)][string]$Name,
		[Parameter(Mandatory)][string]$Phase,
		[Parameter(Mandatory)][string]$Service,
		[Parameter(Mandatory)][string]$ScriptPath
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
	if ($elapsedOk -lt 3) {
		throw ("Step suspiciously fast: {0} finished in {1:N2}s — deploy likely did not run" -f $Name, $elapsedOk)
	}
	Write-Host ('[all] step OK: {0} ({1:N1}s)' -f $Name, $elapsedOk) -ForegroundColor Green
}

$allStart = Get-Date

# Overlap npm build with backend deploy (biggest wall-clock win for full release).
$feOut = Join-Path $env:TEMP ('utoo_fe_build_out_{0}.log' -f $PID)
$feErr = Join-Path $env:TEMP ('utoo_fe_build_err_{0}.log' -f $PID)
Write-Host ('[all] start frontend build in background -> {0}' -f $feOut) -ForegroundColor Cyan
$feProc = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
	'-NoProfile',
	'-ExecutionPolicy', 'Bypass',
	'-File', $frontendBuildScript
) -WorkingDirectory $root -PassThru -NoNewWindow `
	-RedirectStandardOutput $feOut -RedirectStandardError $feErr

try {
	Invoke-UtooDeployStep -Name 'libs_services' -Phase 'libs_services' -Service 'all' -ScriptPath $deployScript
	Invoke-UtooDeployStep -Name 'gateway' -Phase 'gateway' -Service 'gateway' -ScriptPath $deployScript

	Write-Host ''
	Write-Host '[all] wait frontend build...' -ForegroundColor Cyan
	$feWaitStart = Get-Date
	Wait-Process -Id $feProc.Id
	$feBuildSec = ((Get-Date) - $feWaitStart).TotalSeconds
	$feCode = 0
	if ($null -ne $feProc.ExitCode) { $feCode = [int]$feProc.ExitCode }
	if ($feCode -ne 0) {
		Write-Host '----- frontend build stdout -----' -ForegroundColor Yellow
		if (Test-Path -LiteralPath $feOut) { Get-Content -LiteralPath $feOut -ErrorAction SilentlyContinue }
		Write-Host '----- frontend build stderr -----' -ForegroundColor Yellow
		if (Test-Path -LiteralPath $feErr) { Get-Content -LiteralPath $feErr -ErrorAction SilentlyContinue }
		throw ("Frontend build failed (exit={0})" -f $feCode)
	}
	Write-Host ('[all] frontend build OK (waited {0:N1}s after backend; see {1})' -f $feBuildSec, $feOut) -ForegroundColor Green

	Invoke-UtooDeployStep -Name 'frontend' -Phase 'static' -Service 'frontend' -ScriptPath $deployScript
} finally {
	if ($feProc -and -not $feProc.HasExited) {
		try { Stop-Process -Id $feProc.Id -Force -ErrorAction SilentlyContinue } catch { }
	}
}

$totalSec = ((Get-Date) - $allStart).TotalSeconds
Write-Host ''
Write-Host ('ci-run-all.ps1: OK (target={0}, total={1:N1}s)' -f $target, $totalSec)
exit 0

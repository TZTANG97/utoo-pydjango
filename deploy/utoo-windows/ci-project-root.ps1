# Resolve repo root in GitLab CI (Windows bash runner may set wrong CI_PROJECT_DIR).
function Get-UtooCiProjectRoot {
	$fromScript = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
	$cwd = (Get-Location).Path

	function Test-RepoRoot([string]$Path) {
		if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
		return (Test-Path -LiteralPath (Join-Path $Path '.git')) -or
			(Test-Path -LiteralPath (Join-Path $Path 'deploy\utoo-windows\ci-build-frontend.ps1')) -or
			(Test-Path -LiteralPath (Join-Path $Path 'qd_test_server_django'))
	}

	if (Test-RepoRoot $cwd) { return [IO.Path]::GetFullPath($cwd) }
	if (Test-RepoRoot $fromScript) { return $fromScript }

	$ci = $env:CI_PROJECT_DIR
	if (-not [string]::IsNullOrWhiteSpace($ci)) {
		$ci = $ci.Trim().TrimEnd('\', '/')
		if (Test-RepoRoot $ci) {
			return [IO.Path]::GetFullPath($ci)
		}
		Write-Host "[ci] ignore invalid CI_PROJECT_DIR: $ci" -ForegroundColor Yellow
	}

	return $fromScript
}

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

	# Prefer GitLab checkout dir — shell executor may leave cwd on an unrelated local clone.
	$ci = $env:CI_PROJECT_DIR
	if (-not [string]::IsNullOrWhiteSpace($ci)) {
		$ci = $ci.Trim().TrimEnd('\', '/')
		if (Test-RepoRoot $ci) {
			Write-Host ("[ci] project root from CI_PROJECT_DIR: {0}" -f $ci)
			return [IO.Path]::GetFullPath($ci)
		}
		Write-Host "[ci] ignore invalid CI_PROJECT_DIR: $ci" -ForegroundColor Yellow
	}

	if (Test-RepoRoot $cwd) { return [IO.Path]::GetFullPath($cwd) }
	if (Test-RepoRoot $fromScript) { return $fromScript }

	return $fromScript
}

# Resolve utoo monorepo root under GitLab CI (Windows).
# P5: also exposes Get-QdMallCiProjectRoot alias for scripts copied from mall deploy.
function Get-UtooCiProjectRoot {
	$fromScript = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
	$cwd = (Get-Location).Path
	$inCi = ($env:CI -eq 'true') -or (-not [string]::IsNullOrWhiteSpace($env:CI_JOB_ID))

	function Test-RepoRoot([string]$Path) {
		if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
		try {
			$full = [IO.Path]::GetFullPath($Path.Trim().TrimEnd('\', '/'))
		} catch {
			return $false
		}
		return (Test-Path -LiteralPath (Join-Path $full '.git')) -or
			(Test-Path -LiteralPath (Join-Path $full 'deploy\utoo-windows\ci-deploy-windows.ps1')) -or
			(Test-Path -LiteralPath (Join-Path $full 'platform\utoo_gateway\manage.py')) -or
			(Test-Path -LiteralPath (Join-Path $full 'utoo-web-front\package.json'))
	}

	function Assert-CiCheckout([string]$Root) {
		$sha = ($env:CI_COMMIT_SHA | ForEach-Object { "$_" }).Trim()
		if ([string]::IsNullOrWhiteSpace($sha)) { return }
		$git = Join-Path $Root '.git'
		if (-not (Test-Path -LiteralPath $git)) {
			Write-Warning "[ci] root has no .git; skip HEAD vs CI_COMMIT_SHA check: $Root"
			return
		}
		Push-Location $Root
		try {
			$head = (& git rev-parse HEAD 2>$null | ForEach-Object { "$_" }).Trim()
			if ([string]::IsNullOrWhiteSpace($head)) {
				throw "git rev-parse HEAD failed under $Root"
			}
			if (-not [string]::Equals($head, $sha, [StringComparison]::OrdinalIgnoreCase)) {
				throw ("Refusing deploy from wrong checkout: HEAD={0} CI_COMMIT_SHA={1} root={2}" -f $head, $sha, $Root)
			}
			Write-Host ("[ci] HEAD matches CI_COMMIT_SHA={0}" -f $sha)
		} finally {
			Pop-Location
		}
	}

	if (Test-RepoRoot $cwd) {
		$full = [IO.Path]::GetFullPath($cwd)
		Write-Host ("[ci] project root from cwd: {0}" -f $full)
		if ($inCi) { Assert-CiCheckout $full }
		return $full
	}
	if (Test-RepoRoot $fromScript) {
		Write-Host ("[ci] project root from script path: {0}" -f $fromScript)
		if ($inCi) { Assert-CiCheckout $fromScript }
		return $fromScript
	}

	$ci = $env:CI_PROJECT_DIR
	if (-not [string]::IsNullOrWhiteSpace($ci)) {
		$ci = $ci.Trim().TrimEnd('\', '/')
		if (Test-RepoRoot $ci) {
			$full = [IO.Path]::GetFullPath($ci)
			Write-Host ("[ci] project root from CI_PROJECT_DIR: {0}" -f $full)
			if ($inCi) { Assert-CiCheckout $full }
			return $full
		}
		Write-Host "[ci] ignore invalid CI_PROJECT_DIR: $ci" -ForegroundColor Yellow
	}

	if ($inCi) {
		throw 'Cannot resolve utoo repo root under GitLab CI'
	}
	return $fromScript
}

function Get-QdMallCiProjectRoot {
	# Alias for mall-origin scripts running inside utoo-pydjango (P5).
	return Get-UtooCiProjectRoot
}

# GitLab CI：构建统一前端 qd_web_front（C 端 + 管理后台单 SPA）
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
$jobCwd = (Get-Location).Path
$root = Get-UtooCiProjectRoot
Set-Location $root
Write-Host "[ci] project root: $root"

$feDir = 'qd_web_front'
$target = Join-Path $root $feDir
if (-not (Test-Path -LiteralPath (Join-Path $target 'package.json'))) {
	Write-Error "No package.json under $target"
	exit 1
}

Set-Location $target
Write-Host ("[ci] build unified front in {0}" -f (Get-Location))

@(
	'VITE_APP_BASE_API=/api',
	'VITE_API_MODE=django'
) | Set-Content -LiteralPath (Join-Path $target '.env.production') -Encoding utf8
Write-Host '[ci] wrote qd_web_front/.env.production'

if (Test-Path -LiteralPath (Join-Path $target 'package-lock.json')) {
	& npm ci
} else {
	& npm install
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& npm run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not [string]::IsNullOrWhiteSpace($jobCwd)) {
	try {
		$jobTarget = Join-Path $jobCwd $feDir
		$srcDist = Join-Path $target 'dist'
		if (Test-Path -LiteralPath $srcDist) {
			$srcNorm = [System.IO.Path]::GetFullPath($srcDist)
			$dstDist = Join-Path $jobTarget 'dist'
			$dstNorm = [System.IO.Path]::GetFullPath($dstDist)
			if (-not [string]::Equals($srcNorm, $dstNorm, [System.StringComparison]::OrdinalIgnoreCase)) {
				New-Item -ItemType Directory -Force -Path $jobTarget | Out-Null
				if (Test-Path -LiteralPath $dstDist) {
					Remove-Item -LiteralPath $dstDist -Recurse -Force -ErrorAction SilentlyContinue
				}
				Copy-Item -LiteralPath $srcDist -Destination $dstDist -Recurse -Force
				Write-Host "Mirrored dist to: $dstNorm"
			}
		}
	} catch {
		Write-Warning ("Mirror dist failed: " + $_.Exception.Message)
	}
}

Set-Location $root
Write-Host 'ci-build-frontend.ps1: OK'

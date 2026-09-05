# GitLab CI: build utoo-web-front (P5)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
$jobCwd = (Get-Location).Path
$root = Get-QdMallCiProjectRoot
Set-Location $root
Write-Host "[ci] project root: $root"

$feDir = 'utoo-web-front'
$target = Join-Path $root $feDir
if (-not (Test-Path -LiteralPath (Join-Path $target 'package.json'))) {
	Write-Error "No package.json under $target"
	exit 1
}

Set-Location $target
Write-Host ("[ci] build utoo-web-front in {0}" -f (Get-Location))

$distDir = Join-Path $target 'dist'
if (Test-Path -LiteralPath $distDir) {
	Remove-Item -LiteralPath $distDir -Recurse -Force
	Write-Host '[ci] removed stale utoo-web-front/dist'
}

$commitSha = (($env:CI_COMMIT_SHA | ForEach-Object { "$_" }).Trim())
if ([string]::IsNullOrWhiteSpace($commitSha)) {
	Push-Location $root
	try { $commitSha = (& git rev-parse HEAD 2>$null | ForEach-Object { "$_" }).Trim() } finally { Pop-Location }
}
if ([string]::IsNullOrWhiteSpace($commitSha)) { $commitSha = 'unknown' }

@(
	'VITE_APP_BASE_API=/api',
	'VITE_API_MODE=django',
	("VITE_BUILD_ID={0}" -f $commitSha)
) | Set-Content -LiteralPath (Join-Path $target '.env.production') -Encoding utf8
Write-Host ('[ci] wrote utoo-web-front/.env.production buildId={0}' -f $commitSha)

if (Test-Path -LiteralPath (Join-Path $target 'package-lock.json')) {
	& npm ci
} else {
	& npm install
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& npm run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$indexHtml = Join-Path $distDir 'index.html'
if (-not (Test-Path -LiteralPath $indexHtml)) {
	Write-Error "UTOO frontend build produced no dist/index.html"
	exit 1
}

$buildInfo = @{
	commit = $commitSha
	builtAt = (Get-Date).ToString('o')
	root = $root
	jobId = (($env:CI_JOB_ID | ForEach-Object { "$_" }).Trim())
	product = 'utoo-web-front'
} | ConvertTo-Json -Compress
$buildInfoPath = Join-Path $distDir 'build-info.json'
[IO.File]::WriteAllText($buildInfoPath, $buildInfo, [Text.UTF8Encoding]::new($false))
Write-Host ("[ci] wrote {0}" -f $buildInfoPath)

if (-not [string]::IsNullOrWhiteSpace($jobCwd)) {
	try {
		$jobTarget = Join-Path $jobCwd $feDir
		$srcDist = Join-Path $target 'dist'
		if (Test-Path -LiteralPath $srcDist) {
			$srcNorm = [System.IO.Path]::GetFullPath($srcDist)
			$dstDist = Join-Path $jobTarget 'dist'
			$dstNorm = [System.IO.Path]::GetFullPath($dstDist)
			if (-not [string]::Equals($srcNorm, $dstNorm, [StringComparison]::OrdinalIgnoreCase)) {
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
Write-Host 'ci-build-utoo-frontend.ps1: OK'
exit 0

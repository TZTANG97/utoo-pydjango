# GitLab CI: build qd_web_front (C + admin SPA)
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

# Always rebuild into a clean dist — stale dist was previously uploaded when build was skipped/mis-rooted.
$distDir = Join-Path $target 'dist'
if (Test-Path -LiteralPath $distDir) {
	Remove-Item -LiteralPath $distDir -Recurse -Force
	Write-Host '[ci] removed stale qd_web_front/dist'
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
Write-Host ('[ci] wrote qd_web_front/.env.production buildId={0}' -f $commitSha)

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
	Write-Error "Frontend build produced no dist/index.html under $distDir"
	exit 1
}
$indexText = Get-Content -LiteralPath $indexHtml -Raw -Encoding utf8
if ($indexText -notmatch 'assets/index-[^"\.]+\.js') {
	Write-Error 'dist/index.html missing hashed assets/index-*.js entry'
	exit 1
}

# Stamp the exact commit into dist so deploy can refuse uploading an unrelated/old package.
$buildInfo = @{
	commit = $commitSha
	builtAt = (Get-Date).ToString('o')
	root = $root
	jobId = (($env:CI_JOB_ID | ForEach-Object { "$_" }).Trim())
} | ConvertTo-Json -Compress
$buildInfoPath = Join-Path $distDir 'build-info.json'
[IO.File]::WriteAllText($buildInfoPath, $buildInfo, [Text.UTF8Encoding]::new($false))
Write-Host ("[ci] wrote {0}" -f $buildInfoPath)

# Keep markers that survive Vite minify (prefer URL/path string literals, not exported fn names).
$markerNeedles = @(
	'ServiceConsultDetail',
	'warehouse-config',
	'InventoryWarehouseConfig',
	'updateAccessRightsQuery.ajax',
	'addUserExpManage.ajax',
	'grab-orders'
)
$assetFiles = Get-ChildItem -LiteralPath (Join-Path $distDir 'assets') -Filter '*.js' -ErrorAction Stop
$joined = ''
foreach ($f in $assetFiles) {
	$joined += [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::UTF8)
}
$joined += $indexText
$joined += $buildInfo
foreach ($needle in $markerNeedles) {
	if ($joined.IndexOf($needle, [StringComparison]::Ordinal) -lt 0) {
		Write-Error ("Frontend dist missing expected marker '{0}' — refusing to publish stale/wrong build (root={1})" -f $needle, $root)
		exit 1
	}
}
# Commit stamp lives in build-info.json (already included above).
if ($commitSha -ne 'unknown' -and $buildInfo.IndexOf($commitSha, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
	Write-Error ("build-info.json missing CI_COMMIT_SHA {0}" -f $commitSha)
	exit 1
}
Write-Host '[ci] dist marker check OK'

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

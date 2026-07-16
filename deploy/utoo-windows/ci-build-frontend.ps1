# GitLab CI：构建 C 端 + 管理后台前端（npm + package-lock）
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
$jobCwd = (Get-Location).Path
$root = Get-UtooCiProjectRoot
Set-Location $root
Write-Host "[ci] project root: $root"

$frontends = @(
	@{ Dir = 'qd_test_front_v3'; Name = 'C-front' },
	@{ Dir = 'qd_admin_front'; Name = 'admin-front' }
)

foreach ($fe in $frontends) {
	$target = Join-Path $root $fe.Dir
	if (-not (Test-Path -LiteralPath (Join-Path $target 'package.json'))) {
		Write-Error "No package.json under $target"
		exit 1
	}
	Set-Location $target
	Write-Host ("[ci] build {0} in {1}" -f $fe.Name, (Get-Location))

	if (Test-Path -LiteralPath (Join-Path $target 'package-lock.json')) {
		& npm ci
	} else {
		& npm install
	}
	if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

	& npm run build
	if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

	# Windows runner 偶发 artifacts 基准目录与检出根不一致，镜像一份到 job cwd
	if (-not [string]::IsNullOrWhiteSpace($jobCwd)) {
		try {
			$jobTarget = Join-Path $jobCwd $fe.Dir
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
}

Set-Location $root
Write-Host 'ci-build-frontend.ps1: OK'

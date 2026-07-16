# GitLab CI：Windows Shell Runner + OpenSSH → Linux systemd
# 微服务模式：6 上游 + 网关 + 双前端静态（无蓝绿）
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
$root = Get-UtooCiProjectRoot
Set-Location $root
Write-Host "[ci] project root: $root"

$env:MSYS2_ARG_CONV_EXCL = '*'
$env:MSYS_NO_PATHCONV = '1'
$script:UtooSshExe = Join-Path $env:SystemRoot 'System32\OpenSSH\ssh.exe'
if (-not (Test-Path -LiteralPath $script:UtooSshExe)) { $script:UtooSshExe = 'ssh' }
$script:UtooScpExe = Join-Path $env:SystemRoot 'System32\OpenSSH\scp.exe'
if (-not (Test-Path -LiteralPath $script:UtooScpExe)) { $script:UtooScpExe = 'scp' }

function Protect-LinuxPath([string]$Path) {
	if ([string]::IsNullOrWhiteSpace($Path)) { return $Path }
	$t = $Path.Trim().TrimEnd('/')
	if ($t -notmatch '^/') { $t = '/' + $t }
	while ($t.Contains('//')) { $t = $t.Replace('//', '/') }
	return $t
}

function Normalize-DeployLinuxPath {
	param([string]$Value, [string]$DefaultIfEmpty = '')
	if ([string]::IsNullOrWhiteSpace($Value)) {
		if ([string]::IsNullOrWhiteSpace($DefaultIfEmpty)) { return $Value }
		return Protect-LinuxPath $DefaultIfEmpty
	}
	$v = $Value.Trim().Trim('"')
	if ($v -match '(?i)Program Files[/\\]Git[/\\](.+)') {
		$rest = ($Matches[1] -replace '\\', '/').Trim()
		if ($rest -notmatch '^/') { $rest = '/' + $rest }
		return Protect-LinuxPath $rest
	}
	if ($v -match '^[A-Za-z]:[/\\]' -and -not [string]::IsNullOrWhiteSpace($DefaultIfEmpty)) {
		return Protect-LinuxPath $DefaultIfEmpty
	}
	return Protect-LinuxPath $v
}

function Get-CiEnv([string]$Name) {
	if (-not (Test-Path "env:$Name")) { return $null }
	(Get-Item "env:$Name").Value
}

function Resolve-DeployTarget {
	$t = Get-CiEnv 'UTOO_DEPLOY_TARGET'
	if (-not [string]::IsNullOrWhiteSpace($t)) { return $t.Trim().ToLowerInvariant() }
	$jn = Get-CiEnv 'CI_JOB_NAME'
	if ($jn -eq 'deploy_prod') { return 'prod' }
	if ($jn -eq 'deploy_dev') { return 'dev' }
	$ref = Get-CiEnv 'CI_COMMIT_REF_NAME'
	if ($ref -eq 'prod') { return 'prod' }
	return 'dev'
}

function Get-BranchAwareEnv([string]$BaseName) {
	$target = Resolve-DeployTarget
	foreach ($n in @("${BaseName}_$($target.ToUpperInvariant())", $BaseName)) {
		$v = Get-CiEnv $n
		if (-not [string]::IsNullOrWhiteSpace($v)) {
			Write-Host ("[deploy] env {0} from {1}" -f $BaseName, $n)
			return $v
		}
	}
	return $null
}

# --- local deploy env (optional, not committed) ---
$deployTarget = Resolve-DeployTarget
$ciLocal = Join-Path $root 'deploy/ci-local'
$localCandidates = @(
	'C:\ProgramData\utoo-deploy.env.ps1',
	("C:\ProgramData\utoo-deploy-{0}.env.ps1" -f $deployTarget),
	(Join-Path $ciLocal ("utoo-deploy-{0}.env.ps1" -f $deployTarget))
)
foreach ($f in $localCandidates) {
	if (Test-Path -LiteralPath $f) {
		. $f
		Write-Host ("[deploy] loaded local env: {0}" -f $f) -ForegroundColor DarkGreen
		break
	}
}

$DeployUser = Get-BranchAwareEnv 'DEPLOY_USER'
$deployHost = Get-BranchAwareEnv 'DEPLOY_HOST'
$sshKey = Get-BranchAwareEnv 'SSH_PRIVATE_KEY'
if ([string]::IsNullOrWhiteSpace($DeployUser) -or [string]::IsNullOrWhiteSpace($deployHost) -or [string]::IsNullOrWhiteSpace($sshKey)) {
	Write-Error @"
Missing deploy variables. Set GitLab CI/CD Variables (or deploy/ci-local/utoo-deploy-$deployTarget.env.ps1):
  DEPLOY_USER / DEPLOY_USER_DEV / DEPLOY_USER_PROD
  DEPLOY_HOST / DEPLOY_HOST_DEV / DEPLOY_HOST_PROD
  SSH_PRIVATE_KEY / SSH_PRIVATE_KEY_DEV / SSH_PRIVATE_KEY_PROD
"@
	exit 1
}

$RemoteRoot = Normalize-DeployLinuxPath (Get-CiEnv 'UTOO_REMOTE_ROOT') '/opt/utoo'
$StaticC = Normalize-DeployLinuxPath (Get-CiEnv 'UTOO_STATIC_C') '/var/www/utoo-c'
$StaticAdmin = Normalize-DeployLinuxPath (Get-CiEnv 'UTOO_STATIC_ADMIN') '/var/www/utoo-admin'

# 上游微服务（不含网关）
$UpstreamUnits = @(
	@{ Dir = 'qd_svc_auth'; Service = 'qd-auth'; Port = 18081 },
	@{ Dir = 'qd_svc_order'; Service = 'qd-order'; Port = 18082 },
	@{ Dir = 'qd_svc_payment'; Service = 'qd-payment'; Port = 18084 },
	@{ Dir = 'qd_svc_wx'; Service = 'qd-wx'; Port = 18087 },
	@{ Dir = 'qd_svc_admin_asset'; Service = 'qd-admin-asset'; Port = 18090 },
	@{ Dir = 'qd_svc_admin_platform'; Service = 'qd-admin-platform'; Port = 18091 }
)
$GatewayUnit = @{ Dir = 'qd_test_server_django'; Service = 'qd-gateway'; Port = 18083 }

# libs_services | gateway | static | all（默认 all，兼容旧单 Job）
$DeployPhase = (Get-CiEnv 'UTOO_DEPLOY_PHASE')
if ([string]::IsNullOrWhiteSpace($DeployPhase)) { $DeployPhase = 'all' }
$DeployPhase = $DeployPhase.Trim().ToLowerInvariant()
$validPhases = @('libs_services', 'gateway', 'static', 'all')
if ($validPhases -notcontains $DeployPhase) {
	Write-Error ("Invalid UTOO_DEPLOY_PHASE={0}. Use: {1}" -f $DeployPhase, ($validPhases -join ', '))
	exit 1
}

Write-Host ("[deploy] target={0} host={1}@{2} root={3} phase={4}" -f $deployTarget, $DeployUser, $deployHost, $RemoteRoot, $DeployPhase)

# --- SSH key / known_hosts ---
$keyFile = Join-Path $env:TEMP ("gitlab_ci_utoo_key_{0}" -f [Guid]::NewGuid().ToString('N'))
$knownHostsFile = Join-Path $env:TEMP ("gitlab_ci_utoo_kh_{0}" -f [Guid]::NewGuid().ToString('N'))
try {
	$normalizedKey = ($sshKey -replace "`r`n", "`n" -replace "`r", "`n").Trim() + "`n"
	[IO.File]::WriteAllText($keyFile, $normalizedKey, [Text.UTF8Encoding]::new($false))
	icacls $keyFile /inheritance:r | Out-Null
	icacls $keyFile /grant:r "${env:USERNAME}:(R)" | Out-Null

	$kh = Get-BranchAwareEnv 'SSH_KNOWN_HOSTS'
	if ([string]::IsNullOrWhiteSpace($kh)) {
		$scan = & ssh-keyscan -T 20 -t rsa,ecdsa,ed25519 -H $deployHost 2>$null
		if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($scan | Out-String))) {
			Write-Error "ssh-keyscan failed for $deployHost"
			exit 1
		}
		$scan | Set-Content -LiteralPath $knownHostsFile -Encoding ascii
	} else {
		$kh | Set-Content -LiteralPath $knownHostsFile -Encoding ascii
	}

	$SshArgs = @(
		'-i', $keyFile,
		'-o', 'IdentitiesOnly=yes',
		'-o', "UserKnownHostsFile=$knownHostsFile",
		'-o', 'StrictHostKeyChecking=yes',
		'-o', 'BatchMode=yes'
	)
	$SshTarget = "$DeployUser@$deployHost"

	function Invoke-Remote([string]$RemoteCmd) {
		& $script:UtooSshExe @SshArgs $SshTarget $RemoteCmd
		if ($LASTEXITCODE -ne 0) { throw "Remote command failed (exit $LASTEXITCODE): $RemoteCmd" }
	}
	function Invoke-RemoteSudo([string]$RemoteCmd) {
		$escaped = $RemoteCmd -replace "'", "'\''"
		$cmd = "sudo -n bash -c '$escaped'"
		& $script:UtooSshExe @SshArgs $SshTarget $cmd
		if ($LASTEXITCODE -ne 0) {
			& $script:UtooSshExe @SshArgs $SshTarget $RemoteCmd
			if ($LASTEXITCODE -ne 0) { throw "Remote sudo/cmd failed (exit $LASTEXITCODE): $RemoteCmd" }
		}
	}
	function Invoke-Scp([string]$LocalPath, [string]$RemotePath) {
		& $script:UtooScpExe @SshArgs $LocalPath "${SshTarget}:$RemotePath"
		if ($LASTEXITCODE -ne 0) { throw "scp failed: $LocalPath -> $RemotePath" }
	}
	function Get-UtooPackTarExe {
		$winTar = Join-Path $env:SystemRoot 'System32\tar.exe'
		if (Test-Path -LiteralPath $winTar) { return $winTar }
		throw 'Windows System32\tar.exe not found'
	}
	function Invoke-TarPack([string]$ArchiveFile, [string]$WorkingDirectory, [string[]]$Exclude = @()) {
		$tar = Get-UtooPackTarExe
		$archiveFull = [IO.Path]::GetFullPath($ArchiveFile)
		Push-Location $WorkingDirectory
		try {
			$args = @('-cf', $archiveFull)
			foreach ($ex in $Exclude) { $args += "--exclude=$ex" }
			$args += '.'
			& $tar @args
			if ($LASTEXITCODE -ne 0) { throw "tar pack failed in $WorkingDirectory" }
		} finally { Pop-Location }
	}
	function Invoke-RemoteBashScript([string]$LocalScriptPath, [hashtable]$Replacements) {
		$text = [IO.File]::ReadAllText($LocalScriptPath)
		foreach ($k in $Replacements.Keys) { $text = $text.Replace($k, [string]$Replacements[$k]) }
		$remoteSh = "/tmp/utoo_ci_{0}.sh" -f [Guid]::NewGuid().ToString('N')
		$localSh = Join-Path $env:TEMP ("utoo_ci_{0}.sh" -f [Guid]::NewGuid().ToString('N'))
		try {
			$unix = ($text -replace "`r`n", "`n" -replace "`r", "`n")
			[IO.File]::WriteAllText($localSh, $unix, [Text.UTF8Encoding]::new($false))
			Invoke-Scp -LocalPath $localSh -RemotePath $remoteSh
			Invoke-RemoteSudo ("bash {0}; ec=`$?; rm -f {0}; exit `$ec" -f $remoteSh)
		} finally {
			Remove-Item -LiteralPath $localSh -Force -ErrorAction SilentlyContinue
		}
	}

	function Sync-DirToRemote([string]$LocalDir, [string]$RemoteDir, [string[]]$Exclude, [string[]]$PreserveNames) {
		$preserveExpr = ($PreserveNames | ForEach-Object { "-not -name $_" }) -join ' '
		if ([string]::IsNullOrWhiteSpace($preserveExpr)) { $preserveExpr = '-not -name .keep' }
		Invoke-RemoteSudo ("mkdir -p {0} && find {0} -mindepth 1 -maxdepth 1 {1} -print0 | xargs -0r rm -rf" -f $RemoteDir, $preserveExpr)
		$tarLocal = Join-Path $env:TEMP ("utoo_sync_{0}.tar" -f [Guid]::NewGuid().ToString('N'))
		$tarRemote = "/tmp/utoo_sync_{0}.tar" -f [Guid]::NewGuid().ToString('N')
		try {
			Invoke-TarPack -ArchiveFile $tarLocal -WorkingDirectory $LocalDir -Exclude $Exclude
			Invoke-Scp -LocalPath $tarLocal -RemotePath $tarRemote
			Invoke-RemoteSudo ("mkdir -p {0} && tar -xf {1} -C {0} && chown -R {2}:{2} {0} && rm -f {1}" -f $RemoteDir, $tarRemote, $DeployUser)
		} finally {
			Remove-Item -LiteralPath $tarLocal -Force -ErrorAction SilentlyContinue
		}
	}

	function Deploy-DjangoUnit {
		param(
			[Parameter(Mandatory)][hashtable]$Unit
		)
		$dir = $Unit.Dir
		$svc = $Unit.Service
		$port = $Unit.Port
		$localDir = Join-Path $root $dir
		if (-not (Test-Path -LiteralPath $localDir)) {
			throw "Local service directory missing: $localDir"
		}
		$remoteDir = "{0}/{1}" -f $RemoteRoot, $dir
		$healthUrl = "http://127.0.0.1:{0}/health" -f $port

		Write-Host ("[deploy] === {0} ({1} :{2}) ===" -f $dir, $svc, $port) -ForegroundColor Cyan

		Write-Host ("[deploy] sync {0}..." -f $dir)
		Sync-DirToRemote `
			-LocalDir $localDir `
			-RemoteDir $remoteDir `
			-Exclude @('.venv', '__pycache__', '*.pyc', '.git', '.env', '.env.local', 'tests', '.pytest_cache') `
			-PreserveNames @('.venv', '.env', '.env.local')

		$envCheck = ("if [ ! -f {0}/.env ] && [ ! -f {1}/config/shared-database.env ]; then echo deploy_error_missing_env:{2}; exit 1; fi" -f $remoteDir, $RemoteRoot, $dir)
		Invoke-Remote $envCheck

		Write-Host ("[deploy] pip {0}..." -f $dir)
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-pip-install.sh') -Replacements @{
			'__ROOT__' = $RemoteRoot
			'__SVC_DIR__' = $dir
		}
		Write-Host ("[deploy] django check {0}..." -f $dir)
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-smoke.sh') -Replacements @{
			'__ROOT__' = $RemoteRoot
			'__SVC_DIR__' = $dir
		}

		Write-Host ("[deploy] systemctl restart {0}" -f $svc)
		Invoke-RemoteSudo ("systemctl restart {0}" -f $svc)
		$healthWait = ('j=1; while [ $j -le 60 ]; do if curl -sf "{0}" >/dev/null; then echo deploy_health_ok:{1}; exit 0; fi; sleep 2; j=$((j+1)); done; echo deploy_health_fail:{1} >&2; systemctl --no-pager status {1} -l || true; journalctl -u {1} -n 80 --no-pager || true; exit 1' -f $healthUrl, $svc)
		Invoke-RemoteSudo $healthWait
	}

	$doLibsServices = ($DeployPhase -eq 'all' -or $DeployPhase -eq 'libs_services')
	$doGateway = ($DeployPhase -eq 'all' -or $DeployPhase -eq 'gateway')
	$doStatic = ($DeployPhase -eq 'all' -or $DeployPhase -eq 'static')

	if ($doLibsServices) {
		Write-Host '[deploy] sync qd_libs_common...'
		Sync-DirToRemote `
			-LocalDir (Join-Path $root 'qd_libs_common') `
			-RemoteDir ("{0}/qd_libs_common" -f $RemoteRoot) `
			-Exclude @('.venv', '__pycache__', '*.pyc', '.git', '*.egg-info') `
			-PreserveNames @('.keep')
		Invoke-RemoteSudo ("mkdir -p {0}/config" -f $RemoteRoot)
		foreach ($unit in $UpstreamUnits) {
			Deploy-DjangoUnit -Unit $unit
		}
		Write-Host '[deploy] phase libs_services done.'
	}

	if ($doGateway) {
		Deploy-DjangoUnit -Unit $GatewayUnit
		Write-Host '[deploy] phase gateway done.'
	}

	if ($doStatic) {
		$cDist = Join-Path $root 'qd_test_front_v3/dist'
		$aDist = Join-Path $root 'qd_admin_front/dist'
		if (-not (Test-Path -LiteralPath $cDist)) { Write-Error "Missing $cDist — run build_frontend_* first"; exit 1 }
		if (-not (Test-Path -LiteralPath $aDist)) { Write-Error "Missing $aDist — run build_frontend_* first"; exit 1 }
		Write-Host '[deploy] sync C-front static...'
		Sync-DirToRemote -LocalDir $cDist -RemoteDir $StaticC -Exclude @() -PreserveNames @('.keep')
		Write-Host '[deploy] sync admin-front static...'
		Sync-DirToRemote -LocalDir $aDist -RemoteDir $StaticAdmin -Exclude @() -PreserveNames @('.keep')
		Write-Host '[deploy] phase static done.'
	}

	Write-Host ("utoo deploy phase={0} finished OK." -f $DeployPhase)
} finally {
	Remove-Item -LiteralPath $keyFile -Force -ErrorAction SilentlyContinue
	Remove-Item -LiteralPath $knownHostsFile -Force -ErrorAction SilentlyContinue
}

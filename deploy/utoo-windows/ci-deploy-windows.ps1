# GitLab CI: Windows Shell Runner + OpenSSH blue/green deploy
# P5: runs inside utoo-pydjango; only deploys UTOO product to /opt/qd-mall-* slots.
# Forbidden: mid-tier identity/order/payment/asset/platform; Qingdao gateway/mall/admin-web.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
. (Join-Path $PSScriptRoot 'ci-env.ps1')
$root = Get-QdMallCiProjectRoot
Set-Location $root
Write-Host "[ci] project root: $root"
$ciSha = (($env:CI_COMMIT_SHA | ForEach-Object { "$_" }).Trim())
if (-not [string]::IsNullOrWhiteSpace($ciSha)) {
	Write-Host ("[ci] CI_COMMIT_SHA={0} CI_JOB_ID={1}" -f $ciSha, $env:CI_JOB_ID)
}

# Bridge legacy UTOO_* job vars onto QD_MALL_* expected by this script body.
if ([string]::IsNullOrWhiteSpace($env:QD_MALL_DEPLOY_TARGET) -and -not [string]::IsNullOrWhiteSpace($env:UTOO_DEPLOY_TARGET)) {
	$env:QD_MALL_DEPLOY_TARGET = $env:UTOO_DEPLOY_TARGET
}
if ([string]::IsNullOrWhiteSpace($env:QD_MALL_DEPLOY_PHASE) -and -not [string]::IsNullOrWhiteSpace($env:UTOO_DEPLOY_PHASE)) {
	$phaseBridge = $env:UTOO_DEPLOY_PHASE.Trim().ToLowerInvariant()
	if ($phaseBridge -eq 'gateway') { $phaseBridge = 'utoo_gateway' }
	if ($phaseBridge -eq 'static') { $phaseBridge = 'static_utoo' }
	$env:QD_MALL_DEPLOY_PHASE = $phaseBridge
}
if ([string]::IsNullOrWhiteSpace($env:QD_MALL_DEPLOY_SERVICE) -and -not [string]::IsNullOrWhiteSpace($env:UTOO_DEPLOY_SERVICE)) {
	$svcBridge = $env:UTOO_DEPLOY_SERVICE.Trim().ToLowerInvariant()
	if ($svcBridge -eq 'gateway') { $svcBridge = 'utoo_gateway' }
	if ($svcBridge -eq 'frontend') { $svcBridge = 'utoo_frontend' }
	$env:QD_MALL_DEPLOY_SERVICE = $svcBridge
}

$env:MSYS2_ARG_CONV_EXCL = '*'
$env:MSYS_NO_PATHCONV = '1'
$script:QdSshExe = Join-Path $env:SystemRoot 'System32\OpenSSH\ssh.exe'
if (-not (Test-Path -LiteralPath $script:QdSshExe)) { $script:QdSshExe = 'ssh' }
$script:QdScpExe = Join-Path $env:SystemRoot 'System32\OpenSSH\scp.exe'
if (-not (Test-Path -LiteralPath $script:QdScpExe)) { $script:QdScpExe = 'scp' }

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

function Get-CiEnv([string]$Name) { Get-QdMallCiEnv $Name }
function Resolve-DeployTarget { Resolve-QdMallDeployTarget }
function Get-BranchAwareEnv([string]$BaseName) { Get-QdMallBranchAwareEnv $BaseName }

$deployTarget = Resolve-DeployTarget
Import-QdMallDeployLocalEnv -RepoRoot $root -DeployTarget $deployTarget | Out-Null

$DeployUser = Get-BranchAwareEnv 'DEPLOY_USER'
$deployHost = Get-BranchAwareEnv 'DEPLOY_HOST'
$sshKey = Resolve-QdMallSshPrivateKey -DeployTarget $deployTarget
if ([string]::IsNullOrWhiteSpace($DeployUser) -or [string]::IsNullOrWhiteSpace($deployHost) -or [string]::IsNullOrWhiteSpace($sshKey)) {
	Write-Error @"
Missing deploy variables. Set GitLab CI/CD Variables (or C:\ProgramData\qd-mall-deploy-$deployTarget.env.ps1):
  DEPLOY_USER / DEPLOY_USER_DEV / DEPLOY_USER_PROD
  DEPLOY_HOST / DEPLOY_HOST_DEV / DEPLOY_HOST_PROD
  SSH: runner-local env file, GitLab Variable type=File, or SSH_PRIVATE_KEY_*_B64 (not multiline PEM Variable)
"@
	exit 1
}

$StaticWeb = Normalize-DeployLinuxPath (Get-CiEnv 'QD_MALL_STATIC_WEB') '/var/www/qd-admin-web'
$UtooStaticWeb = Normalize-DeployLinuxPath (Get-CiEnv 'QD_MALL_UTOO_STATIC_WEB') '/var/www/utoo-web'
$SharedConfig = Normalize-DeployLinuxPath (Get-CiEnv 'QD_MALL_SHARED_CONFIG') '/opt/qd-mall/config'
$UpstreamConf = Normalize-DeployLinuxPath (Get-CiEnv 'QD_MALL_UPSTREAM_CONF') '/usr/local/nginx/conf/qd_mall_upstream_gateway.conf'
$SwitchScript = Normalize-DeployLinuxPath (Get-CiEnv 'QD_MALL_SWITCH_SCRIPT') '/usr/local/sbin/qd-mall-switch-active.sh'
$UtooGwUpstreamConf = Normalize-DeployLinuxPath (Get-CiEnv 'QD_MALL_UTOO_GATEWAY_UPSTREAM_CONF') '/usr/local/nginx/conf/utoo_upstream_server.conf'
$UtooGwSwitchScript = Normalize-DeployLinuxPath (Get-CiEnv 'QD_MALL_UTOO_GATEWAY_SWITCH_SCRIPT') '/usr/local/sbin/qd-mall-switch-utoo-active.sh'
$ServiceUpstreamConfDir = Normalize-DeployLinuxPath (Get-CiEnv 'QD_MALL_SERVICE_UPSTREAM_CONF_DIR') '/usr/local/nginx/conf'
$ServiceSwitchScript = Normalize-DeployLinuxPath (Get-CiEnv 'QD_MALL_SERVICE_SWITCH_SCRIPT') '/usr/local/sbin/qd-mall-switch-service.sh'

# 服务目录（大平台仓路径）→ 蓝绿端口 / systemd 基名 / upstream 文件
$script:ServiceCatalog = [ordered]@{
	'identity' = @{ Dir = 'platform/identity'; UnitBase = 'qd-identity'; BluePort = 18081; GreenPort = 18181; UpstreamFile = 'qd_mall_upstream_identity.conf'; LegacyUpstream = 'utoo_upstream_identity.conf'; SwitchName = 'identity' }
	'order' = @{ Dir = 'platform/order'; UnitBase = 'qd-order'; BluePort = 18082; GreenPort = 18182; UpstreamFile = 'qd_mall_upstream_order.conf'; LegacyUpstream = 'utoo_upstream_order.conf'; SwitchName = 'order' }
	'payment' = @{ Dir = 'platform/payment'; UnitBase = 'qd-payment'; BluePort = 18084; GreenPort = 18184; UpstreamFile = 'qd_mall_upstream_payment.conf'; LegacyUpstream = 'utoo_upstream_payment.conf'; SwitchName = 'payment' }
	'admin_asset' = @{ Dir = 'platform/admin_asset'; UnitBase = 'qd-admin-asset'; BluePort = 18090; GreenPort = 18190; UpstreamFile = 'qd_mall_upstream_admin_asset.conf'; LegacyUpstream = 'utoo_upstream_admin_asset.conf'; SwitchName = 'admin_asset' }
	'admin_platform' = @{ Dir = 'platform/admin_platform'; UnitBase = 'qd-admin-platform'; BluePort = 18091; GreenPort = 18191; UpstreamFile = 'qd_mall_upstream_admin_platform.conf'; LegacyUpstream = 'utoo_upstream_admin_platform.conf'; SwitchName = 'admin_platform' }
	'mall' = @{ Dir = 'services/mall'; UnitBase = 'qd-mall-mall'; BluePort = 18092; GreenPort = 18192; UpstreamFile = 'qd_mall_upstream_mall.conf'; LegacyUpstream = ''; SwitchName = 'mall' }
	'utoo_biz' = @{ Dir = 'services/utoo_biz'; UnitBase = 'qd-utoo-biz'; BluePort = 18093; GreenPort = 18193; UpstreamFile = 'qd_mall_upstream_utoo_biz.conf'; LegacyUpstream = ''; SwitchName = 'utoo_biz' }
}

$DeployPhase = (Get-CiEnv 'QD_MALL_DEPLOY_PHASE')
if ([string]::IsNullOrWhiteSpace($DeployPhase)) { $DeployPhase = 'utoo_gateway' }
$DeployPhase = $DeployPhase.Trim().ToLowerInvariant()
# P5: only UTOO product phases (deploy into existing /opt/qd-mall-* runtime slots).
$validPhases = @('service', 'utoo_gateway', 'static_utoo', 'all')
if ($validPhases -notcontains $DeployPhase) {
	Write-Error ("P5: Invalid QD_MALL_DEPLOY_PHASE={0}. UTOO GitLab only allows: {1}" -f $DeployPhase, ($validPhases -join ', '))
	exit 1
}

$DeployService = (Get-CiEnv 'QD_MALL_DEPLOY_SERVICE')
if ([string]::IsNullOrWhiteSpace($DeployService)) { $DeployService = 'utoo_gateway' }
$DeployService = $DeployService.Trim().ToLowerInvariant()
$validServices = @('utoo_biz', 'utoo_gateway', 'utoo_frontend', 'all')
if ($validServices -notcontains $DeployService) {
	Write-Error ("P5: Invalid QD_MALL_DEPLOY_SERVICE={0}. UTOO GitLab only allows: {1}" -f $DeployService, ($validServices -join ', '))
	exit 1
}
if ($DeployPhase -eq 'service' -and $DeployService -ne 'utoo_biz') {
	Write-Error 'P5: QD_MALL_DEPLOY_PHASE=service requires QD_MALL_DEPLOY_SERVICE=utoo_biz (mid-tier forbidden)'
	exit 1
}
if ($DeployPhase -eq 'static_utoo' -and $DeployService -notin @('utoo_frontend', 'all')) {
	Write-Error 'QD_MALL_DEPLOY_PHASE=static_utoo requires QD_MALL_DEPLOY_SERVICE=utoo_frontend'
	exit 1
}
if ($DeployPhase -eq 'all') {
	Write-Error 'P5: phase=all disabled in this script; use ci-run-all.ps1 (utoo_biz -> utoo_gateway -> utoo frontend)'
	exit 1
}

Write-Host ("[deploy] target={0} host={1}@{2} phase={3} service={4}" -f $deployTarget, $DeployUser, $deployHost, $DeployPhase, $DeployService)

$sshWorkDir = Join-Path $env:TEMP 'qd-mall-ci-ssh'
if (-not [string]::IsNullOrWhiteSpace($env:CI_PROJECT_DIR)) {
	$ciDir = $env:CI_PROJECT_DIR.Trim().TrimEnd('\', '/')
	if (Test-Path -LiteralPath $ciDir) {
		$sshWorkDir = Join-Path $ciDir '.ci-ssh'
	}
}
New-Item -ItemType Directory -Force -Path $sshWorkDir | Out-Null
$keyFile = Join-Path $sshWorkDir ("gitlab_ci_qd_key_{0}" -f [Guid]::NewGuid().ToString('N'))
$knownHostsFile = Join-Path $sshWorkDir ("gitlab_ci_qd_kh_{0}" -f [Guid]::NewGuid().ToString('N'))

function Protect-QdSshPrivateKeyFile([string]$Path) {
	$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
	Write-Host ("[deploy] ssh key ACL owner: {0}" -f $identity.Name)
	$acl = Get-Acl -LiteralPath $Path
	$acl.SetAccessRuleProtection($true, $false)
	foreach ($access in @($acl.Access)) { [void]$acl.RemoveAccessRule($access) }
	$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
		$identity.User,
		[System.Security.AccessControl.FileSystemRights]::FullControl,
		[System.Security.AccessControl.AccessControlType]::Allow
	)
	$acl.AddAccessRule($rule)
	Set-Acl -LiteralPath $Path -AclObject $acl
}

try {
	$normalizedKey = ($sshKey -replace "`r`n", "`n" -replace "`r", "`n").Trim() + "`n"
	if ($normalizedKey -notmatch '(?m)^-----BEGIN .*PRIVATE KEY-----') {
		Write-Error 'SSH_PRIVATE_KEY does not look like a private key PEM.'
		exit 1
	}
	[IO.File]::WriteAllText($keyFile, $normalizedKey, [Text.UTF8Encoding]::new($false))
	Protect-QdSshPrivateKeyFile -Path $keyFile

	$kh = Get-BranchAwareEnv 'SSH_KNOWN_HOSTS'
	if ([string]::IsNullOrWhiteSpace($kh)) {
		$sshKeyscan = Join-Path $env:SystemRoot 'System32\OpenSSH\ssh-keyscan.exe'
		if (-not (Test-Path -LiteralPath $sshKeyscan)) { $sshKeyscan = 'ssh-keyscan' }
		Write-Host ("[deploy] SSH_KNOWN_HOSTS empty; probing via {0}" -f $sshKeyscan) -ForegroundColor Yellow
		$prevEap = $ErrorActionPreference
		$ErrorActionPreference = 'Continue'
		try {
			$scanRaw = & $sshKeyscan -T 20 -t rsa,ecdsa,ed25519 -H $deployHost 2>&1
			$scanExit = $LASTEXITCODE
		} finally {
			$ErrorActionPreference = $prevEap
		}
		$scanLines = @(
			$scanRaw |
				ForEach-Object { "$_" } |
				Where-Object { $_ -match '^\|1\||^[^\s#]+\s+(ssh-rsa|ssh-ed25519|ecdsa-sha2-)' }
		)
		if ($scanExit -ne 0 -or $scanLines.Count -eq 0) {
			Write-Error ("ssh-keyscan failed for {0}. Set SSH_KNOWN_HOSTS_DEV." -f $deployHost)
			exit 1
		}
		$scanLines | Set-Content -LiteralPath $knownHostsFile -Encoding ascii
	} else {
		$kh | Set-Content -LiteralPath $knownHostsFile -Encoding ascii
	}

	$SshArgs = @(
		'-i', $keyFile,
		'-o', 'IdentitiesOnly=yes',
		'-o', "UserKnownHostsFile=$knownHostsFile",
		'-o', 'StrictHostKeyChecking=yes',
		'-o', 'BatchMode=yes',
		'-o', 'ConnectTimeout=30',
		'-o', 'ConnectionAttempts=3',
		'-o', 'ServerAliveInterval=15',
		'-o', 'ServerAliveCountMax=4'
	)
	$SshTarget = "$DeployUser@$deployHost"

	Write-Host '[deploy] SSH warmup'
	$prevEapWarm = $ErrorActionPreference
	$ErrorActionPreference = 'Continue'
	try { & $script:QdSshExe @SshArgs $SshTarget 'true' 2>&1 | Out-Null } finally { $ErrorActionPreference = $prevEapWarm }

	function Test-QdSshTransportFailed([int]$ExitCode) {
		return ($ExitCode -eq 255 -or $ExitCode -eq 124)
	}
	function Test-QdSudoUnavailable([string]$ErrText) {
		return [bool]($ErrText -match '(?i)a password is required|sudo:.*(not allowed|no tty|a terminal is required|a password is required)|is not in the sudoers|sorry, try again|sudo: command not found|sudo: unable to resolve host')
	}

	function Invoke-QdSshRetry {
		param([Parameter(Mandatory)][scriptblock]$Action, [Parameter(Mandatory)][string]$What, [int]$Retries = 3)
		$lastEc = 1
		$lastOut = ''
		for ($i = 1; $i -le $Retries; $i++) {
			$global:LASTEXITCODE = 0
			$prevEap = $ErrorActionPreference
			$ErrorActionPreference = 'Continue'
			try {
				$lastOut = & $Action 2>&1
				$lastEc = [int]$LASTEXITCODE
			} finally {
				$ErrorActionPreference = $prevEap
			}
			if ($lastEc -eq 0) { return $lastOut }
			if (-not (Test-QdSshTransportFailed $lastEc) -or $i -eq $Retries) { break }
			Write-Host ("[deploy] SSH transport fail (exit={0}) retry {1}/{2}: {3}" -f $lastEc, $i, $Retries, $What) -ForegroundColor Yellow
			Start-Sleep -Seconds (3 * $i)
		}
		$msg = (($lastOut | ForEach-Object { "$_" } | Out-String).Trim())
		throw ("{0} failed (exit {1}): {2}" -f $What, $lastEc, $msg)
	}

	function Invoke-Remote([string]$RemoteCmd) {
		Invoke-QdSshRetry -What ("ssh: $RemoteCmd") -Action { & $script:QdSshExe @SshArgs $SshTarget $RemoteCmd } | Out-Null
	}
	function Invoke-RemoteCapture([string]$RemoteCmd) {
		$out = Invoke-QdSshRetry -What ("ssh: $RemoteCmd") -Action { & $script:QdSshExe @SshArgs $SshTarget $RemoteCmd }
		return (($out | Out-String).Trim())
	}
	function Invoke-RemoteSudo([string]$RemoteCmd) {
		$escaped = $RemoteCmd -replace "'", "'\''"
		$cmd = "sudo -n bash -c '$escaped'"
		try {
			Invoke-QdSshRetry -What ("sudo: $RemoteCmd") -Action { & $script:QdSshExe @SshArgs $SshTarget $cmd } | Out-Null
			return
		} catch {
			$errText = "$_"
			if ($errText -match 'exit 255|Connection timed out|Connection refused|Connection reset') { throw }
			if (-not (Test-QdSudoUnavailable $errText)) { throw }
			Write-Host ('[deploy] sudo -n unavailable; retrying without sudo: {0}' -f $RemoteCmd) -ForegroundColor Yellow
			Invoke-QdSshRetry -What ("ssh(no-sudo): $RemoteCmd") -Action { & $script:QdSshExe @SshArgs $SshTarget $RemoteCmd } | Out-Null
		}
	}
	function Invoke-RemoteSudoCapture([string]$RemoteCmd) {
		$escaped = $RemoteCmd -replace "'", "'\''"
		$cmd = "sudo -n bash -c '$escaped'"
		try {
			$out = Invoke-QdSshRetry -What ("sudo-capture: $RemoteCmd") -Action { & $script:QdSshExe @SshArgs $SshTarget $cmd }
			return (($out | Out-String).Trim())
		} catch {
			$errText = "$_"
			if ($errText -match 'exit 255|Connection timed out|Connection refused|Connection reset') { throw }
			if (-not (Test-QdSudoUnavailable $errText)) { throw }
			$out = Invoke-QdSshRetry -What ("ssh-capture(no-sudo): $RemoteCmd") -Action { & $script:QdSshExe @SshArgs $SshTarget $RemoteCmd }
			return (($out | Out-String).Trim())
		}
	}
	function Invoke-Scp([string]$LocalPath, [string]$RemotePath) {
		Invoke-QdSshRetry -What ("scp: $LocalPath -> $RemotePath") -Action {
			& $script:QdScpExe @SshArgs $LocalPath "${SshTarget}:$RemotePath"
		} | Out-Null
	}
	function Get-QdPackTarExe {
		$winTar = Join-Path $env:SystemRoot 'System32\tar.exe'
		if (Test-Path -LiteralPath $winTar) { return $winTar }
		throw 'Windows System32\tar.exe not found'
	}
	function Invoke-TarPack([string]$ArchiveFile, [string]$WorkingDirectory, [string[]]$Exclude = @()) {
		$tar = Get-QdPackTarExe
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
		$remoteSh = "/tmp/qd_mall_ci_{0}.sh" -f [Guid]::NewGuid().ToString('N')
		$localSh = Join-Path $env:TEMP ("qd_mall_ci_{0}.sh" -f [Guid]::NewGuid().ToString('N'))
		try {
			$unix = ($text -replace "`r`n", "`n" -replace "`r", "`n")
			[IO.File]::WriteAllText($localSh, $unix, [Text.UTF8Encoding]::new($false))
			Invoke-Scp -LocalPath $localSh -RemotePath $remoteSh
			$wrap = ("bash {0}; ec=`$?; if [ `$ec -eq 0 ]; then rm -f {0}; else echo [deploy] remote script failed kept={0} ec=`$ec >&2; fi; exit `$ec" -f $remoteSh)
			Invoke-RemoteSudo $wrap
		} finally {
			Remove-Item -LiteralPath $localSh -Force -ErrorAction SilentlyContinue
		}
	}
	function Invoke-RemoteBashScriptCapture([string]$LocalScriptPath, [hashtable]$Replacements) {
		$text = [IO.File]::ReadAllText($LocalScriptPath)
		foreach ($k in $Replacements.Keys) { $text = $text.Replace($k, [string]$Replacements[$k]) }
		$remoteSh = "/tmp/qd_mall_ci_{0}.sh" -f [Guid]::NewGuid().ToString('N')
		$localSh = Join-Path $env:TEMP ("qd_mall_ci_{0}.sh" -f [Guid]::NewGuid().ToString('N'))
		try {
			$unix = ($text -replace "`r`n", "`n" -replace "`r", "`n")
			[IO.File]::WriteAllText($localSh, $unix, [Text.UTF8Encoding]::new($false))
			Invoke-Scp -LocalPath $localSh -RemotePath $remoteSh
			return (Invoke-RemoteSudoCapture ("bash {0}; ec=`$?; if [ `$ec -eq 0 ]; then rm -f {0}; else echo [deploy] remote script failed kept={0} ec=`$ec >&2; fi; exit `$ec" -f $remoteSh))
		} finally {
			Remove-Item -LiteralPath $localSh -Force -ErrorAction SilentlyContinue
		}
	}

	function Sync-DirToRemote([string]$LocalDir, [string]$RemoteDir, [string[]]$Exclude, [string[]]$PreserveNames) {
		$preserveExpr = ($PreserveNames | ForEach-Object { "-not -name $_" }) -join ' '
		if ([string]::IsNullOrWhiteSpace($preserveExpr)) { $preserveExpr = '-not -name .keep' }
		$clean = @(
			"mkdir -p {0}",
			"chown -R {2}:{2} {0} || true",
			"find {0} -mindepth 1 -maxdepth 1 {1} -print0 | xargs -0r rm -rf",
			"find {0} -type d -name __pycache__ -prune -print0 2>/dev/null | xargs -0r rm -rf || true",
			"find {0} -type f -name '*.pyc' -delete 2>/dev/null || true"
		) -join '; '
		Invoke-RemoteSudo ($clean -f $RemoteDir, $preserveExpr, $DeployUser)
		$tarLocal = Join-Path $env:TEMP ("qd_sync_{0}.tar" -f [Guid]::NewGuid().ToString('N'))
		$tarRemote = "/tmp/qd_sync_{0}.tar" -f [Guid]::NewGuid().ToString('N')
		try {
			Invoke-TarPack -ArchiveFile $tarLocal -WorkingDirectory $LocalDir -Exclude $Exclude
			Invoke-Scp -LocalPath $tarLocal -RemotePath $tarRemote
			Invoke-RemoteSudo ("mkdir -p {0} && tar -xf {1} -C {0} && chown -R {2}:{2} {0} && rm -f {1}" -f $RemoteDir, $tarRemote, $DeployUser)
		} finally {
			Remove-Item -LiteralPath $tarLocal -Force -ErrorAction SilentlyContinue
		}
	}

	function Sync-SharedToSlot([string]$SlotRoot) {
		$localShared = Join-Path $root 'shared'
		if (-not (Test-Path -LiteralPath $localShared)) {
			throw "Local shared/ missing: $localShared"
		}
		Write-Host ("[deploy] sync shared/ -> {0}/shared" -f $SlotRoot)
		Sync-DirToRemote `
			-LocalDir $localShared `
			-RemoteDir ("{0}/shared" -f $SlotRoot) `
			-Exclude @('__pycache__', '*.pyc', '.git') `
			-PreserveNames @('.keep')
		$localLibs = Join-Path $root 'platform\qd_libs_common'
		if (-not (Test-Path -LiteralPath $localLibs)) {
			$altLibs = Join-Path $root 'qd_libs_common'
			if (Test-Path -LiteralPath $altLibs) { $localLibs = $altLibs }
		}
		if (Test-Path -LiteralPath $localLibs) {
			Write-Host ("[deploy] sync qd_libs_common -> {0}/platform/qd_libs_common" -f $SlotRoot)
			Sync-DirToRemote `
				-LocalDir $localLibs `
				-RemoteDir ("{0}/platform/qd_libs_common" -f $SlotRoot) `
				-Exclude @('__pycache__', '*.pyc', '.git', '.pytest_cache', 'tests') `
				-PreserveNames @('.keep')
		} else {
			Write-Warning "Local qd_libs_common missing; django may fail if qd_common required."
		}
		Invoke-RemoteSudo ("mkdir -p {0}/config {1} && if [ -f {1}/shared-database.env ] && [ ! -e {0}/config/shared-database.env ]; then ln -sfn {1}/shared-database.env {0}/config/shared-database.env; fi" -f $SlotRoot, $SharedConfig)
	}

	function Resolve-IdleSlotFromPorts {
		param(
			[Parameter(Mandatory)][string]$ActivePort,
			[Parameter(Mandatory)][string]$BluePort,
			[Parameter(Mandatory)][string]$GreenPort
		)
		if ($ActivePort -eq $BluePort) {
			return @{ Slot = 'green'; Root = '/opt/qd-mall-green'; Port = [int]$GreenPort }
		}
		return @{ Slot = 'blue'; Root = '/opt/qd-mall-blue'; Port = [int]$BluePort }
	}

	function Resolve-ServiceIdleSlot {
		param([Parameter(Mandatory)][string]$ServiceKey)
		$def = $script:ServiceCatalog[$ServiceKey]
		if ($null -eq $def) { throw "Unknown service: $ServiceKey" }
		$confCandidates = @($def.UpstreamFile)
		if ($def.LegacyUpstream) { $confCandidates += $def.LegacyUpstream }
		$serviceConf = "{0}/{1}" -f $ServiceUpstreamConfDir, $confCandidates[0]
		$portRegex = "{0}|{1}" -f $def.BluePort, $def.GreenPort
		Write-Host ("[deploy] discover active {0} from {1}" -f $ServiceKey, $serviceConf)
		$activePort = (Invoke-RemoteBashScriptCapture -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-discover-service-port.sh') -Replacements @{
			'__CONF__' = $serviceConf
			'__PORTS__' = $portRegex
			'__DEFAULT_PORT__' = [string]$def.BluePort
		}).Trim()
		# 若新文件没有，试旧名
		if ($activePort -notmatch ("^({0})$" -f $portRegex) -and $def.LegacyUpstream) {
			$legacyConf = "{0}/{1}" -f $ServiceUpstreamConfDir, $def.LegacyUpstream
			$activePort = (Invoke-RemoteBashScriptCapture -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-discover-service-port.sh') -Replacements @{
				'__CONF__' = $legacyConf
				'__PORTS__' = $portRegex
				'__DEFAULT_PORT__' = [string]$def.BluePort
			}).Trim()
		}
		if ($activePort -notmatch ("^({0})$" -f $portRegex)) {
			$activePort = [string]$def.BluePort
		}
		$idle = Resolve-IdleSlotFromPorts -ActivePort $activePort -BluePort ([string]$def.BluePort) -GreenPort ([string]$def.GreenPort)
		$unit = @{
			Dir = $def.Dir
			Service = ("{0}-{1}" -f $def.UnitBase, $idle.Slot)
			Port = $idle.Port
			SwitchName = $def.SwitchName
		}
		Write-Host ("[deploy] active {0}=:{1}; idle {2}=:{3} root={4}" -f $ServiceKey, $activePort, $idle.Slot, $idle.Port, $idle.Root) -ForegroundColor Cyan
		return @{ Slot = $idle.Slot; Root = $idle.Root; Unit = $unit }
	}

	$Slot = $null
	$RemoteRoot = $null
	$GwPort = $null
	$GatewayUnit = $null
	$UtooGwPort = $null
	$UtooGatewayUnit = $null
	$SingleServiceUnit = $null
	$UpstreamUnits = $null

	$needQdGwSlot = ($DeployPhase -in @('all', 'gateway', 'libs_services'))
	$needUtooGwSlot = ($DeployPhase -in @('utoo_gateway'))
	$needSingle = ($DeployPhase -in @('service', 'mall') -or ($DeployPhase -eq 'service'))

	if ($DeployPhase -eq 'mall') { $DeployService = 'mall'; $needSingle = $true }

	if ($needQdGwSlot) {
		Write-Host ("[deploy] discover Qingdao gateway from {0}" -f $UpstreamConf)
		$activePort = (Invoke-RemoteBashScriptCapture -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-discover-upstream-port.sh') -Replacements @{
			'__CONF__' = $UpstreamConf
		}).Trim()
		if ($activePort -notmatch '^(18080|18180)$') { $activePort = '18080' }
		$idle = Resolve-IdleSlotFromPorts -ActivePort $activePort -BluePort '18080' -GreenPort '18180'
		$Slot = $idle.Slot
		$RemoteRoot = $idle.Root
		$GwPort = $idle.Port
		$GatewayUnit = @{ Dir = 'gateway'; Service = ("qd-mall-gateway-{0}" -f $Slot); Port = $GwPort }
		$UpstreamUnits = @(
			@{ Dir = 'platform/identity'; Service = ("qd-identity-{0}" -f $Slot); Port = $(if ($Slot -eq 'green') { 18181 } else { 18081 }) },
			@{ Dir = 'platform/order'; Service = ("qd-order-{0}" -f $Slot); Port = $(if ($Slot -eq 'green') { 18182 } else { 18082 }) },
			@{ Dir = 'platform/payment'; Service = ("qd-payment-{0}" -f $Slot); Port = $(if ($Slot -eq 'green') { 18184 } else { 18084 }) },
			@{ Dir = 'platform/admin_asset'; Service = ("qd-admin-asset-{0}" -f $Slot); Port = $(if ($Slot -eq 'green') { 18190 } else { 18090 }) },
			@{ Dir = 'platform/admin_platform'; Service = ("qd-admin-platform-{0}" -f $Slot); Port = $(if ($Slot -eq 'green') { 18191 } else { 18091 }) },
			@{ Dir = 'services/mall'; Service = ("qd-mall-mall-{0}" -f $Slot); Port = $(if ($Slot -eq 'green') { 18192 } else { 18092 }) },
			@{ Dir = 'services/utoo_biz'; Service = ("qd-utoo-biz-{0}" -f $Slot); Port = $(if ($Slot -eq 'green') { 18193 } else { 18093 }) }
		)
		Write-Host ("[deploy] idle slot={0} root={1} qd_gateway={2}" -f $Slot, $RemoteRoot, $GwPort) -ForegroundColor Cyan
	}

	if ($needUtooGwSlot) {
		$activePort = (Invoke-RemoteBashScriptCapture -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-discover-utoo-gateway-port.sh') -Replacements @{
			'__CONF__' = $UtooGwUpstreamConf
		}).Trim()
		if ($activePort -notmatch '^(18083|18183)$') { $activePort = '18083' }
		$idle = Resolve-IdleSlotFromPorts -ActivePort $activePort -BluePort '18083' -GreenPort '18183'
		$Slot = $idle.Slot
		$RemoteRoot = $idle.Root
		$UtooGwPort = $idle.Port
		$UtooGatewayUnit = @{ Dir = 'platform/utoo_gateway'; Service = ("qd-gateway-{0}" -f $Slot); Port = $UtooGwPort }
		Write-Host ("[deploy] idle slot={0} utoo_gateway={1}" -f $Slot, $UtooGwPort) -ForegroundColor Cyan
	}

	if ($DeployPhase -eq 'service' -or ($DeployPhase -eq 'mall')) {
		$resolved = Resolve-ServiceIdleSlot -ServiceKey $DeployService
		$Slot = $resolved.Slot
		$RemoteRoot = $resolved.Root
		$SingleServiceUnit = $resolved.Unit
	}

	function Sync-MallDomainPackages([string]$SlotRoot) {
		# mall INSTALLED_APPS + admin_platform catalog re-export 均依赖这些域目录
		$domains = @('sales', 'rental', 'procurement', 'production', 'reporting', 'catalog', 'inventory')
		foreach ($d in $domains) {
			$localDir = Join-Path $root ("services\{0}" -f $d)
			if (-not (Test-Path -LiteralPath $localDir)) {
				Write-Host ("[deploy][warn] skip missing domain: {0}" -f $localDir) -ForegroundColor Yellow
				continue
			}
			Sync-DirToRemote `
				-LocalDir $localDir `
				-RemoteDir ("{0}/services/{1}" -f $SlotRoot, $d) `
				-Exclude @('.venv', '__pycache__', '*.pyc', '.git', '.env', 'tests', '.pytest_cache', 'node_modules') `
				-PreserveNames @('.keep')
		}
	}

	function Sync-DjangoUnitCode {
		param([Parameter(Mandatory)][hashtable]$Unit, [Parameter(Mandatory)][string]$SlotRoot)
		$dir = $Unit.Dir
		$svc = $Unit.Service
		$port = $Unit.Port
		$localDir = Join-Path $root ($dir -replace '/', '\')
		if (-not (Test-Path -LiteralPath $localDir)) { throw "Local service directory missing: $localDir" }
		$remoteDir = "{0}/{1}" -f $SlotRoot, $dir
		Write-Host ("[deploy] === sync {0} ({1} :{2}) ===" -f $dir, $svc, $port) -ForegroundColor Cyan
		if ($dir -eq 'services/mall') {
			$peerRoot = if ($SlotRoot -match 'green$') { '/opt/qd-mall-blue' } else { '/opt/qd-mall-green' }
			$peerEnv = "{0}/services/mall/.env" -f $peerRoot
			$mallEnv = "{0}/services/mall/.env" -f $SlotRoot
			Write-Host ("[deploy] seed mall .env from peer if idle slot missing: {0}" -f $mallEnv)
			Invoke-RemoteSudo ("mkdir -p {0}/services/mall && if [ ! -f {1} ] && [ -f {2} ]; then cp -a {2} {1} && chown deploy:deploy {1} && chmod 600 {1}; fi" -f $SlotRoot, $mallEnv, $peerEnv)
		}
		if ($dir -eq 'gateway') {
			$peerRoot = if ($SlotRoot -match 'green$') { '/opt/qd-mall-blue' } else { '/opt/qd-mall-green' }
			$peerEnv = "{0}/gateway/.env" -f $peerRoot
			$gwEnv = "{0}/gateway/.env" -f $SlotRoot
			Write-Host ("[deploy] seed gateway .env from peer if idle slot missing: {0}" -f $gwEnv)
			Invoke-RemoteSudo ("mkdir -p {0}/gateway && if [ ! -f {1} ] && [ -f {2} ]; then cp -a {2} {1} && chown deploy:deploy {1} && chmod 600 {1}; fi" -f $SlotRoot, $gwEnv, $peerEnv)
		}
		if ($dir -eq 'platform/utoo_gateway' -or $dir -eq 'services/utoo_biz') {
			$peerRoot = if ($SlotRoot -match 'green$') { '/opt/qd-mall-blue' } else { '/opt/qd-mall-green' }
			$kind = if ($dir -eq 'platform/utoo_gateway') { 'utoo_gateway' } else { 'utoo_biz' }
			Write-Host ("[deploy] seed {0} .env (VIP map / peer) on {1}" -f $kind, $SlotRoot) -ForegroundColor Cyan
			Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-seed-utoo-env.sh') -Replacements @{
				'__SLOT_ROOT__' = $SlotRoot
				'__PEER_SLOT_ROOT__' = $peerRoot
				'__KIND__' = $kind
			}
		}
		Invoke-RemoteSudo ("systemctl stop {0} || true" -f $svc)
		Sync-DirToRemote `
			-LocalDir $localDir `
			-RemoteDir $remoteDir `
			-Exclude @('.venv', '__pycache__', '*.pyc', '.git', '.env', '.env.local', 'tests', '.pytest_cache', 'node_modules') `
			-PreserveNames @('.venv', '.env', '.env.local')
		if ($dir -eq 'services/mall') {
			Sync-MallDomainPackages -SlotRoot $SlotRoot
		}
		if ($dir -eq 'platform/admin_platform') {
			# T3-A：goods/catalog repo re-export → apps.catalog，slot 必须有 services/catalog
			Write-Host ("[deploy] sync catalog domain for admin_platform ({0})" -f $SlotRoot) -ForegroundColor Cyan
			$catalogLocal = Join-Path $root 'services\catalog'
			if (Test-Path -LiteralPath $catalogLocal) {
				Sync-DirToRemote `
					-LocalDir $catalogLocal `
					-RemoteDir ("{0}/services/catalog" -f $SlotRoot) `
					-Exclude @('.venv', '__pycache__', '*.pyc', '.git', '.env', 'tests', '.pytest_cache', 'node_modules') `
					-PreserveNames @('.keep')
			} else {
				Write-Host ("[deploy][warn] missing services/catalog for admin_platform") -ForegroundColor Yellow
			}
		}
		$envCheck = ("if [ ! -f {0}/.env ] && [ ! -f {1}/config/shared-database.env ]; then echo deploy_error_missing_env:{2}; exit 1; fi" -f $remoteDir, $SlotRoot, $dir)
		Invoke-Remote $envCheck
	}

	function Deploy-DjangoUnit {
		param([Parameter(Mandatory)][hashtable]$Unit, [Parameter(Mandatory)][string]$SlotRoot)
		$dir = $Unit.Dir
		$svc = $Unit.Service
		$port = $Unit.Port
		$healthUrl = "http://127.0.0.1:{0}/health" -f $port
		Sync-DjangoUnitCode -Unit $Unit -SlotRoot $SlotRoot
		Write-Host ("[deploy] pip {0}..." -f $dir)
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-pip-install.sh') -Replacements @{
			'__ROOT__' = $SlotRoot
			'__SVC_DIR__' = $dir
		}
		Write-Host ("[deploy] django check {0}..." -f $dir)
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-smoke.sh') -Replacements @{
			'__ROOT__' = $SlotRoot
			'__SVC_DIR__' = $dir
		}
		Write-Host ("[deploy] systemctl restart {0}" -f $svc)
		Invoke-RemoteSudo ("systemctl restart {0}" -f $svc)
		if ($dir -eq 'platform/utoo_gateway') {
			Invoke-UtooUnitPostDeployEnv -SlotRoot $SlotRoot -UnitName $svc -RelEnvPath 'platform/utoo_gateway/.env'
		}
		if ($dir -eq 'services/utoo_biz') {
			Invoke-UtooUnitPostDeployEnv -SlotRoot $SlotRoot -UnitName $svc -RelEnvPath 'services/utoo_biz/.env'
		}
		$healthWait = ('j=1; while [ $j -le 60 ]; do if curl -sf "{0}" >/dev/null || curl -sf "{0}/" >/dev/null; then echo deploy_health_ok:{1}; exit 0; fi; sleep 1; j=$((j+1)); done; echo deploy_health_fail:{1} >&2; systemctl --no-pager status {1} -l || true; journalctl -u {1} -n 80 --no-pager || true; exit 1' -f $healthUrl, $svc)
		Invoke-RemoteSudo $healthWait
		if ($dir -eq 'services/mall') {
			Invoke-MallPostDeployEnv -SlotRoot $SlotRoot -MallUnit $svc -MallPort $port
		}
	}

	function Invoke-MallPostDeployEnv {
		param(
			[Parameter(Mandatory)][string]$SlotRoot,
			[Parameter(Mandatory)][string]$MallUnit,
			[Parameter(Mandatory)][int]$MallPort
		)
		$peerRoot = if ($SlotRoot -match 'green$') { '/opt/qd-mall-blue' } else { '/opt/qd-mall-green' }
		Write-Host ("[deploy] post-mall env sync JWT/OSS ({0} :{1})..." -f $MallUnit, $MallPort) -ForegroundColor Cyan
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-post-mall-env.sh') -Replacements @{
			'__SLOT_ROOT__' = $SlotRoot
			'__PEER_SLOT_ROOT__' = $peerRoot
			'__MALL_UNIT__' = $MallUnit
			'__MALL_PORT__' = [string]$MallPort
		}
	}

	function Invoke-GatewayPostDeployEnv {
		param(
			[Parameter(Mandatory)][string]$SlotRoot,
			[Parameter(Mandatory)][string]$GwUnit
		)
		$gwEnv = "{0}/gateway/.env" -f $SlotRoot
		$unitFile = "/etc/systemd/system/{0}.service" -f $GwUnit
		Write-Host ("[deploy] post-gateway systemd EnvironmentFile ({0})..." -f $GwUnit) -ForegroundColor Cyan
		Invoke-RemoteSudo ("if [ -f {0} ] && [ -f {1} ] && ! grep -q 'EnvironmentFile=-{0}' {1}; then sed -i '/^WorkingDirectory=/a EnvironmentFile=-{0}' {1}; systemctl daemon-reload; systemctl restart {2}; fi" -f $gwEnv, $unitFile, $GwUnit)
	}

	function Invoke-UtooUnitPostDeployEnv {
		param(
			[Parameter(Mandatory)][string]$SlotRoot,
			[Parameter(Mandatory)][string]$UnitName,
			[Parameter(Mandatory)][string]$RelEnvPath
		)
		$envFile = "{0}/{1}" -f $SlotRoot, $RelEnvPath
		$unitFile = "/etc/systemd/system/{0}.service" -f $UnitName
		Write-Host ("[deploy] post-utoo systemd EnvironmentFile ({0} -> {1})..." -f $UnitName, $envFile) -ForegroundColor Cyan
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-unit-envfile.sh') -Replacements @{
			'__UNIT_FILE__' = $unitFile
			'__ENV_FILE__' = $envFile
			'__UNIT_NAME__' = $UnitName
		}
	}

	$doLibs = ($DeployPhase -in @('all', 'libs_services'))
	$doSingle = ($DeployPhase -in @('service', 'mall'))
	$doGateway = ($DeployPhase -in @('all', 'gateway'))
	$doUtooGateway = ($DeployPhase -eq 'utoo_gateway')
	$doStatic = ($DeployPhase -eq 'static')
	$doStaticUtoo = ($DeployPhase -eq 'static_utoo')

	if ($doSingle) {
		Sync-SharedToSlot -SlotRoot $RemoteRoot
		Deploy-DjangoUnit -Unit $SingleServiceUnit -SlotRoot $RemoteRoot
		$switchName = $SingleServiceUnit.SwitchName
		if (-not $switchName) { $switchName = $DeployService }
		Write-Host ("[deploy] switch {0} -> {1}" -f $switchName, $SingleServiceUnit.Port)
		Invoke-RemoteSudo ("/bin/bash '{0}' {1} {2}" -f $ServiceSwitchScript, $switchName, $SingleServiceUnit.Port)
		Write-Host ("[deploy] phase service done: {0}" -f $DeployService)
	}

	if ($doLibs) {
		if (-not $RemoteRoot -or -not $UpstreamUnits) { throw 'libs_services requires slot resolution' }
		Sync-SharedToSlot -SlotRoot $RemoteRoot
		$stopList = ($UpstreamUnits | ForEach-Object { $_.Service }) -join ' '
		Invoke-RemoteSudo ("systemctl stop {0} || true" -f $stopList)
		$specParts = @()
		foreach ($unit in $UpstreamUnits) {
			Sync-DjangoUnitCode -Unit $unit -SlotRoot $RemoteRoot
			$specParts += ("{0}|{1}|{2}" -f $unit.Dir, $unit.Service, $unit.Port)
		}
		Write-Host ('[deploy] parallel pip/restart for {0} units...' -f $UpstreamUnits.Count) -ForegroundColor Cyan
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-units-parallel.sh') -Replacements @{
			'__ROOT__' = $RemoteRoot
			'__SPECS__' = ($specParts -join ';')
		}
		$portByDir = @{}
		foreach ($unit in $UpstreamUnits) { $portByDir[$unit.Dir] = [string]$unit.Port }
		$mallUnit = ($UpstreamUnits | Where-Object { $_.Dir -eq 'services/mall' } | Select-Object -First 1)
		if ($mallUnit) {
			Invoke-MallPostDeployEnv -SlotRoot $RemoteRoot -MallUnit $mallUnit.Service -MallPort ([int]$mallUnit.Port)
		}
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-switch-services-batch.sh') -Replacements @{
			'__NGINX_CONF_DIR__' = $ServiceUpstreamConfDir
			'__ORDER_PORT__' = $portByDir['platform/order']
			'__IDENTITY_PORT__' = $portByDir['platform/identity']
			'__PAYMENT_PORT__' = $portByDir['platform/payment']
			'__ASSET_PORT__' = $portByDir['platform/admin_asset']
			'__PLATFORM_PORT__' = $portByDir['platform/admin_platform']
			'__MALL_PORT__' = $portByDir['services/mall']
			'__UTOO_BIZ_PORT__' = $portByDir['services/utoo_biz']
		}
		Write-Host '[deploy] phase libs_services done.'
	}

	if ($doGateway) {
		if (-not $RemoteRoot -or -not $GatewayUnit) { throw 'gateway phase requires slot resolution' }
		Sync-SharedToSlot -SlotRoot $RemoteRoot
		Deploy-DjangoUnit -Unit $GatewayUnit -SlotRoot $RemoteRoot
		Invoke-GatewayPostDeployEnv -SlotRoot $RemoteRoot -GwUnit $GatewayUnit.Service
		Invoke-RemoteSudo ("/bin/bash '{0}' {1}" -f $SwitchScript, $GwPort)
		Invoke-RemoteSudo ('curl -sf "http://127.0.0.1:{0}/health" >/dev/null && echo deploy_qd_gateway_ok' -f $GwPort)
		Write-Host '[deploy] phase gateway (Qingdao) done.'
	}

	if ($doUtooGateway) {
		if (-not $RemoteRoot -or -not $UtooGatewayUnit) { throw 'utoo_gateway phase requires slot resolution' }
		Sync-SharedToSlot -SlotRoot $RemoteRoot
		Deploy-DjangoUnit -Unit $UtooGatewayUnit -SlotRoot $RemoteRoot
		Invoke-RemoteSudo ("/bin/bash '{0}' {1}" -f $UtooGwSwitchScript, $UtooGwPort)
		Invoke-RemoteSudo ('curl -sf "http://127.0.0.1:{0}/health" >/dev/null && echo deploy_utoo_gateway_ok' -f $UtooGwPort)
		Write-Host '[deploy] phase utoo_gateway done.'
	}

	if ($doStatic) {
		$webDist = Join-Path $root 'admin-web\dist'
		if (-not (Test-Path -LiteralPath $webDist)) { Write-Error "Missing $webDist — run frontend build first"; exit 1 }
		$buildInfoPath = Join-Path $webDist 'build-info.json'
		if (-not (Test-Path -LiteralPath $buildInfoPath)) { Write-Error "Missing $buildInfoPath"; exit 1 }
		$buildInfoText = Get-Content -LiteralPath $buildInfoPath -Raw -Encoding utf8
		$expectedCommit = (($env:CI_COMMIT_SHA | ForEach-Object { "$_" }).Trim())
		if (-not [string]::IsNullOrWhiteSpace($expectedCommit) -and ($buildInfoText.IndexOf($expectedCommit, [StringComparison]::OrdinalIgnoreCase) -lt 0)) {
			Write-Error ("build-info.json missing CI_COMMIT_SHA={0}" -f $expectedCommit)
			exit 1
		}
		Write-Host ("[deploy] sync admin-web -> {0}" -f $StaticWeb)
		Sync-DirToRemote -LocalDir $webDist -RemoteDir $StaticWeb -Exclude @() -PreserveNames @('.keep')
		Write-Host '[deploy] phase static (admin-web) done.'
	}

	if ($doStaticUtoo) {
		$webDist = Join-Path $root 'utoo-web-front\dist'
		if (-not (Test-Path -LiteralPath $webDist)) { Write-Error "Missing $webDist — build utoo-web-front first"; exit 1 }
		$buildInfoPath = Join-Path $webDist 'build-info.json'
		if (-not (Test-Path -LiteralPath $buildInfoPath)) { Write-Error "Missing $buildInfoPath"; exit 1 }
		$buildInfoText = Get-Content -LiteralPath $buildInfoPath -Raw -Encoding utf8
		$expectedCommit = (($env:CI_COMMIT_SHA | ForEach-Object { "$_" }).Trim())
		if (-not [string]::IsNullOrWhiteSpace($expectedCommit) -and ($buildInfoText.IndexOf($expectedCommit, [StringComparison]::OrdinalIgnoreCase) -lt 0)) {
			Write-Error ("build-info.json missing CI_COMMIT_SHA={0}" -f $expectedCommit)
			exit 1
		}
		Write-Host ("[deploy] sync utoo-web-front -> {0}" -f $UtooStaticWeb)
		Sync-DirToRemote -LocalDir $webDist -RemoteDir $UtooStaticWeb -Exclude @() -PreserveNames @('.keep')
		Write-Host '[deploy] phase static_utoo done.'
	}

	Write-Host ("qd-mall deploy phase={0} finished OK." -f $DeployPhase)
	exit 0
} finally {
	Remove-Item -LiteralPath $keyFile -Force -ErrorAction SilentlyContinue
	Remove-Item -LiteralPath $knownHostsFile -Force -ErrorAction SilentlyContinue
}

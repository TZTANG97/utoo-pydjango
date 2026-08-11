# GitLab CI: Windows Shell Runner + OpenSSH blue/green deploy
# Idle slot publish -> health -> nginx switch -> static
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'ci-project-root.ps1')
$root = Get-UtooCiProjectRoot
Set-Location $root
Write-Host "[ci] project root: $root"
$ciSha = (($env:CI_COMMIT_SHA | ForEach-Object { "$_" }).Trim())
if (-not [string]::IsNullOrWhiteSpace($ciSha)) {
	Write-Host ("[ci] CI_COMMIT_SHA={0} CI_JOB_ID={1} CI_PROJECT_DIR={2}" -f $ciSha, $env:CI_JOB_ID, $env:CI_PROJECT_DIR)
}

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

$StaticWeb = Normalize-DeployLinuxPath (Get-CiEnv 'UTOO_STATIC_WEB') '/var/www/utoo-web'
if ([string]::IsNullOrWhiteSpace((Get-CiEnv 'UTOO_STATIC_WEB'))) {
	$legacyC = Get-CiEnv 'UTOO_STATIC_C'
	if (-not [string]::IsNullOrWhiteSpace($legacyC)) {
		$StaticWeb = Normalize-DeployLinuxPath $legacyC '/var/www/utoo-web'
	}
}
$SharedConfig = Normalize-DeployLinuxPath (Get-CiEnv 'UTOO_SHARED_CONFIG') '/opt/utoo/config'
$UpstreamConf = Normalize-DeployLinuxPath (Get-CiEnv 'UTOO_UPSTREAM_CONF') '/usr/local/nginx/conf/utoo_upstream_server.conf'
$SwitchScript = Normalize-DeployLinuxPath (Get-CiEnv 'UTOO_SWITCH_SCRIPT') '/usr/local/sbin/utoo-switch-active.sh'
$ServiceUpstreamConfDir = Normalize-DeployLinuxPath (Get-CiEnv 'UTOO_SERVICE_UPSTREAM_CONF_DIR') '/usr/local/nginx/conf'
$ServiceSwitchScript = Normalize-DeployLinuxPath (Get-CiEnv 'UTOO_SERVICE_SWITCH_SCRIPT') '/usr/local/sbin/utoo-switch-service.sh'

# libs_services | gateway | static | service | all
$DeployPhase = (Get-CiEnv 'UTOO_DEPLOY_PHASE')
if ([string]::IsNullOrWhiteSpace($DeployPhase)) { $DeployPhase = 'all' }
$DeployPhase = $DeployPhase.Trim().ToLowerInvariant()
$validPhases = @('libs_services', 'gateway', 'static', 'service', 'all')
if ($validPhases -notcontains $DeployPhase) {
	Write-Error ("Invalid UTOO_DEPLOY_PHASE={0}. Use: {1}" -f $DeployPhase, ($validPhases -join ', '))
	exit 1
}

$DeployService = (Get-CiEnv 'UTOO_DEPLOY_SERVICE')
if ([string]::IsNullOrWhiteSpace($DeployService)) { $DeployService = 'all' }
$DeployService = $DeployService.Trim().ToLowerInvariant()
$validServices = @('order', 'payment', 'admin_asset', 'admin_platform', 'gateway', 'frontend', 'all')
if ($validServices -notcontains $DeployService) {
	Write-Error ("Invalid UTOO_DEPLOY_SERVICE={0}. Use: {1}" -f $DeployService, ($validServices -join ', '))
	exit 1
}
if ($DeployPhase -eq 'service' -and $DeployService -notin @('order', 'payment', 'admin_asset', 'admin_platform', 'gateway')) {
	Write-Error 'UTOO_DEPLOY_PHASE=service requires UTOO_DEPLOY_SERVICE=order|payment|admin_asset|admin_platform|gateway'
	exit 1
}
if ($DeployPhase -eq 'static' -and $DeployService -notin @('frontend', 'all')) {
	Write-Error 'UTOO_DEPLOY_PHASE=static requires UTOO_DEPLOY_SERVICE=frontend'
	exit 1
}

Write-Host ("[deploy] target={0} host={1}@{2} phase={3} service={4}" -f $deployTarget, $DeployUser, $deployHost, $DeployPhase, $DeployService)

# --- SSH key / known_hosts ---
# Prefer job workspace over C:\Windows\TEMP so service-account ACL stays consistent.
$sshWorkDir = Join-Path $env:TEMP 'utoo-ci-ssh'
if (-not [string]::IsNullOrWhiteSpace($env:CI_PROJECT_DIR)) {
	$ciDir = $env:CI_PROJECT_DIR.Trim().TrimEnd('\', '/')
	if (Test-Path -LiteralPath $ciDir) {
		$sshWorkDir = Join-Path $ciDir '.ci-ssh'
	}
}
New-Item -ItemType Directory -Force -Path $sshWorkDir | Out-Null
$keyFile = Join-Path $sshWorkDir ("gitlab_ci_utoo_key_{0}" -f [Guid]::NewGuid().ToString('N'))
$knownHostsFile = Join-Path $sshWorkDir ("gitlab_ci_utoo_kh_{0}" -f [Guid]::NewGuid().ToString('N'))

function Protect-UtooSshPrivateKeyFile([string]$Path) {
	# OpenSSH on Windows rejects keys readable by other users.
	# Do NOT use $env:USERNAME — GitLab Runner as a service often differs from that value.
	$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
	Write-Host ("[deploy] ssh key ACL owner: {0}" -f $identity.Name)
	$acl = Get-Acl -LiteralPath $Path
	$acl.SetAccessRuleProtection($true, $false)
	foreach ($access in @($acl.Access)) {
		[void]$acl.RemoveAccessRule($access)
	}
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
		Write-Error 'SSH_PRIVATE_KEY_DEV/SSH_PRIVATE_KEY does not look like a private key PEM. Check GitLab CI variable value (not .pub).'
		exit 1
	}
	[IO.File]::WriteAllText($keyFile, $normalizedKey, [Text.UTF8Encoding]::new($false))
	Protect-UtooSshPrivateKeyFile -Path $keyFile

	$kh = Get-BranchAwareEnv 'SSH_KNOWN_HOSTS'
	if ([string]::IsNullOrWhiteSpace($kh)) {
		# ssh-keyscan writes banners to stderr; with ErrorActionPreference=Stop that becomes NativeCommandError.
		$sshKeyscan = Join-Path $env:SystemRoot 'System32\OpenSSH\ssh-keyscan.exe'
		if (-not (Test-Path -LiteralPath $sshKeyscan)) { $sshKeyscan = 'ssh-keyscan' }
		Write-Host ("[deploy] SSH_KNOWN_HOSTS empty; probing host keys via {0}" -f $sshKeyscan) -ForegroundColor Yellow
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
			Write-Error ("ssh-keyscan failed for {0} (exit={1}). Set GitLab CI variable SSH_KNOWN_HOSTS_DEV to avoid auto scan.`n{2}" -f $deployHost, $scanExit, (($scanRaw | Out-String).Trim()))
			exit 1
		}
		$scanLines | Set-Content -LiteralPath $knownHostsFile -Encoding ascii
	} else {
		Write-Host '[deploy] using SSH_KNOWN_HOSTS from CI variables'
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

	# Warm SSH once after keyscan/cold start so the first real sync is less likely to hit exit 255.
	Write-Host '[deploy] SSH warmup (true)'
	$prevEapWarm = $ErrorActionPreference
	$ErrorActionPreference = 'Continue'
	try {
		& $script:UtooSshExe @SshArgs $SshTarget 'true' 2>&1 | Out-Null
	} finally {
		$ErrorActionPreference = $prevEapWarm
	}

	function Test-UtooSshTransportFailed([int]$ExitCode) {
		# OpenSSH: 255 = connection/protocol failure (timeout, reset, etc.)
		return ($ExitCode -eq 255 -or $ExitCode -eq 124)
	}

	function Test-UtooSudoUnavailable([string]$ErrText) {
		# Only treat these as "sudo -n cannot run at all". Inner command failures
		# (pip/health/script exit != 0) must NOT fall back to no-sudo — that deletes
		# /tmp/utoo_ci_*.sh via rm -f then masks the real error as exit 127.
		return [bool]($ErrText -match '(?i)a password is required|sudo:.*(not allowed|no tty|a terminal is required|a password is required)|is not in the sudoers|sorry, try again|sudo: command not found|sudo: unable to resolve host')
	}

	function Invoke-UtooSshRetry {
		param(
			[Parameter(Mandatory)][scriptblock]$Action,
			[Parameter(Mandatory)][string]$What,
			[int]$Retries = 3
		)
		$lastEc = 1
		$lastOut = ''
		for ($i = 1; $i -le $Retries; $i++) {
			$global:LASTEXITCODE = 0
			# ssh/scp stderr must not become terminating errors under ErrorActionPreference=Stop
			$prevEap = $ErrorActionPreference
			$ErrorActionPreference = 'Continue'
			try {
				$lastOut = & $Action 2>&1
				$lastEc = [int]$LASTEXITCODE
			} finally {
				$ErrorActionPreference = $prevEap
			}
			if ($lastEc -eq 0) { return $lastOut }
			if (-not (Test-UtooSshTransportFailed $lastEc) -or $i -eq $Retries) {
				break
			}
			Write-Host ("[deploy] SSH transport fail (exit={0}) retry {1}/{2}: {3}" -f $lastEc, $i, $Retries, $What) -ForegroundColor Yellow
			Start-Sleep -Seconds (3 * $i)
		}
		$msg = (($lastOut | ForEach-Object { "$_" } | Out-String).Trim())
		throw ("{0} failed (exit {1}): {2}" -f $What, $lastEc, $msg)
	}

	function Invoke-Remote([string]$RemoteCmd) {
		Invoke-UtooSshRetry -What ("ssh: $RemoteCmd") -Action {
			& $script:UtooSshExe @SshArgs $SshTarget $RemoteCmd
		} | Out-Null
	}
	function Invoke-RemoteCapture([string]$RemoteCmd) {
		$out = Invoke-UtooSshRetry -What ("ssh: $RemoteCmd") -Action {
			& $script:UtooSshExe @SshArgs $SshTarget $RemoteCmd
		}
		return (($out | Out-String).Trim())
	}
	function Invoke-RemoteSudo([string]$RemoteCmd) {
		# Prefer passwordless sudo. Do NOT fall back to no-sudo on inner-command failure:
		# that caused /tmp/utoo_ci_*.sh already rm'd then "No such file" (exit 127) on retry,
		# especially visible on first deploy after runner/SSH cold start when pip/health fails.
		$escaped = $RemoteCmd -replace "'", "'\''"
		$cmd = "sudo -n bash -c '$escaped'"
		try {
			Invoke-UtooSshRetry -What ("sudo: $RemoteCmd") -Action {
				& $script:UtooSshExe @SshArgs $SshTarget $cmd
			} | Out-Null
			return
		} catch {
			$errText = "$_"
			if ($errText -match 'exit 255|Connection timed out|Connection refused|Connection reset') {
				throw
			}
			if (-not (Test-UtooSudoUnavailable $errText)) {
				throw
			}
			Write-Host ('[deploy] sudo -n unavailable; retrying without sudo: {0}' -f $RemoteCmd) -ForegroundColor Yellow
			Invoke-UtooSshRetry -What ("ssh(no-sudo): $RemoteCmd") -Action {
				& $script:UtooSshExe @SshArgs $SshTarget $RemoteCmd
			} | Out-Null
		}
	}
	function Invoke-Scp([string]$LocalPath, [string]$RemotePath) {
		Invoke-UtooSshRetry -What ("scp: $LocalPath -> $RemotePath") -Action {
			& $script:UtooScpExe @SshArgs $LocalPath "${SshTarget}:$RemotePath"
		} | Out-Null
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
			# Keep remote script on failure so debugging still has the file; success still cleans up.
			$wrap = ("bash {0}; ec=`$?; if [ `$ec -eq 0 ]; then rm -f {0}; else echo [deploy] remote script failed kept={0} ec=`$ec >&2; fi; exit `$ec" -f $remoteSh)
			try {
				Invoke-RemoteSudo $wrap
			} catch {
				Write-Host ('[deploy] remote bash failed: {0}' -f $_.Exception.Message) -ForegroundColor Yellow
				try {
					# Surface which unit failed; avoid only showing the last healthy services' tails.
					$summary = Invoke-RemoteSudoCapture 'echo "===== unit log files ====="; ls -la /tmp/utoo_unit_*.log 2>/dev/null || true; echo "===== unit fail markers ====="; grep -HE "deploy_pip_failed|deploy_health_fail|deploy_units_parallel_failed|Traceback|ERROR|FAILED:" /tmp/utoo_unit_*.log 2>/dev/null | tail -n 120 || true; echo "===== unit status lines ====="; grep -HE "deploy_(pip_ok|django_check_ok|health_ok|pip_failed|health_fail|unit_start)" /tmp/utoo_unit_*.log 2>/dev/null || true; echo "===== per-unit tail ====="; for f in /tmp/utoo_unit_*.log; do [ -f "$f" ] || continue; echo "----- $f -----"; tail -n 100 "$f"; done; true'
					if (-not [string]::IsNullOrWhiteSpace($summary)) {
						Write-Host '[deploy] ---- remote unit failure summary ----' -ForegroundColor Yellow
						Write-Host $summary
						Write-Host '[deploy] ---- end unit failure summary ----' -ForegroundColor Yellow
					}
				} catch {
					# ignore log fetch failures
				}
				throw
			}
		} finally {
			Remove-Item -LiteralPath $localSh -Force -ErrorAction SilentlyContinue
		}
	}
	function Invoke-RemoteSudoCapture([string]$RemoteCmd) {
		$escaped = $RemoteCmd -replace "'", "'\''"
		$cmd = "sudo -n bash -c '$escaped'"
		try {
			$out = Invoke-UtooSshRetry -What ("sudo-capture: $RemoteCmd") -Action {
				& $script:UtooSshExe @SshArgs $SshTarget $cmd
			}
			return (($out | Out-String).Trim())
		} catch {
			$errText = "$_"
			if ($errText -match 'exit 255|Connection timed out|Connection refused|Connection reset') {
				throw
			}
			if (-not (Test-UtooSudoUnavailable $errText)) {
				throw
			}
			Write-Host ('[deploy] sudo -n capture unavailable; retrying without sudo: {0}' -f $RemoteCmd) -ForegroundColor Yellow
			$out = Invoke-UtooSshRetry -What ("ssh-capture(no-sudo): $RemoteCmd") -Action {
				& $script:UtooSshExe @SshArgs $SshTarget $RemoteCmd
			}
			return (($out | Out-String).Trim())
		}
	}
	function Invoke-RemoteBashScriptCapture([string]$LocalScriptPath, [hashtable]$Replacements) {
		$text = [IO.File]::ReadAllText($LocalScriptPath)
		foreach ($k in $Replacements.Keys) { $text = $text.Replace($k, [string]$Replacements[$k]) }
		$remoteSh = "/tmp/utoo_ci_{0}.sh" -f [Guid]::NewGuid().ToString('N')
		$localSh = Join-Path $env:TEMP ("utoo_ci_{0}.sh" -f [Guid]::NewGuid().ToString('N'))
		try {
			$unix = ($text -replace "`r`n", "`n" -replace "`r", "`n")
			[IO.File]::WriteAllText($localSh, $unix, [Text.UTF8Encoding]::new($false))
			Invoke-Scp -LocalPath $localSh -RemotePath $remoteSh
			$out = Invoke-RemoteSudoCapture ("bash {0}; ec=`$?; if [ `$ec -eq 0 ]; then rm -f {0}; else echo [deploy] remote script failed kept={0} ec=`$ec >&2; fi; exit `$ec" -f $remoteSh)
			return $out
		} finally {
			Remove-Item -LiteralPath $localSh -Force -ErrorAction SilentlyContinue
		}
	}

	function Sync-DirToRemote([string]$LocalDir, [string]$RemoteDir, [string[]]$Exclude, [string[]]$PreserveNames) {
		$preserveExpr = ($PreserveNames | ForEach-Object { "-not -name $_" }) -join ' '
		if ([string]::IsNullOrWhiteSpace($preserveExpr)) { $preserveExpr = '-not -name .keep' }
		# chown first so leftover root/service-owned __pycache__ can be removed under sudo.
		$clean = @(
			"mkdir -p {0}",
			"chown -R {2}:{2} {0} || true",
			"find {0} -mindepth 1 -maxdepth 1 {1} -print0 | xargs -0r rm -rf",
			"find {0} -type d -name __pycache__ -prune -print0 2>/dev/null | xargs -0r rm -rf || true",
			"find {0} -type f -name '*.pyc' -delete 2>/dev/null || true"
		) -join '; '
		Invoke-RemoteSudo ($clean -f $RemoteDir, $preserveExpr, $DeployUser)
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

	# --- 网关发布：按公网 Nginx upstream 解析空闲槽（保留整套发布回退路径）---
	$needGatewaySlot = ($DeployPhase -eq 'all' -or $DeployPhase -eq 'libs_services' -or $DeployPhase -eq 'gateway')
	$Slot = $null
	$RemoteRoot = $null
	$GwPort = $null

	if ($needGatewaySlot) {
		Write-Host ("[deploy] discover active upstream from {0}" -f $UpstreamConf)
		$activePort = (Invoke-RemoteBashScriptCapture -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-discover-upstream-port.sh') -Replacements @{
			'__CONF__' = $UpstreamConf
		}).Trim()
		if ($activePort -notmatch '^(18083|18183)$') {
			Write-Host ("[deploy][warn] unexpected active port '{0}', fallback 18083" -f $activePort) -ForegroundColor Yellow
			$activePort = '18083'
		}
		Write-Host ("[deploy] Nginx active gateway port: {0}" -f $activePort)

		if ($activePort -eq '18083') {
			$Slot = 'green'
			$RemoteRoot = '/opt/utoo-green'
			$GwPort = 18183
			$UpstreamUnits = @(
				@{ Dir = 'qd_svc_order'; Service = 'qd-order-green'; Port = 18182 },
				@{ Dir = 'qd_svc_payment'; Service = 'qd-payment-green'; Port = 18184 },
				@{ Dir = 'qd_svc_admin_asset'; Service = 'qd-admin-asset-green'; Port = 18190 },
				@{ Dir = 'qd_svc_admin_platform'; Service = 'qd-admin-platform-green'; Port = 18191 }
			)
			$GatewayUnit = @{ Dir = 'qd_test_server_django'; Service = 'qd-gateway-green'; Port = 18183 }
		} else {
			$Slot = 'blue'
			$RemoteRoot = '/opt/utoo-blue'
			$GwPort = 18083
			$UpstreamUnits = @(
				@{ Dir = 'qd_svc_order'; Service = 'qd-order-blue'; Port = 18082 },
				@{ Dir = 'qd_svc_payment'; Service = 'qd-payment-blue'; Port = 18084 },
				@{ Dir = 'qd_svc_admin_asset'; Service = 'qd-admin-asset-blue'; Port = 18090 },
				@{ Dir = 'qd_svc_admin_platform'; Service = 'qd-admin-platform-blue'; Port = 18091 }
			)
			$GatewayUnit = @{ Dir = 'qd_test_server_django'; Service = 'qd-gateway-blue'; Port = 18083 }
		}
		Write-Host ("[deploy] idle slot={0} root={1} new_gateway={2}" -f $Slot, $RemoteRoot, $GwPort) -ForegroundColor Cyan
	}

	# --- 单上游服务发布：按该服务的 Nginx upstream 解析自己的空闲槽 ---
	$SingleServiceUnit = $null
	if ($DeployPhase -eq 'service') {
		$serviceDefinitions = @{
			'order' = @{
				Dir = 'qd_svc_order'; UnitBase = 'qd-order'; BluePort = 18082; GreenPort = 18182
				UpstreamFile = 'utoo_upstream_order.conf'
			}
			'payment' = @{
				Dir = 'qd_svc_payment'; UnitBase = 'qd-payment'; BluePort = 18084; GreenPort = 18184
				UpstreamFile = 'utoo_upstream_payment.conf'
			}
			'admin_asset' = @{
				Dir = 'qd_svc_admin_asset'; UnitBase = 'qd-admin-asset'; BluePort = 18090; GreenPort = 18190
				UpstreamFile = 'utoo_upstream_admin_asset.conf'
			}
			'admin_platform' = @{
				Dir = 'qd_svc_admin_platform'; UnitBase = 'qd-admin-platform'; BluePort = 18091; GreenPort = 18191
				UpstreamFile = 'utoo_upstream_admin_platform.conf'
			}
		}
		$definition = $serviceDefinitions[$DeployService]
		if ($null -eq $definition) {
			throw "No independent deployment definition for service: $DeployService"
		}

		$serviceConf = "{0}/{1}" -f $ServiceUpstreamConfDir, $definition.UpstreamFile
		$portRegex = "{0}|{1}" -f $definition.BluePort, $definition.GreenPort
		Write-Host ("[deploy] discover active {0} upstream from {1}" -f $DeployService, $serviceConf)
		$activePort = (Invoke-RemoteBashScriptCapture -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-discover-service-port.sh') -Replacements @{
			'__CONF__' = $serviceConf
			'__PORTS__' = $portRegex
			'__DEFAULT_PORT__' = [string]$definition.BluePort
		}).Trim()
		if ($activePort -notmatch ("^({0})$" -f $portRegex)) {
			Write-Host ("[deploy][warn] unexpected active {0} port '{1}', fallback {2}" -f $DeployService, $activePort, $definition.BluePort) -ForegroundColor Yellow
			$activePort = [string]$definition.BluePort
		}

		if ($activePort -eq [string]$definition.BluePort) {
			$Slot = 'green'
			$RemoteRoot = '/opt/utoo-green'
			$targetPort = $definition.GreenPort
		} else {
			$Slot = 'blue'
			$RemoteRoot = '/opt/utoo-blue'
			$targetPort = $definition.BluePort
		}
		$SingleServiceUnit = @{
			Dir = $definition.Dir
			Service = ("{0}-{1}" -f $definition.UnitBase, $Slot)
			Port = $targetPort
			UpstreamFile = $definition.UpstreamFile
		}
		Write-Host ("[deploy] active {0}=:{1}; deploy {2} to idle {3}=:{4}" -f $DeployService, $activePort, $SingleServiceUnit.Service, $Slot, $targetPort) -ForegroundColor Cyan
	}

	function Sync-DjangoUnitCode {
		param(
			[Parameter(Mandatory)][hashtable]$Unit,
			[Parameter(Mandatory)][string]$SlotRoot
		)
		$dir = $Unit.Dir
		$svc = $Unit.Service
		$port = $Unit.Port
		$localDir = Join-Path $root $dir
		if (-not (Test-Path -LiteralPath $localDir)) {
			throw "Local service directory missing: $localDir"
		}
		$remoteDir = "{0}/{1}" -f $SlotRoot, $dir

		Write-Host ("[deploy] === sync {0} ({1} :{2}) ===" -f $dir, $svc, $port) -ForegroundColor Cyan
		# Idle unit may still be running; stop so wipe does not race with writing .pyc
		Invoke-RemoteSudo ("systemctl stop {0} || true" -f $svc)
		Sync-DirToRemote `
			-LocalDir $localDir `
			-RemoteDir $remoteDir `
			-Exclude @('.venv', '__pycache__', '*.pyc', '.git', '.env', '.env.local', 'tests', '.pytest_cache') `
			-PreserveNames @('.venv', '.env', '.env.local')

		# 确保槽内 config/shared-database.env 可用（symlink 到共享目录）
		Invoke-RemoteSudo ("mkdir -p {0}/config {1} && if [ -f {1}/shared-database.env ] && [ ! -e {0}/config/shared-database.env ]; then ln -sfn {1}/shared-database.env {0}/config/shared-database.env; fi" -f $SlotRoot, $SharedConfig)

		$envCheck = ("if [ ! -f {0}/.env ] && [ ! -f {1}/config/shared-database.env ]; then echo deploy_error_missing_env:{2}; exit 1; fi" -f $remoteDir, $SlotRoot, $dir)
		Invoke-Remote $envCheck
	}

	function Deploy-DjangoUnit {
		param(
			[Parameter(Mandatory)][hashtable]$Unit,
			[Parameter(Mandatory)][string]$SlotRoot
		)
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
		$healthWait = ('j=1; while [ $j -le 60 ]; do if curl -sf "{0}" >/dev/null; then echo deploy_health_ok:{1}; exit 0; fi; sleep 1; j=$((j+1)); done; echo deploy_health_fail:{1} >&2; systemctl --no-pager status {1} -l || true; journalctl -u {1} -n 80 --no-pager || true; exit 1' -f $healthUrl, $svc)
		Invoke-RemoteSudo $healthWait
	}

	$doLibsServices = ($DeployPhase -eq 'all' -or $DeployPhase -eq 'libs_services')
	$doGateway = ($DeployPhase -eq 'all' -or $DeployPhase -eq 'gateway')
	$doSingleService = ($DeployPhase -eq 'service')
	$doStatic = ($DeployPhase -eq 'all' -or $DeployPhase -eq 'static')
	$script:StagedDistTar = $null

	if ($doSingleService) {
		Write-Host ("[deploy] sync qd_libs_common -> {0} for {1}" -f $RemoteRoot, $DeployService)
		Sync-DirToRemote `
			-LocalDir (Join-Path $root 'qd_libs_common') `
			-RemoteDir ("{0}/qd_libs_common" -f $RemoteRoot) `
			-Exclude @('.venv', '__pycache__', '*.pyc', '.git', '*.egg-info') `
			-PreserveNames @('.keep')
		Invoke-RemoteSudo ("mkdir -p {0}/config {1}" -f $RemoteRoot, $SharedConfig)
		Deploy-DjangoUnit -Unit $SingleServiceUnit -SlotRoot $RemoteRoot

		Write-Host ("[deploy] switch {0} upstream -> {1} via {2}" -f $DeployService, $SingleServiceUnit.Port, $ServiceSwitchScript)
		Invoke-RemoteSudo ("/bin/bash '{0}' {1} {2}" -f $ServiceSwitchScript, $DeployService, $SingleServiceUnit.Port)
		Write-Host ("[deploy] phase service done: {0}." -f $DeployService)
	}

	if ($doLibsServices) {
		Write-Host ("[deploy] sync qd_libs_common -> {0}" -f $RemoteRoot)
		Sync-DirToRemote `
			-LocalDir (Join-Path $root 'qd_libs_common') `
			-RemoteDir ("{0}/qd_libs_common" -f $RemoteRoot) `
			-Exclude @('.venv', '__pycache__', '*.pyc', '.git', '*.egg-info') `
			-PreserveNames @('.keep')
		Invoke-RemoteSudo ("mkdir -p {0}/config {1}" -f $RemoteRoot, $SharedConfig)

		# Stop idle-slot units before wipe/sync so gunicorn cannot recreate root-owned __pycache__.
		$stopList = ($UpstreamUnits | ForEach-Object { $_.Service }) -join ' '
		Write-Host ("[deploy] stop idle units before sync: {0}" -f $stopList) -ForegroundColor Cyan
		Invoke-RemoteSudo ("systemctl stop {0} || true" -f $stopList)

		# Sync code sequentially (SCP from Windows), then pip/restart in parallel on the server.
		$specParts = @()
		foreach ($unit in $UpstreamUnits) {
			Sync-DjangoUnitCode -Unit $unit -SlotRoot $RemoteRoot
			$specParts += ("{0}|{1}|{2}" -f $unit.Dir, $unit.Service, $unit.Port)
		}
		Write-Host ('[deploy] parallel pip/restart for {0} services...' -f $UpstreamUnits.Count) -ForegroundColor Cyan
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-units-parallel.sh') -Replacements @{
			'__ROOT__' = $RemoteRoot
			'__SPECS__' = ($specParts -join ';')
		}

		# Align internal :190xx upstreams with idle slot (one nginx reload).
		$portByDir = @{}
		foreach ($unit in $UpstreamUnits) { $portByDir[$unit.Dir] = [string]$unit.Port }
		Write-Host '[deploy] batch switch service upstreams (single nginx reload)' -ForegroundColor Cyan
		Invoke-RemoteBashScript -LocalScriptPath (Join-Path $PSScriptRoot 'ci-remote-switch-services-batch.sh') -Replacements @{
			'__NGINX_CONF_DIR__' = $ServiceUpstreamConfDir
			'__ORDER_PORT__' = $portByDir['qd_svc_order']
			'__PAYMENT_PORT__' = $portByDir['qd_svc_payment']
			'__ASSET_PORT__' = $portByDir['qd_svc_admin_asset']
			'__PLATFORM_PORT__' = $portByDir['qd_svc_admin_platform']
		}
		Write-Host '[deploy] phase libs_services done.'
	}

	if ($doGateway) {
		# 若仅跑 gateway 阶段，仍需已解析槽位
		if (-not $RemoteRoot) { throw 'gateway phase requires slot resolution' }
		Deploy-DjangoUnit -Unit $GatewayUnit -SlotRoot $RemoteRoot

		# 同步后立刻核对关键路由已落盘（避免切流了但代码没上去）
		$remoteUrls = ("{0}/qd_test_server_django/config/urls.py" -f $RemoteRoot)
		$markerCheck = ("if grep -q adminLabSale {0}; then echo deploy_urls_marker_ok; else echo deploy_urls_marker_missing >&2; exit 1; fi" -f $remoteUrls)
		Write-Host ("[deploy] verify remote urls.py contains adminLabSale ({0})" -f $remoteUrls)
		Invoke-RemoteSudo $markerCheck

		Write-Host ("[deploy] switch nginx upstream -> {0} via {1}" -f $GwPort, $SwitchScript)
		Invoke-RemoteSudo ("/bin/bash '{0}' {1}" -f $SwitchScript, $GwPort)

		# 切流后探测公网：新路由必须是 JSON，不能是 Django HTML 404
		$publicBase = (Get-CiEnv 'UTOO_PUBLIC_WEB_BASE')
		if ([string]::IsNullOrWhiteSpace($publicBase)) { $publicBase = 'https://uat.utoodev.laide.tech' }
		$publicBase = $publicBase.TrimEnd('/')
		$probeUrl = "{0}/api/adminLabSale/expOrderList.ajax" -f $publicBase
		$probeOut = Join-Path $env:TEMP ("utoo_gw_probe_{0}.body" -f [Guid]::NewGuid().ToString('N'))
		try {
			Write-Host ("[deploy] probe public gateway route: {0}" -f $probeUrl)
			$probeCode = (& curl.exe -sS -o $probeOut -w "%{http_code}" --max-time 30 -X POST $probeUrl `
				-H "Content-Type: application/x-www-form-urlencoded" `
				-d "sale_user_id=1&month=2026-06&type=1&start=0&length=10&draw=1")
			$probeCode = ("$probeCode").Trim()
			$probeBody = Get-Content -LiteralPath $probeOut -Raw -Encoding utf8
			$previewLen = [Math]::Min(160, $probeBody.Length)
			Write-Host ("[deploy] probe http={0} body={1}" -f $probeCode, $probeBody.Substring(0, $previewLen))
			if ($probeBody -match 'Page not found|didn.?t match any of these') {
				Write-Error @"
Gateway switch verification FAILED: public $probeUrl still returns Django HTML 404.
Nginx may not be using $UpstreamConf, or traffic still hits the old slot.
Switched to gateway port $GwPort. On server check:
  cat $UpstreamConf
  curl -sS -X POST http://127.0.0.1:$GwPort/api/adminLabSale/expOrderList.ajax -d 'sale_user_id=1&month=2026-06&type=1&start=0&length=10&draw=1'
"@
				exit 1
			}
			# 期望 JSON（未登录也行）
			if ($probeBody -notmatch '"res"\s*:|"code"\s*:') {
				Write-Error ("Gateway switch verification FAILED: expected JSON from {0}, got:`n{1}" -f $probeUrl, $probeBody.Substring(0, [Math]::Min(400, $probeBody.Length)))
				exit 1
			}
			Write-Host '[deploy] verified public gateway serves adminLabSale JSON'
		} finally {
			Remove-Item -LiteralPath $probeOut -Force -ErrorAction SilentlyContinue
		}
		Write-Host '[deploy] phase gateway done (switched).'
	}

	if ($doStatic) {
		$webDist = Join-Path $root 'qd_web_front/dist'
		if (-not (Test-Path -LiteralPath $webDist)) { Write-Error "Missing $webDist — run build_frontend_* first"; exit 1 }
		$localIndex = Join-Path $webDist 'index.html'
		if (-not (Test-Path -LiteralPath $localIndex)) { Write-Error "Missing $localIndex"; exit 1 }
		$localIndexText = Get-Content -LiteralPath $localIndex -Raw -Encoding utf8
		if ($localIndexText -notmatch 'src="/assets/(index-[^"]+\.js)"') {
			Write-Error 'Local dist/index.html has no /assets/index-*.js entry'
			exit 1
		}
		$expectedAsset = $Matches[1]
		$buildInfoPath = Join-Path $webDist 'build-info.json'
		if (-not (Test-Path -LiteralPath $buildInfoPath)) {
			Write-Error "Missing $buildInfoPath — refuse to publish dist without build stamp (possible stale package)"
			exit 1
		}
		$buildInfoText = Get-Content -LiteralPath $buildInfoPath -Raw -Encoding utf8
		$expectedCommit = (($env:CI_COMMIT_SHA | ForEach-Object { "$_" }).Trim())
		if (-not [string]::IsNullOrWhiteSpace($expectedCommit) -and ($buildInfoText.IndexOf($expectedCommit, [StringComparison]::OrdinalIgnoreCase) -lt 0)) {
			Write-Error ("Local build-info.json does not contain CI_COMMIT_SHA={0}. Refusing stale/wrong dist.`n{1}" -f $expectedCommit, $buildInfoText)
			exit 1
		}
		Write-Host ("[deploy] sync unified front static -> {0} (expect {1})" -f $StaticWeb, $expectedAsset)
		Write-Host ("[deploy] local build-info: {0}" -f $buildInfoText.Trim())
		# 若线上仍是本机 manual-local 旧包，先打日志方便对照
		try {
			$prevInfo = (Invoke-RemoteCapture ("cat {0}/build-info.json 2>/dev/null || true" -f $StaticWeb))
			if (-not [string]::IsNullOrWhiteSpace($prevInfo)) {
				Write-Host ("[deploy] remote build-info BEFORE sync: {0}" -f $prevInfo.Trim()) -ForegroundColor Yellow
				if ($prevInfo -match 'manual-local') {
					Write-Host '[deploy] WARNING: remote site was published by manual-local deploy; CI will overwrite it.' -ForegroundColor Yellow
				}
			}
		} catch { }
		Sync-DirToRemote -LocalDir $webDist -RemoteDir $StaticWeb -Exclude @() -PreserveNames @('.keep')
		$remoteIndex = (Invoke-RemoteCapture ("cat {0}/index.html" -f $StaticWeb))
		if ($remoteIndex -notmatch [regex]::Escape($expectedAsset)) {
			Write-Error ("Remote {0}/index.html does not reference {1} after sync. Got:`n{2}" -f $StaticWeb, $expectedAsset, $remoteIndex)
			exit 1
		}
		$remoteBuildInfo = (Invoke-RemoteCapture ("cat {0}/build-info.json" -f $StaticWeb))
		if (-not [string]::IsNullOrWhiteSpace($expectedCommit) -and ($remoteBuildInfo.IndexOf($expectedCommit, [StringComparison]::OrdinalIgnoreCase) -lt 0)) {
			Write-Error ("Remote build-info.json does not contain CI_COMMIT_SHA={0}. Got:`n{1}" -f $expectedCommit, $remoteBuildInfo)
			exit 1
		}
		Write-Host ("[deploy] verified remote index.html -> {0}" -f $expectedAsset)
		Write-Host ("[deploy] verified remote build-info.json -> {0}" -f $expectedCommit)
		# Extra gate: public HTTPS must serve the same entry JS (catches wrong nginx root / CDN / failed sync).
		$publicBase = (Get-CiEnv 'UTOO_PUBLIC_WEB_BASE')
		if ([string]::IsNullOrWhiteSpace($publicBase)) { $publicBase = 'https://uat.utoodev.laide.tech' }
		$publicBase = $publicBase.TrimEnd('/')
		try {
			$tmpIdx = Join-Path $env:TEMP ("utoo_pub_idx_{0}.html" -f [Guid]::NewGuid().ToString('N'))
			& curl.exe -sS -o $tmpIdx --max-time 30 -H 'Cache-Control: no-cache' ("{0}/index.html?t={1}" -f $publicBase, [DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
			if ($LASTEXITCODE -ne 0) { throw "curl index failed exit=$LASTEXITCODE" }
			$pubHtml = Get-Content -LiteralPath $tmpIdx -Raw -Encoding utf8
			if ($pubHtml -notmatch [regex]::Escape($expectedAsset)) {
				Write-Error ("Public {0}/index.html does not reference {1} after deploy. Got:`n{2}" -f $publicBase, $expectedAsset, $pubHtml.Substring(0, [Math]::Min(500, $pubHtml.Length)))
				exit 1
			}
			Write-Host ("[deploy] verified public site {0} -> {1}" -f $publicBase, $expectedAsset)
		} catch {
			Write-Error ("Public site verification failed: {0}" -f $_.Exception.Message)
			exit 1
		} finally {
			Remove-Item -LiteralPath $tmpIdx -Force -ErrorAction SilentlyContinue
		}
		Write-Host '[deploy] phase static done.'
	}

	Write-Host ("utoo deploy phase={0} finished OK." -f $DeployPhase)
} finally {
	Remove-Item -LiteralPath $keyFile -Force -ErrorAction SilentlyContinue
	Remove-Item -LiteralPath $knownHostsFile -Force -ErrorAction SilentlyContinue
}

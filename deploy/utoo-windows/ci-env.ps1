# Shared GitLab CI env helpers (P5: mall-origin scripts inside utoo-pydjango).

function Get-QdMallCiEnv([string]$Name) {
	if (-not (Test-Path "env:$Name")) { return $null }
	(Get-Item "env:$Name").Value
}

function Resolve-QdMallDeployTarget {
	# Prefer QD_MALL_*; accept UTOO_DEPLOY_TARGET from legacy utoo CI jobs.
	$t = Get-QdMallCiEnv 'QD_MALL_DEPLOY_TARGET'
	if ([string]::IsNullOrWhiteSpace($t)) { $t = Get-QdMallCiEnv 'UTOO_DEPLOY_TARGET' }
	if (-not [string]::IsNullOrWhiteSpace($t)) { return $t.Trim().ToLowerInvariant() }
	$ref = Get-QdMallCiEnv 'CI_COMMIT_REF_NAME'
	if ($ref -eq 'prod') { return 'prod' }
	return 'dev'
}

function Import-QdMallDeployLocalEnv {
	param(
		[Parameter(Mandatory)][string]$RepoRoot,
		[string]$DeployTarget = (Resolve-QdMallDeployTarget)
	)
	$ciLocal = Join-Path $RepoRoot 'deploy/ci-local'
	# Prefer qd-mall host env (same server slots); fall back to utoo-deploy.* on this runner.
	$localCandidates = @(
		'C:\ProgramData\qd-mall-deploy.env.ps1',
		("C:\ProgramData\qd-mall-deploy-{0}.env.ps1" -f $DeployTarget),
		(Join-Path $ciLocal ("qd-mall-deploy-{0}.env.ps1" -f $DeployTarget)),
		'C:\ProgramData\utoo-deploy.env.ps1',
		("C:\ProgramData\utoo-deploy-{0}.env.ps1" -f $DeployTarget),
		(Join-Path $ciLocal ("utoo-deploy-{0}.env.ps1" -f $DeployTarget))
	)
	foreach ($f in $localCandidates) {
		if (Test-Path -LiteralPath $f) {
			. $f
			Write-Host ("[deploy] loaded local env: {0}" -f $f) -ForegroundColor DarkGreen
			return $f
		}
	}
	return $null
}

function Get-QdMallBranchAwareEnv([string]$BaseName) {
	$target = Resolve-QdMallDeployTarget
	foreach ($n in @("${BaseName}_$($target.ToUpperInvariant())", $BaseName)) {
		$v = Get-QdMallCiEnv $n
		if (-not [string]::IsNullOrWhiteSpace($v)) {
			Write-Host ("[deploy] env {0} from {1}" -f $BaseName, $n)
			return $v
		}
	}
	return $null
}

function Resolve-QdMallSecretMaterial {
	param([Parameter(Mandatory)][string]$Value)
	$v = ($Value | ForEach-Object { "$_" }).Trim()
	if ([string]::IsNullOrWhiteSpace($v)) { return $null }
	if ($v -like '-----BEGIN*') { return $v }
	if (Test-Path -LiteralPath $v -PathType Leaf) {
		Write-Host ("[deploy] read secret material from file: {0}" -f $v)
		return [IO.File]::ReadAllText($v)
	}
	return $v
}

function Resolve-QdMallSshPrivateKey {
	param([string]$DeployTarget = (Resolve-QdMallDeployTarget))
	$target = $DeployTarget.ToUpperInvariant()
	$candidates = @(
		"SSH_PRIVATE_KEY_${target}_FILE",
		"SSH_PRIVATE_KEY_$target",
		"SSH_PRIVATE_KEY_${target}_B64",
		'SSH_PRIVATE_KEY_FILE',
		'SSH_PRIVATE_KEY',
		'SSH_PRIVATE_KEY_B64'
	)
	foreach ($name in $candidates) {
		$raw = Get-QdMallCiEnv $name
		if ([string]::IsNullOrWhiteSpace($raw)) { continue }
		if ($name -like '*_FILE') {
			if (-not (Test-Path -LiteralPath $raw.Trim() -PathType Leaf)) {
				Write-Warning ("[deploy] ssh key file not found: {0}={1}" -f $name, $raw)
				continue
			}
			$material = [IO.File]::ReadAllText($raw.Trim())
			if ($material -like '-----BEGIN*') {
				Write-Host ("[deploy] ssh key from {0}" -f $name)
				return $material
			}
			continue
		}
		if ($name -like '*_B64') {
			try {
				$bytes = [Convert]::FromBase64String($raw.Trim())
				$decoded = [Text.Encoding]::UTF8.GetString($bytes)
				if ($decoded -like '-----BEGIN*') {
					Write-Host ("[deploy] ssh key from {0} (base64)" -f $name)
					return $decoded
				}
			} catch {
				Write-Warning ("[deploy] ignore invalid base64 in {0}" -f $name)
			}
			continue
		}
		$material = Resolve-QdMallSecretMaterial -Value $raw
		if ($material -like '-----BEGIN*') {
			Write-Host ("[deploy] ssh key from {0}" -f $name)
			return $material
		}
	}
	return $null
}

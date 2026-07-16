# Shared bootstrap for qd_svc_* / gateway start-*.ps1
# Usage: . "$PSScriptRoot\_start-svc.ps1"; Start-QdService -RelPath "qd_svc_wx"

function Start-QdService {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelPath,
        [string]$CheckImport = "pymysql"
    )

    $Root = Split-Path -Parent $PSScriptRoot
    $SvcDir = Join-Path $Root $RelPath
    Set-Location $SvcDir

    $py = Join-Path $SvcDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) {
        Write-Host "Creating venv in $SvcDir ..."
        python -m venv .venv
        if (-not (Test-Path $py)) {
            throw "Failed to create venv: $py"
        }
    }

    # Quiet probe — missing module is expected until first install
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $null = & $py -c "import $CheckImport" 2>&1 | Out-Null
    $hasImport = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $prevEap

    if (-not $hasImport) {
        Write-Host "Dependencies missing for $RelPath — installing (first run)..."
        & $py -m pip install -q -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            & $py -m pip install -r requirements.txt
        }
        $libs = Join-Path $Root "qd_libs_common"
        if (Test-Path $libs) {
            & $py -m pip install -q -e $libs
            if ($LASTEXITCODE -ne 0) {
                & $py -m pip install -e $libs
            }
        }
    }

    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Copy-Item ".env.example" ".env"
    }

    & $py run.py
}

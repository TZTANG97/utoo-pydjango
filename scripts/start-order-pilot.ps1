# Order-domain middle-platform pilot: open gateway + qd_svc_order in two terminals.
# Prerequisite: gateway .env (or .env.local) has SVC_ORDER_URL=http://127.0.0.1:18082
# Docs: E:\utoo\docs\现网架构说明.md
# Usage from repo root:  .\scripts\start-order-pilot.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Scripts = Join-Path $Root "scripts"

$jobs = @(
    @{ Name = "order"; Script = "start-order.ps1"; Port = 18082 },
    @{ Name = "gateway"; Script = "start-gateway.ps1"; Port = 18083 }
)

Write-Host "Order pilot: opening gateway + order only." -ForegroundColor Cyan
Write-Host "Ensure SVC_ORDER_URL=http://127.0.0.1:18082 in qd_test_server_django/.env" -ForegroundColor Yellow
Write-Host "Checklist: E:\utoo\docs\现网架构说明.md" -ForegroundColor DarkGray
Write-Host ""

foreach ($j in $jobs) {
    $path = Join-Path $Scripts $j.Script
    if (-not (Test-Path $path)) {
        Write-Warning "Missing script: $path"
        continue
    }
    Write-Host ("  -> {0,-12} :{1}  {2}" -f $j.Name, $j.Port, $j.Script)
    Start-Process -FilePath "powershell.exe" -WorkingDirectory $Root -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", $path
    )
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "Started. Health: http://127.0.0.1:18083/health" -ForegroundColor Green
Write-Host "Order svc: http://127.0.0.1:18082 (see svc README for health if any)" -ForegroundColor Green

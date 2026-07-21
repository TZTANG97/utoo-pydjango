# 微服务开发：独立终端拉起「网关 + 4 业务服务」（order/payment/asset/platform）
# 前提：仓库根已有 config/shared-database.env；网关 .env 已启用 SVC_*_URL
#   - 勿设 SVC_AUTH_URL（C 端认证在网关）
#   - SVC_WX_URL 与 SVC_PAYMENT_URL 同指 :18084
# 用法：在仓库根执行  .\scripts\start-ms-dev.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Scripts = Join-Path $Root "scripts"

$jobs = @(
    @{ Name = "gateway"; Script = "start-gateway.ps1"; Port = 18083 },
    @{ Name = "order"; Script = "start-order.ps1"; Port = 18082 },
    @{ Name = "payment+wx"; Script = "start-payment.ps1"; Port = 18084 },
    @{ Name = "admin-asset"; Script = "start-admin-asset.ps1"; Port = 18090 },
    @{ Name = "admin-platform"; Script = "start-admin-platform.ps1"; Port = 18091 }
)

Write-Host "Opening $($jobs.Count) terminals for microservice mode..." -ForegroundColor Cyan
Write-Host "Frontend still targets http://127.0.0.1:18083 only." -ForegroundColor DarkGray
Write-Host "C-end auth + admin login stay on gateway. /api/wx/* served by payment :18084." -ForegroundColor DarkGray
Write-Host ""

foreach ($j in $jobs) {
    $path = Join-Path $Scripts $j.Script
    if (-not (Test-Path $path)) {
        Write-Warning "Missing script: $path"
        continue
    }
    Write-Host ("  -> {0,-16} :{1}  {2}" -f $j.Name, $j.Port, $j.Script)
    Start-Process -FilePath "powershell.exe" -WorkingDirectory $Root -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", $path
    )
    Start-Sleep -Milliseconds 400
}

Write-Host ""
Write-Host "All launch windows started. Check each window for bind errors / DB issues." -ForegroundColor Green
Write-Host "Health: http://127.0.0.1:18083/health" -ForegroundColor Green

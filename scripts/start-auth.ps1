# Start auth — DEPRECATED
# C-end auth is in-process on the gateway (apps/auth_pc). Do not start qd_svc_auth.
Write-Host "qd_svc_auth is deprecated. C-end auth runs on the gateway (clear SVC_AUTH_URL)." -ForegroundColor Yellow
Write-Host "Use: .\scripts\start-gateway.ps1" -ForegroundColor Cyan
exit 0

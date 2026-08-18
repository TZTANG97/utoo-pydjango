# qd_svc_auth has been removed. Password login is qd_svc_identity.
Write-Host "qd_svc_auth was removed. Do not set SVC_AUTH_URL." -ForegroundColor Yellow
Write-Host "Password login: .\scripts\start-identity.ps1  (local :18110)" -ForegroundColor Cyan
Write-Host "Production: SVC_IDENTITY_URL=http://127.0.0.1:19081 + deploy_identity_*" -ForegroundColor Cyan
exit 0

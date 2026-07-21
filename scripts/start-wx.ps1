# Start wx — DEPRECATED (merged into qd_svc_payment :18084)
# Forwards to start-payment.ps1 so old habits still work.
Write-Host "qd_svc_wx merged into qd_svc_payment (:18084). Starting payment..." -ForegroundColor Yellow
Write-Host "Set SVC_WX_URL=http://127.0.0.1:18084 (same as SVC_PAYMENT_URL)." -ForegroundColor Cyan
. "$PSScriptRoot\_start-svc.ps1"
Start-QdService -RelPath "qd_svc_payment"

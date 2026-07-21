# Start payment :18084
. "$PSScriptRoot\_start-svc.ps1"
Start-QdService -RelPath "qd_svc_payment"

# Start admin asset :18090
. "$PSScriptRoot\_start-svc.ps1"
Start-QdService -RelPath "qd_svc_admin_asset"

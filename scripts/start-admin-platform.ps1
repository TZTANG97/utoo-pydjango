# Start admin platform :18091
. "$PSScriptRoot\_start-svc.ps1"
Start-QdService -RelPath "qd_svc_admin_platform"

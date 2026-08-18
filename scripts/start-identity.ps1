# Start identity mid-platform :18110
. "$PSScriptRoot\_start-svc.ps1"
Start-QdService -RelPath "qd_svc_identity"

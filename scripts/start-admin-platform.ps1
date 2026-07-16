# 启动后台 Platform 微服务 :18091（含原 entry/invoice）
. "$PSScriptRoot\_start-svc.ps1"
Start-QdService -RelPath "qd_svc_admin_platform"

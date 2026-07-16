# 启动 API 网关 / BFF :18083
. "$PSScriptRoot\_start-svc.ps1"
Start-QdService -RelPath "qd_test_server_django"

# 启动后台 Platform 微服务 :18091（含原 entry/invoice）
$Root = Split-Path -Parent $PSScriptRoot
Set-Location "$Root\qd_svc_admin_platform"

if (-not (Test-Path ".venv")) {
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
    .\.venv\Scripts\pip install -e "$Root\qd_libs_common"
}
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}
.\.venv\Scripts\python.exe run.py

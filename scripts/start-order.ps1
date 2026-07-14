# 启动订单 / 实验管理微服务 :18082
$Root = Split-Path -Parent $PSScriptRoot
Set-Location "$Root\qd_svc_order"

if (-not (Test-Path ".venv")) {
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
    .\.venv\Scripts\pip install -e "$Root\qd_libs_common"
}
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}
.\.venv\Scripts\python.exe run.py

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
.\.venv\Scripts\celery -A config beat -l info

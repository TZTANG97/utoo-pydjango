@echo off
setlocal
if "%CI_PROJECT_DIR%"=="" (
  echo CI_PROJECT_DIR is empty
  exit /b 1
)
cd /d "%CI_PROJECT_DIR%" || exit /b 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CI_PROJECT_DIR%\deploy\utoo-windows\ci-deploy-windows.ps1"
exit /b %ERRORLEVEL%

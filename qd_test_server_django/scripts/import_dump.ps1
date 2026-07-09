# 从 .sql 文件恢复本机 qd_pt_new（需本机已安装 mysql 客户端并在 PATH 中）
param(
    [Parameter(Mandatory = $true)]
    [string]$SqlFile,
    [string]$DbHost = "127.0.0.1",
    [string]$DbUser = "root",
    [string]$DbName = "qd_pt_new"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $SqlFile)) {
    Write-Error "文件不存在: $SqlFile"
}

$pwd = Read-Host "MySQL 密码 ($DbUser@$DbHost)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($pwd)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)

Write-Host "创建库 $DbName ..."
mysql -h $DbHost -u $DbUser -p$plain -e "CREATE DATABASE IF NOT EXISTS ``$DbName`` DEFAULT CHARSET utf8mb4;"

Write-Host "导入 $SqlFile （可能较久）..."
Get-Content $SqlFile -Raw | mysql -h $DbHost -u $DbUser -p$plain $DbName

Write-Host "完成。可执行: python scripts/check_db.py"

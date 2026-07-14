# qd_svc_admin_asset

**后台 Asset 微服务**（数字化中心 / 库存管理 / 资金管理）。

- **默认 HTTP 端口**：**18090**
- **职责**：后台数字化、库存、资金相关 `.ajax` 接口
- **共享库**：`../qd_libs_common`

## 启动

```powershell
# 仓库根
.\scripts\start-admin-asset.ps1
# 或
cd qd_svc_admin_asset
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install -e ..\qd_libs_common
copy .env.example .env
.\.venv\Scripts\python.exe run.py
```

## 网关转发

在 `qd_test_server_django/.env` 中：

```env
SVC_ADMIN_ASSET_URL=http://127.0.0.1:18090
```

未配置时网关本地处理 `apps.admin_digital` / `admin_inventory` / `admin_fund`。

## 验证

```powershell
GET http://127.0.0.1:18090/health
```

# qd_svc_admin_platform

**后台 Platform 微服务**（产品/会员/运营/服务平台/系统/订单设置/开票收款 + C 端入驻/发票）。

- **默认 HTTP 端口**：**18091**
- **吸收（已完成）**：原 `qd_svc_entry`、`qd_svc_invoice` 代码在本仓 `apps/entry`、`apps/invoices`、`apps/pc_invoice`
- **废弃仓**：请勿再启动 `qd_svc_entry` / `qd_svc_invoice`

## 启动

```powershell
# 仓库根
.\scripts\start-admin-platform.ps1
# 或
cd qd_svc_admin_platform
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install -e ..\qd_libs_common
copy .env.example .env
.\.venv\Scripts\python.exe run.py
```

## 网关

```env
SVC_ADMIN_PLATFORM_URL=http://127.0.0.1:18091
SVC_ENTRY_URL=http://127.0.0.1:18091
SVC_INVOICE_URL=http://127.0.0.1:18091
```

健康检查：`GET http://127.0.0.1:18091/health`

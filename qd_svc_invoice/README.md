# qd_svc_invoice

**发票** 微服务（MS-3）。

- **默认 HTTP 端口**：18085
- **职责**：开票申请/取消、发票抬头 CRUD、可开票订单、发票明细等 PC `.ajax` 接口。

## 启动

```powershell
E:\utoo\scripts\start-invoice.ps1
```

## 验证

```powershell
GET http://127.0.0.1:18085/health
pytest
```

## 网关转发

```
SVC_INVOICE_URL=http://127.0.0.1:18085
```

共享响应库：`../qd_libs_common`。

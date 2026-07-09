# qd_svc_payment

**支付/资产** 微服务（MS-3 首期：积分与账户）。

- **默认 HTTP 端口**：18084
- **职责**：积分/账户、余额支付、微信预下单、**支付回调**（`pay.ajax` / `rechargePay.ajax` / `amountPayBack.ajax`）等。

## 启动

```powershell
E:\utoo\scripts\start-payment.ps1
# 或
python run.py
```

## 验证

```powershell
GET http://127.0.0.1:18084/health
pytest
```

## 网关转发

在 `qd_test_server_django` 的 `.env` 中设置：

```
SVC_PAYMENT_URL=http://127.0.0.1:18084
```

网关将把积分/资产相关 `/api/pc/*` 透明转发到本服务。认证、订单接口分别由 `qd_svc_auth`、`qd_svc_order` 承担。

共享响应库：`../qd_libs_common`（`qd_common.responses`）。约定见 `E:\utoo\docs\微服务拆分与仓库约定.md`。

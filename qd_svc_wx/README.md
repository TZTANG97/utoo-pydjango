# qd_svc_wx（已废弃）

**本服务已并入 [`qd_svc_payment`](../qd_svc_payment)（:18084）。**

- 原路径 `/api/wx/*` 现由支付服务提供。
- 网关请配置：`SVC_WX_URL=http://127.0.0.1:18084`（与 `SVC_PAYMENT_URL` 相同）。
- 请使用 `.\scripts\start-payment.ps1`，勿再启动本目录进程。

保留本目录仅作对照；新功能请改 `qd_svc_payment/apps/wx/`。

# qd_svc_invoice（已废弃）

> **DEPRECATED**：C 端发票已并入 **`qd_svc_admin_platform`（:18091）**。  
> 请勿再单独启动本仓。网关请配置：
>
> ```env
> SVC_INVOICE_URL=http://127.0.0.1:18091
> SVC_ADMIN_PLATFORM_URL=http://127.0.0.1:18091
> ```
>
> 代码保留仅供对照；新改动请提交到 `qd_svc_admin_platform/apps/invoices`（及 `pc_invoice`）。

原端口：18085。历史职责：开票申请/抬头等 `/api/invoice/*`、部分 `/api/pc/*`。

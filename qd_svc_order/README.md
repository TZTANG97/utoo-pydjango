# qd_svc_order

**订单** 微服务（MS-2）。

- **默认 HTTP 端口**：18082
- **职责**：PC 订单/目录 `.ajax`、实验主单/子单、咨询/评价/省市区等订单域接口。

## 启动

```powershell
E:\utoo\scripts\start-order.ps1
# 或
python run.py
```

## 验证

```powershell
GET http://127.0.0.1:18082/health
pytest
```

## 网关转发

在 `qd_test_server_django` 的 `.env` 中设置：

```
SVC_ORDER_URL=http://127.0.0.1:18082
```

网关将把 `/api/experimentOrder/*`、`/api/experimentChildOrder/*` 及订单相关 `/api/pc/*` 透明转发到本服务。积分/资产/认证仍留在网关或其它微服务。

共享响应库：`../qd_libs_common`（`qd_common.responses`）。约定见 `E:\utoo\docs\微服务拆分与仓库约定.md`。

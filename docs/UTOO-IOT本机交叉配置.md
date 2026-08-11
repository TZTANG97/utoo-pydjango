# UTOO × IOT — 配置实勘与异机联调

## 硬约束

- **UTOO 与 IOT 不在同一台服务器**。
- 跨机调用只写对方 **公网 HTTPS 域名**，禁止写对方 `127.0.0.1` / `localhost`。
- **允许**本机环回的，仅限「同一进程所在机器内部」的上游，例如 UTOO 机上：网关 `SVC_ORDER_URL=http://127.0.0.1:18082`。

```text
[IOT 服务器]                          [UTOO 服务器]
  IOT API (公网 HTTPS)    <───────     qd_svc_order  IOT_BASE_URL
  UTOO_CALLBACK_URL       ───────>     公网网关 https://uat.utoodev.laide.tech
                                         └─ /api/iot/* → 机内 127.0.0.1:18082
```

## 正式包实勘（UTOO 机内，可写 127.0.0.1）

| 配置项 | 当前值 | 实际含义 |
|--------|--------|----------|
| 网关 `SERVER_PORT_HTTP` | `18083` | 本机监听 / 前端打 API 入口 |
| `SVC_ORDER_URL` | `http://127.0.0.1:18082` | **机内** `qd_svc_order`，不是跨机 |
| DB | 阿里云 RDS UAT | 远程库 |
| `IMAGE_WEB_SERVER` / `CORS_HTTPS` | `https://uat.utoodev.laide.tech`（以服务器实际 env 为准） | **公网站点** |
| Redis | `127.0.0.1:6379` | **机内** Redis |

## 异机联动 env（正确写法）

### `qd_svc_order/.env.local`（UTOO 机）

```env
# 必须是 IOT 公网基址（客户端会拼 /nss/...）
IOT_BASE_URL=https://www.laidecloud.com
IOT_SERVICE_TOKEN=<与 IOT 一致>
IOT_HMAC_SECRET=<与 IOT 一致>
IOT_APP_ID=utoo-iot
IOT_HTTP_TIMEOUT=15
IOT_UTOO_CALLBACK_URL=https://uat.utoodev.laide.tech/api/iot/callback/experiment-event
```

### IOT 服务器 `.env`（或 systemd EnvironmentFile）

```env
UTOO_CALLBACK_URL=https://uat.utoodev.laide.tech/api/iot/callback/experiment-event
UTOO_HMAC_SECRET=<与 UTOO 一致>
UTOO_APP_ID=utoo-iot
UTOO_SERVICE_TOKEN=<与 UTOO 一致>
UTOO_CALLBACK_TIMEOUT_S=15
UTOO_REQUIRE_TASK_FOR_CALLBACK=true
```

> 本机开发若两端都跑在本机，才可用 `127.0.0.1`；那是例外，**不是**正式异机配置。

## 公网探活（2026-08-11）

| URL | 结果 |
|-----|------|
| UTOO 站点 `https://uat.utoodev.laide.tech` | `/api/health` → Django 网关 JSON ok |
| UTOO 回调 `/api/iot/callback/experiment-event` | **404**（iot 路由尚未部署到该 UAT） |
| IOT 前端 `https://www.laidecloud.com/app/main/experiments` | SPA |
| IOT API `https://www.laidecloud.com` | `/health` → production；`/nss/api/auth/me` → 401 |
| IOT `/nss/api/v1/health/utoo-bridge` | **404**（UTOO 对接尚未部署到 IOT 正式环境） |

```powershell
curl.exe -sS https://uat.utoodev.laide.tech/api/health
curl.exe -sS -o NUL -w "%{http_code}" https://uat.utoodev.laide.tech/api/iot/callback/experiment-event
curl.exe -sS https://www.laidecloud.com/health
curl.exe -sS -o NUL -w "%{http_code}" https://www.laidecloud.com/nss/api/v1/health/utoo-bridge
```

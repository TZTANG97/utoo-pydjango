# utoo_gateway · 愉兔 API 网关

**platform/utoo_gateway**，端口 **18083**。

UTOO SPA / 小程序的 **BFF**：历史路径兼容、鉴权转发、**UTOO 菜单/me 拼装**（方案 B）。

| 项 | 值 |
|----|-----|
| 默认端口 | **18083** |
| 前端 | `utoo-web-front` → http://127.0.0.1:9530 或 **9540** |
| Git 分支 | `dev` 开发 / `prod` 生产 |
| 旧仓对照 | `utoo-pydjango/qd_test_server_django`（**禁止活跃发版**） |

---

## 方案 B 职责

| 做 | 不做 |
|----|------|
| `/api/pc/*`、`/api/experimentOrder/*`、`/api/wx/*` 等兼容 | 本地 twin 写登录/实验单 |
| 读 identity **基础**接口后拼装 UTOO me/菜单 | 写 UTOO 独有业务表（→ `utoo_biz`） |
| 转发 order / payment / asset / platform | 上游 404 静默写库（应 **503**） |
| 短信、微信一键等**编排**（令牌走 identity/payment） | 复制 order/payment 状态机 |

菜单筛选（产品逻辑）：UTOO 管理端 `type=2` / `pt_type` 含 `2`；C 端「管理菜单为空」等规则在本 BFF 实现。

---

## 快速启动

```powershell
# 推荐：仓库根
.\scripts\start-dev.ps1

# 仅网关
cd platform/utoo_gateway
copy .env.example .env
python run.py
```

健康检查：

| URL | 说明 |
|-----|------|
| `GET /health` | 简单 JSON |
| `GET /api/health/` | 统一 `{code,message,data}` |

---

## 配置

加载顺序：本目录 `.env` → 共享 `shared-database.env`（DB、JWT）→ `.env.local`（不提交）。

| 变量 | 说明 |
|------|------|
| `SVC_IDENTITY_URL` | identity 中台，如 `http://127.0.0.1:18110` |
| `SVC_ORDER_URL` | `http://127.0.0.1:18082` |
| `SVC_PAYMENT_URL` | `http://127.0.0.1:18084` |
| `SVC_ADMIN_ASSET_URL` | `http://127.0.0.1:18090` |
| `SVC_ADMIN_PLATFORM_URL` | `http://127.0.0.1:18091` |
| `JWT_SECRET_KEY` | 与 identity 一致 |
| `CORS_HTTPS` | 微信支付回调公网根（勿带 `/api`） |

**勿设** `SVC_AUTH_URL`（已删除）。`SVC_WX_URL` 与 payment 同指 **18084**。

---

## 主要 API 前缀

| 前缀 | 说明 |
|------|------|
| `/api/auth/` | 登录、刷新、当前用户 |
| `/api/pc/` | C 端 `.ajax` 兼容 |
| `/api/experimentOrder/` | 主订单 |
| `/api/experimentChildOrder/` | 子单 |
| `/api/invoice/`、`/api/entry/` | 转发 platform |
| `/api/wx/` | 微信（payment 进程） |
| `/api/redeem/` | 积分兑换（网关本地或 payment，见 urls 配置） |

完整对照：[../docs/API对照表.md](../docs/API对照表.md)（若存在于 `E:\utoo\docs` 请同步至本仓）。

---

## 与前端联调

1. 启动本服务 `:18083`
2. `cd utoo-web-front && npm run dev`（`VITE_API_TARGET=http://127.0.0.1:18083`）
3. 浏览器 http://127.0.0.1:9530 或 **9540**

---

## Celery

支付队列 + 数字化统计刷表见原脚本 `scripts/run_celery_worker.ps1`、`run_celery_beat.ps1`（需 Redis）。

---

## 相关文档

- [../../utoo-web-front/README.md](../../utoo-web-front/README.md)
- [../../services/utoo_biz/README.md](../../services/utoo_biz/README.md)
- [../docs/现网架构说明.md](../docs/现网架构说明.md)

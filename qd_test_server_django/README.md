# qd_test_server_django

青岛检测平台 **Django API 网关**（DRF + Celery）。

C 端业务接口的主入口：鉴权、兼容路由、域逻辑（单体模式）或转发到 `qd_svc_*`（微服务模式）。

| 项 | 值 |
|----|-----|
| 默认端口 | **18083** |
| GitLab | http://gitlab.wisecom-tech.com/TZJ/utoo-pydjango.git |
| 开发分支 | `dev` |
| 生产分支 | `prod` |
| 前端 | `qd_test_front_v3` → http://127.0.0.1:9530（代理 `/api` → 本服务） |

---

## 在平台中的位置

| 目录 | 角色 |
|------|------|
| `qd_test_server` | Java 旧服务（只读对照） |
| `qd_test_server_py` | FastAPI 参考实现（**冻结**） |
| **本仓库** | Django **网关 / BFF** |
| `qd_svc_*` | 微服务（auth/order/payment/…，可选） |
| `qd_libs_common` | 公共 Python 包（`qd_common`） |
| `qd_test_front_v3` | Vue3 主前端 |

平台文档：`E:\utoo\docs\`（进度、API 对照、开发启动等）。

---

## 分支约定

| 分支 | 用途 |
|------|------|
| `dev` | 日常开发、联调（默认推送） |
| `prod` | 生产发布 |
| `main` | 可选主干，与 `dev` 对齐时可同步 |

```powershell
git clone http://gitlab.wisecom-tech.com/TZJ/utoo-pydjango.git
cd utoo-pydjango
git checkout dev
```

---

## 快速启动

### 推荐：平台一键（网关 + 前端）

```powershell
# 在 E:\utoo 工作区
.\dev-start.bat
# 或
.\scripts\dev-all.ps1
```

### 仅启动本服务

```powershell
cd E:\utoo\qd_test_server_django   # 或 clone 后的目录
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 1) 数据库（全仓共用，优先）
#    复制 E:\utoo\config\shared-database.env.example
#         → E:\utoo\config\shared-database.env
#    填写 DB_*、JWT_SECRET_KEY

# 2) 本服务环境
copy .env.example .env
# 按需改 Redis、微信、CORS_HTTPS 等（勿在 .env 重复写 DB_*，见下方「配置」）

python run.py
# 或
.\scripts\run_dev.ps1
```

默认：**http://127.0.0.1:18083**

健康检查：

| URL | 说明 |
|-----|------|
| `GET /health` | 简单 JSON；`PAY_DEBUG_ENABLED=true` 时带 `payDebug` 字段 |
| `GET /` | 服务信息 |
| `GET /api/health/` | 统一响应 `{code,message,data}` |

---

## 配置

### 加载顺序

1. 本目录 `.env`（端口、Redis、微信、OSS 等）
2. `E:\utoo\config\shared-database.env`（**DB_\***、**JWT_SECRET_KEY**，网关与各微服务共用）
3. `.env.local`（本机覆盖，不提交 git）

### 必填 / 常用

| 变量 | 说明 |
|------|------|
| `DB_*` / `DB_LEGACY_MYSQL` | 写在 `shared-database.env`；MySQL 5.6 设 `true` |
| `JWT_SECRET_KEY` | 与微服务一致，否则 JWT 无法互认 |
| `SERVER_PORT_HTTP` | 默认 `18083` |
| `REDIS_*` | 支付锁 / 队列；本地可先不启 Redis 做非支付联调 |
| `CORS_HTTPS` | 微信支付回调公网根（**勿带 `/api`**），如 `https://uat.utoo.laide.tech` |
| `PAY_DEBUG_ENABLED` | 支付调试开关（页面路由待完善时见 health 提示） |
| `SVC_*_URL` | 可选；**不配则单体模式**（业务在本仓 `apps.*`） |

微服务上游示例（`.env` 中取消注释）：

```env
# SVC_AUTH_URL=http://127.0.0.1:18081
# SVC_ORDER_URL=http://127.0.0.1:18082
# SVC_PAYMENT_URL=http://127.0.0.1:18084
# SVC_INVOICE_URL=http://127.0.0.1:18085
# SVC_ENTRY_URL=http://127.0.0.1:18086
# SVC_WX_URL=http://127.0.0.1:18087
```

### 勿提交

`.env`、`.env.local`、证书 `*.pem`、`.venv/` 已在 `.gitignore`。仅提交 `.env.example`。

---

## 运行模式

### 单体（默认，日常开发）

不配置 `SVC_*_URL`。登录、订单、资产、支付、发票、入驻、微信等均在本进程处理。

### 微服务

配置对应 `SVC_*_URL` 后，网关对匹配路径做 HTTP 转发（`apps/core/*_forward.py`），域逻辑在 `qd_svc_*`。

禁止微服务之间直接 import 对方业务模块。

---

## 目录结构

```
config/                 # settings、urls、celery、MySQL 5.6 legacy 后端
apps/
  core/                 # 健康检查、统一响应、转发、中间件
  auth_pc/              # 登录 / JWT / 用户
  pc_compat/            # /api/pc/*.ajax 薄层
  orders/               # 订单、子订单、样品、复测等
  payments/             # 资产、充值、余额/微信支付
  invoices/             # 发票
  entry/                # 入驻
  wx/                   # 微信相关
tasks/                  # Celery 任务
scripts/                # 启动、检库、本地初始化
tests/                  # pytest（业务联调用 live_client）
certs/                  # 微信商户私钥（本地放置，勿提交）
```

共享库：上级目录 `qd_libs_common` → `from qd_common.responses import api_ok` 等。

---

## 主要 API 前缀

| 前缀 | 说明 |
|------|------|
| `/api/auth/` | 登录、刷新、当前用户 |
| `/api/pc/` | C 端兼容 `.ajax`（资产、个人中心、目录等） |
| `/api/experimentOrder/` | 主订单 |
| `/api/experimentChildOrder/` | 实验子订单 |
| `/api/invoice/` | 发票 |
| `/api/entry/` | 入驻 |
| `/api/wx/` | 微信 |
| `/api/offlineRecharge/` 等 | 充值 / 兑换等兼容路径 |

完整对照见平台文档：`docs/API对照表.md`。

### 微信支付回调（公网）

由 `CORS_HTTPS` + `/api` 拼接，例如：

| 场景 | 路径 |
|------|------|
| 订单支付 | `{CORS_HTTPS}/api/pc/pay.ajax` |
| 充值 | `{CORS_HTTPS}/api/pc/rechargePay.ajax` |
| 还款/多选支付 | `{CORS_HTTPS}/api/pc/amountPayBack.ajax` |

本地微信无法直连 `127.0.0.1`；联调可用 UAT 公网或内网穿透。

---

## Celery（支付队列等）

```powershell
.\scripts\run_celery_worker.ps1
```

需本机 Redis 可用；`PAY_NOTIFY_USE_QUEUE=true` 时微信回调可走队列。

---

## 测试

```powershell
.\.venv\Scripts\activate
python -m pytest tests/ -q
```

**注意：**

- 业务库联调使用 `live_client`（见 `conftest.py`），**不要**把 `DATABASES['default']['TEST']['NAME']` 设为业务库名 `qd_pt_new`。
- 曾因测试库名配置错误导致 `DROP DATABASE`；当前已修复为默认 `test_*` 库。

常用脚本：

```powershell
.\.venv\Scripts\python.exe scripts\check_db.py
.\.venv\Scripts\python.exe manage.py check
```

---

## 与前端联调

1. 启动本服务 `:18083`
2. 启动 `qd_test_front_v3`（`VITE_API_TARGET=http://127.0.0.1:18083`）
3. 浏览器打开 http://127.0.0.1:9530

测试账号以 UAT/业务库为准（勿把密码写进 README）。

---

## 相关文档

| 文档 | 路径 |
|------|------|
| 开发启动 | `E:\utoo\docs\开发启动.md` |
| 进度总览 | `E:\utoo\docs\进度总览.md` |
| API 对照 | `E:\utoo\docs\API对照表.md` |
| 微服务约定 | `E:\utoo\docs\微服务拆分与仓库约定.md` |
| 代码组织 | `E:\utoo\docs\代码组织约定.md` |

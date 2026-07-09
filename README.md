# utoo-pydjango

青岛检测平台 **Python / Django** 后端 monorepo。

| 项 | 值 |
|----|-----|
| GitLab | http://gitlab.wisecom-tech.com/TZJ/utoo-pydjango.git |
| 开发分支 | `dev` |
| 生产分支 | `prod` |

---

## 仓库结构

| 目录 | 端口 | 说明 |
|------|------|------|
| `qd_test_server_django` | **18083** | API **网关**（日常开发主入口） |
| `qd_svc_auth` | 18081 | 认证微服务 |
| `qd_svc_order` | 18082 | 订单微服务 |
| `qd_svc_payment` | 18084 | 支付 / 资产微服务 |
| `qd_svc_invoice` | 18085 | 发票微服务 |
| `qd_svc_entry` | 18086 | 入驻微服务 |
| `qd_svc_wx` | 18087 | 微信微服务 |
| `qd_libs_common` | — | 公共包 `qd_common` |
| `qd_worker` | — | Celery Worker |
| `config/` | — | 共用数据库模板 `shared-database.env.example` |

前端：`qd_test_front_v3`（独立仓库 / 工作区目录），开发时代理 `/api` → 网关 `18083`。

---

## 分支

| 分支 | 用途 |
|------|------|
| `dev` | 日常开发、联调 |
| `prod` | 生产发布 |

```powershell
git clone http://gitlab.wisecom-tech.com/TZJ/utoo-pydjango.git
cd utoo-pydjango
git checkout dev
```

---

## 快速启动（推荐：单体网关）

不配置 `SVC_*_URL` 时，网关内直接跑全部 C 端业务，**不必**先起各微服务。

```powershell
# 1. 共用数据库
copy config\shared-database.env.example config\shared-database.env
# 编辑 config\shared-database.env 中的 DB_*、JWT_SECRET_KEY

# 2. 网关
cd qd_test_server_django
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

网关：http://127.0.0.1:18083  
健康检查：`GET /health`

若工作区在 `E:\utoo`，也可用平台脚本：

```powershell
E:\utoo\dev-start.bat          # 网关 + Vue3
E:\utoo\scripts\start-gateway.ps1
```

---

## 配置

### 数据库（一处）

所有 Django 服务加载顺序：

1. 各服务自己的 `.env`（端口、Redis、微信等）
2. 仓库根目录 `config/shared-database.env`（**DB_\***、**JWT_SECRET_KEY**）
3. 各服务 `.env.local`（本机覆盖，不提交）

`config/shared-database.env` 已加入 `.gitignore`，只提交 `.example`。

### 微服务模式（可选）

在网关 `.env` 中配置上游后，匹配路径会 HTTP 转发：

```env
# SVC_AUTH_URL=http://127.0.0.1:18081
# SVC_ORDER_URL=http://127.0.0.1:18082
# SVC_PAYMENT_URL=http://127.0.0.1:18084
# SVC_INVOICE_URL=http://127.0.0.1:18085
# SVC_ENTRY_URL=http://127.0.0.1:18086
# SVC_WX_URL=http://127.0.0.1:18087
```

禁止微服务之间直接 import 对方业务模块。

---

## 各服务启动

每个 `qd_svc_*` 目录：

```powershell
cd qd_svc_auth   # 或 order / payment / ...
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# 确保上级 config/shared-database.env 已配置
python run.py
```

公共库本地可编辑安装（网关 / 微服务 `settings` 也会把上级 `qd_libs_common` 加入 `sys.path`）：

```powershell
cd qd_libs_common
pip install -e .
```

---

## 勿提交

- `.env` / `.env.local`
- `config/shared-database.env`
- `.venv/`、证书 `*.pem`
- `__pycache__`、`.pytest_cache`

---

## 文档

更完整的平台说明见工作区 `docs/`（若与本仓同级检出）：

- `docs/开发启动.md`
- `docs/进度总览.md`
- `docs/API对照表.md`
- `docs/微服务拆分与仓库约定.md`

网关细节见 `qd_test_server_django/README.md`。

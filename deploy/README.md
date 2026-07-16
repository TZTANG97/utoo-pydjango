# utoo GitLab CI/CD（微服务独立发版）

**本流水线专用于 Utoo 微服务 monorepo，与工厂 EMKU 发版完全分开**：独立 Runner tag（`utoo-windows`）、独立 Variables、独立服务器目录（`/opt/utoo`）。不要使用 `emku-windows` / EMKU 的部署脚本或机器路径。

机制：Windows Shell Runner + SSH → Linux **systemd 裸进程**。  
一次 `deploy_*`：**6 个上游微服务 + 网关 + C 端 / 管理后台静态**（不做蓝绿）。

与本地一致：网关 `.env` 配置 `SVC_*_URL` 后必须启全部上游，否则对应域 **503**。

## 发布流程

1. 推送到 `dev` 或 `prod`
2. GitLab → **CI/CD → Pipelines**（应看到 **4 个 stages**，不是 2 个）
3. 手动 Play **`build_frontend_*`**
4. 手动 Play **`deploy_services_*`**（6 上游）
5. 其后 **`deploy_gateway_*` → `deploy_static_*`** 会自动接着跑

| Stage | Job | 作用 |
|-------|-----|------|
| `build` | `build_frontend_*` | 构建双前端 dist |
| `deploy_services` | `deploy_services_*` | `qd_libs_common` + 6 上游（auth/order/payment/wx/asset/platform） |
| `deploy_gateway` | `deploy_gateway_*` | 网关 `qd-gateway` |
| `deploy_static` | `deploy_static_*` | `/var/www/utoo-c`、`/var/www/utoo-admin` |

`deploy_services` 内顺序：

1. `qd_svc_auth` `:18081`
2. `qd_svc_order` `:18082`
3. `qd_svc_payment` `:18084`
4. `qd_svc_wx` `:18087`
5. `qd_svc_admin_asset` `:18090`
6. `qd_svc_admin_platform` `:18091`

若 Pipeline 显示 **stuck**：没有 tag=`utoo-windows` 的 Runner，先注册 Runner，不是 stages 少了。

不发：`qd_svc_entry` / `qd_svc_invoice`（已废弃）。`qd_worker` 未进流水线（支付异步队列需要时再加）。

## 服务器目录约定

```text
/opt/utoo/
  qd_libs_common/
  config/shared-database.env     # DB/JWT，只放服务器，CI 不覆盖
  qd_svc_auth/                   # + .venv + .env
  qd_svc_order/
  qd_svc_payment/
  qd_svc_wx/
  qd_svc_admin_asset/
  qd_svc_admin_platform/
  qd_test_server_django/         # 网关 .env 须含 SVC_*_URL

/var/www/utoo-c/                 # C 端 dist
/var/www/utoo-admin/             # 管理后台 dist
```

systemd 示例：`deploy/systemd/qd-*.service.example`。

Nginx 对外只反代网关与静态：

- API → `127.0.0.1:18083`
- C 端静态 → `/var/www/utoo-c`
- 管理后台静态 → `/var/www/utoo-admin`

上游仅本机访问，不必对公网开放 18081–18091。

## 网关 SVC_*（服务器必配）

`/opt/utoo/qd_test_server_django/.env` 示例（与本地微服务模式一致；生产请关 `DEBUG_RELOAD`）：

```env
SVC_AUTH_URL=http://127.0.0.1:18081
SVC_ORDER_URL=http://127.0.0.1:18082
SVC_PAYMENT_URL=http://127.0.0.1:18084
SVC_ADMIN_ASSET_URL=http://127.0.0.1:18090
SVC_ADMIN_PLATFORM_URL=http://127.0.0.1:18091
SVC_INVOICE_URL=http://127.0.0.1:18091
SVC_ENTRY_URL=http://127.0.0.1:18091
SVC_WX_URL=http://127.0.0.1:18087
DEBUG_RELOAD=false
```

各 `qd_svc_*` 也需自有 `.env`（端口等）+ 共用 `config/shared-database.env`。CI **不会**覆盖这些文件。

## GitLab / Runner 配置（独立于 EMKU）

### 1. 为本项目注册 Windows Runner

1. 准备一台 Windows 机器（建议与 EMKU Runner **分开**），安装 [GitLab Runner](https://docs.gitlab.com/runner/install/windows.html)
2. 使用 **本项目**（`web/utoo-pydjango`）的 registration token 注册
3. Executor 选 **`shell`**
4. Tag 只打：**`utoo-windows`**（不要打 `emku-windows`）
5. 机器需已装：PowerShell、OpenSSH Client（`ssh`/`scp`）、Node.js（前端构建）、能访问目标 Linux 服务器

Settings → CI/CD → Runners：确认本项目 Runner 为绿色且带 `utoo-windows`。

### 2. CI 变量（本项目自己的）

Settings → CI/CD → Variables（勿复用 EMKU 项目变量；至少先配 **dev**）：

| 变量 | 说明 |
|------|------|
| `DEPLOY_USER` | SSH 用户（如 `deploy`） |
| `DEPLOY_HOST` | **Utoo** 服务器 IP/域名 |
| `SSH_PRIVATE_KEY` | 对应私钥（脚本会规范化换行） |

可选：`DEPLOY_USER_DEV`、`DEPLOY_HOST_PROD` 等带后缀变量，脚本会按分支优先读取。

### 3. 远端 sudo

远端用户需对 `/opt/utoo`、静态目录及下列 unit **免密 sudo**：

```text
qd-auth qd-order qd-payment qd-wx qd-admin-asset qd-admin-platform qd-gateway
```

示例 drop-in（路径按你们规范调整，**不要**直接拷贝 EMKU 的 sudoers 文件名混用）：

```text
# /etc/sudoers.d/utoo-gitlab-deploy
deploy ALL=(root) NOPASSWD: /bin/bash, /usr/bin/bash, /bin/systemctl, /usr/bin/systemctl, /bin/mkdir, /bin/rm, /bin/tar, /usr/bin/tar, /bin/chown, /usr/bin/find, /usr/bin/xargs, /bin/chmod
```

### 4. known_hosts

**不要**在 Variables 里配多行 `SSH_KNOWN_HOSTS`；脚本会自动 `ssh-keyscan`。

### 5. 关闭 Auto DevOps

Settings → CI/CD → Auto DevOps → **Disable**，避免再跑出带 Auto DevOps 标签的失败流水线。

本机调试变量文件：

```powershell
copy deploy\ci-local\utoo-deploy-dev.env.ps1.example deploy\ci-local\utoo-deploy-dev.env.ps1
```

## 服务器一次性准备

```bash
sudo mkdir -p /opt/utoo/config /var/www/utoo-c /var/www/utoo-admin
sudo chown -R deploy:deploy /opt/utoo /var/www/utoo-c /var/www/utoo-admin

# 放置密钥（勿提交仓库）
# /opt/utoo/config/shared-database.env
# /opt/utoo/qd_test_server_django/.env   # 含 SVC_*
# /opt/utoo/qd_svc_*/.env

cd /path/to/repo/deploy/systemd
for u in qd-auth qd-order qd-payment qd-wx qd-admin-asset qd-admin-platform qd-gateway; do
  sudo cp "${u}.service.example" "/etc/systemd/system/${u}.service"
done
sudo systemctl daemon-reload
sudo systemctl enable qd-auth qd-order qd-payment qd-wx qd-admin-asset qd-admin-platform qd-gateway
```

首次可先手工放齐代码与 `.env`，再：

```bash
curl -sf http://127.0.0.1:18081/health && echo auth_ok
curl -sf http://127.0.0.1:18082/health && echo order_ok
curl -sf http://127.0.0.1:18084/health && echo payment_ok
curl -sf http://127.0.0.1:18087/health && echo wx_ok
curl -sf http://127.0.0.1:18090/health && echo asset_ok
curl -sf http://127.0.0.1:18091/health && echo platform_ok
curl -sf http://127.0.0.1:18083/health && echo gateway_ok
```

## 回滚

无蓝绿：对旧 commit 再跑一次 `deploy_*`，或从备份目录恢复对应服务后 `systemctl restart`。

# utoo GitLab CI/CD（微服务 + 红绿双实例）

**本流水线专用于 Utoo 微服务 monorepo，与工厂 EMKU 发版完全分开**：独立 Runner tag（`utoo-windows`）、独立 Variables、独立服务器目录（`/opt/utoo-blue` / `/opt/utoo-green`）。**禁止**使用 `emku-windows`、`/opt/emku-*`、`emku-switch-*`、`emku_upstream_*` 或 8021/8023/8024/8027。

机制：Windows Shell Runner + SSH → Linux **systemd 裸进程** + **Nginx upstream 独立切流**。每个上游服务只发布并切换自己的蓝绿实例；gateway 和前端也是独立发布入口。

与本地一致：网关 `.env` 配置 `SVC_*_URL` 后，对应 upstream 不可用时该域 API 返回 **503**。

## 红绿架构

```text
公网 Nginx（uat.utoodev.laide.tech 等）
  /api/  → utoo_upstream_server.conf → 当前 gateway :18083 或 :18183
  /      → /var/www/utoo-web

内部 Nginx（仅 127.0.0.1）
  :19081 → utoo_upstream_identity.conf      → identity :18081 或 :18181
  :19082 → utoo_upstream_order.conf          → order :18082 或 :18182
  :19084 → utoo_upstream_payment.conf        → payment :18084 或 :18184
  :19090 → utoo_upstream_admin_asset.conf    → asset :18090 或 :18190
  :19091 → utoo_upstream_admin_platform.conf → platform :18091 或 :18191

/opt/utoo-blue/     180xx 物理实例
/opt/utoo-green/    181xx 物理实例
/opt/utoo/config/shared-database.env   # 双槽共用密钥（CI 不覆盖；各槽 config/ 下可 symlink）
```

| 槽 | 根目录 | 网关 | identity | order | payment | asset | platform | systemd 后缀 |
|----|--------|------|----------|-------|---------|-------|----------|--------------|
| blue | `/opt/utoo-blue` | **18083** | **18081** | 18082 | 18084 | 18090 | 18091 | `-blue` |
| green | `/opt/utoo-green` | **18183** | **18181** | 18182 | 18184 | 18190 | 18191 | `-green` |

- 两个 gateway `.env` 的 `SVC_*_URL` 均指向稳定内部端口 `19081/82/84/90/91`。
- 静态单目录 `/var/www/utoo-web` 独立发布，无蓝绿切流。
- gateway upstream：`/usr/local/nginx/conf/utoo_upstream_server.conf`（一行 `server 127.0.0.1:PORT;`）。
- 单服务 upstream：`/usr/local/nginx/conf/utoo_upstream_{service}.conf`。
- 切流脚本：`utoo-switch-active.sh <gateway_port>` 或 `utoo-switch-service.sh <service> <port>`。

样例见 [`deploy/nginx/`](nginx/)、[`deploy/systemd/`](systemd/)。从单实例迁 139：见 [`MIGRATE-BLUE-GREEN-139.md`](MIGRATE-BLUE-GREEN-139.md)。

## 发布流程

1. 推送到 `dev` 或 `prod`
2. GitLab → **CI/CD → Pipelines**（应看到一个 `deploy` stage 和 **7 个手动按钮**）
3. 按改动范围选择对应按钮；所有按钮互不自动触发。

| Job | 发布内容 | 切换方式 |
|-----|----------|----------|
| `deploy_order_*` | `qd_svc_order` | :18082 ↔ :18182 |
| `deploy_identity_*` | `qd_svc_identity`（密码登录中台） | :18081 ↔ :18181 |
| `deploy_payment_*` | `qd_svc_payment`，含原微信代理 | :18084 ↔ :18184 |
| `deploy_admin_asset_*` | `qd_svc_admin_asset` | :18090 ↔ :18190 |
| `deploy_admin_platform_*` | `qd_svc_admin_platform`，含 entry/invoice | :18091 ↔ :18191 |
| `deploy_gateway_*` | `qd_test_server_django` | :18083 ↔ :18183 |
| `deploy_frontend_*` | 构建并发布统一 `qd_web_front` | 更新 `/var/www/utoo-web` |

若 Pipeline 显示 **stuck**：没有 tag=`utoo-windows` 的 Runner，先注册 Runner，不是 stages 少了。

不发：`qd_svc_wx` / `qd_svc_entry` / `qd_svc_invoice`（已废弃）。旧 `qd_svc_auth` **已从仓库删除**，登录发 **`deploy_identity_*`**（端口 18081）。`qd_worker` 未进流水线。

## 网关 SVC_*（每槽各自 `.env`）

**blue 和 green 均使用相同的服务地址**（gateway 自身 `SERVER_PORT_HTTP` 保持各自 18083 / 18183）：

```env
# 勿设 SVC_AUTH_URL
# 登录切流：配了才打身份中台；空则网关本地登录（回滚）
SVC_IDENTITY_URL=http://127.0.0.1:19081
SVC_ORDER_URL=http://127.0.0.1:19082
SVC_PAYMENT_URL=http://127.0.0.1:19084
SVC_WX_URL=http://127.0.0.1:19084
SVC_ADMIN_ASSET_URL=http://127.0.0.1:19090
SVC_ADMIN_PLATFORM_URL=http://127.0.0.1:19091
SVC_INVOICE_URL=http://127.0.0.1:19091
SVC_ENTRY_URL=http://127.0.0.1:19091
DEBUG_RELOAD=false
SERVER_PORT_HTTP=18083
```

各上游 `.env` 的 `SERVER_PORT_HTTP` 与上表一致。CI **不会**覆盖 `.env` / `shared-database.env`。  
身份中台 JWT 用共享文件里的 `JWT_SECRET_KEY`，必须与网关同一把。

## 身份中台首次上线（登录切流）

先做 **UAT（`dev` / 139）**，不要先动 `prod`。前端不用发。

1. 把含 `deploy/` 的代码放到服务器（或从已有 `/opt/utoo-blue` 更新 `deploy/`）。
2. 一次性安装 systemd + Nginx `:19081`：

```bash
# 在目标机；REPO 指向含 deploy/ 的树
sudo REPO=/opt/utoo-blue bash /opt/utoo-blue/deploy/identity-first-install.sh.example
```

3. 推送到 `dev` 后，GitLab **只点** `deploy_identity_dev`。此时 **不要** 写 `SVC_IDENTITY_URL`。
4. 探活：`curl -fsS http://127.0.0.1:18081/health` 与 `curl -fsS http://127.0.0.1:19081/health`
5. 两槽网关 `.env` 加上 `SVC_IDENTITY_URL=http://127.0.0.1:19081`，再点 `deploy_gateway_dev`（或重启当前网关）。
6. 测管理端 / PC / 小程序密码登录。短信与微信一键仍走网关。

回滚登录：清空 `SVC_IDENTITY_URL` 并重启当前网关。中台切槽：`sudo /usr/local/sbin/utoo-switch-service.sh identity 18081`。

日常：只改登录中台 → 只点 `deploy_identity_*`；只改网关转发 → 只点 `deploy_gateway_*`；两边都改 → **先 identity 探活，再 gateway**。identity 进流水线前不要用全发当登录切流；补齐后 `deploy_all_*` 会带上 identity。

## GitLab / Runner 配置（独立于 EMKU）

### 1. 为本项目注册 Windows Runner

1. 准备一台 Windows 机器（建议与 EMKU Runner **分开**）
2. 使用 **本项目** registration token；Executor **`shell`**
3. Tag 只打：**`utoo-windows`**（不要打 `emku-windows`）
4. 需已装：PowerShell、OpenSSH Client、Node.js、能访问目标 Linux

### 2. CI 变量

| 变量 | 说明 |
|------|------|
| `DEPLOY_USER` / `DEPLOY_HOST` / `SSH_PRIVATE_KEY` | SSH（可 `_DEV` / `_PROD` 后缀） |
| `UTOO_UPSTREAM_CONF` | 可选，默认 `/usr/local/nginx/conf/utoo_upstream_server.conf` |
| `UTOO_SWITCH_SCRIPT` | 可选，默认 `/usr/local/sbin/utoo-switch-active.sh` |
| `UTOO_SERVICE_UPSTREAM_CONF_DIR` | 可选，默认 `/usr/local/nginx/conf` |
| `UTOO_SERVICE_SWITCH_SCRIPT` | 可选，默认 `/usr/local/sbin/utoo-switch-service.sh` |
| `UTOO_STATIC_WEB` | 可选，默认 `/var/www/utoo-web` |
| `UTOO_SHARED_CONFIG` | 可选，默认 `/opt/utoo/config`（共享密钥目录） |

### 3. 远端 sudo

```text
# /etc/sudoers.d/utoo-gitlab-deploy
deploy ALL=(root) NOPASSWD: /bin/bash, /usr/bin/bash, /bin/systemctl, /usr/bin/systemctl, /bin/mkdir, /bin/rm, /bin/tar, /usr/bin/tar, /bin/chown, /usr/bin/find, /usr/bin/xargs, /bin/chmod, /usr/local/sbin/utoo-switch-active.sh, /usr/local/sbin/utoo-switch-service.sh, /usr/local/nginx/sbin/nginx
```

单元名示例：`qd-order-blue` `qd-order-green` `qd-gateway-blue` `qd-gateway-green` 等（见 systemd 样例）。

### 4. known_hosts / Auto DevOps

脚本自动 `ssh-keyscan`。关闭 Auto DevOps，避免干扰。

## 服务器一次性准备

见 [`MIGRATE-BLUE-GREEN-139.md`](MIGRATE-BLUE-GREEN-139.md)（从旧 `/opt/utoo` 单实例迁蓝绿）或新机：

```bash
sudo mkdir -p /opt/utoo/config /opt/utoo-blue /opt/utoo-green /var/www/utoo-web
sudo chown -R deploy:deploy /opt/utoo /opt/utoo-blue /opt/utoo-green /var/www/utoo-web
# 放置 shared-database.env；各槽 config/ 下 symlink
# 安装 deploy/systemd/*-{blue,green}.service.example
# 安装 gateway upstream、5 个服务 upstream、utoo-internal-upstreams.conf 与两个切流脚本
```

## 回滚

- 单服务：`sudo /usr/local/sbin/utoo-switch-service.sh order 18082`（identity 用 `identity 18081`）。
- gateway：`sudo /usr/local/sbin/utoo-switch-active.sh 18083`（或 `18183`）切回上一 gateway。
- 前端：重新执行上一 commit 的 `deploy_frontend_*`。

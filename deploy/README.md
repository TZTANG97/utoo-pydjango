# utoo GitLab CI/CD（微服务 + 红绿双实例）

**本流水线专用于 Utoo 微服务 monorepo，与工厂 EMKU 发版完全分开**：独立 Runner tag（`utoo-windows`）、独立 Variables、独立服务器目录（`/opt/utoo-blue` / `/opt/utoo-green`）。**禁止**使用 `emku-windows`、`/opt/emku-*`、`emku-switch-*`、`emku_upstream_*` 或 8021/8023/8024/8027。

机制：Windows Shell Runner + SSH → Linux **systemd 裸进程** + **Nginx upstream 切网关端口**（对齐 EMKU「空闲槽发版 → health → 切流 → 再发静态」）。

与本地一致：网关 `.env` 配置 `SVC_*_URL` 后必须启全部本槽上游，否则对应域 **503**。

## 红绿架构

```text
Nginx（uat.utoodev.laide.tech 等）
  /api/  → include utoo_upstream_server.conf  → 当前 active 网关端口
  /      → /var/www/utoo-web

/opt/utoo-blue/     网关 :18083 + 上游 18082/84/90/91
/opt/utoo-green/    网关 :18183 + 上游 18182/84/90/91
/opt/utoo/config/shared-database.env   # 双槽共用密钥（CI 不覆盖；各槽 config/ 下可 symlink）
```

| 槽 | 根目录 | 网关 | order | payment | asset | platform | systemd 后缀 |
|----|--------|------|-------|---------|-------|----------|--------------|
| blue | `/opt/utoo-blue` | **18083** | 18082 | 18084 | 18090 | 18091 | `-blue` |
| green | `/opt/utoo-green` | **18183** | 18182 | 18184 | 18190 | 18191 | `-green` |

- 每槽网关 `.env` 的 `SVC_*_URL` **只指向本槽上游**。
- 静态单目录 `/var/www/utoo-web`：**切流成功后再覆盖**。
- Upstream 小文件：`/usr/local/nginx/conf/utoo_upstream_server.conf`（一行 `server 127.0.0.1:PORT;`）
- 切流脚本：`/usr/local/sbin/utoo-switch-active.sh <gateway_port>`

样例见 [`deploy/nginx/`](nginx/)、[`deploy/systemd/`](systemd/)。从单实例迁 139：见 [`MIGRATE-BLUE-GREEN-139.md`](MIGRATE-BLUE-GREEN-139.md)。

## 发布流程

1. 推送到 `dev` 或 `prod`
2. GitLab → **CI/CD → Pipelines**（应看到 **4 个 stages**）
3. 手动 Play **`build_frontend_*`**
4. 手动 Play **`deploy_services_*`**（打到**空闲槽**：libs + 4 上游）
5. 其后 **`deploy_gateway_*`**（空闲槽网关 → health → **切 Nginx**）→ **`deploy_static_*`**（解压前端）会自动接着跑

| Stage | Job | 作用 |
|-------|-----|------|
| `build` | `build_frontend_*` | 构建统一前端 `qd_web_front` dist |
| `deploy_services` | `deploy_services_*` | 空闲槽：`qd_libs_common` + 4 上游 |
| `deploy_gateway` | `deploy_gateway_*` | 空闲槽网关 + health + `utoo-switch-active.sh` |
| `deploy_static` | `deploy_static_*` | `/var/www/utoo-web`（切流后） |

`deploy_services` 内顺序（空闲槽端口）：

1. `qd_svc_order`
2. `qd_svc_payment`（含原 `/api/wx/*`）
3. `qd_svc_admin_asset`
4. `qd_svc_admin_platform`

若 Pipeline 显示 **stuck**：没有 tag=`utoo-windows` 的 Runner，先注册 Runner，不是 stages 少了。

不发：`qd_svc_auth` / `qd_svc_wx` / `qd_svc_entry` / `qd_svc_invoice`（已废弃）。`qd_worker` 未进流水线。

## 网关 SVC_*（每槽各自 `.env`）

**蓝** `/opt/utoo-blue/qd_test_server_django/.env`：

```env
# 勿设 SVC_AUTH_URL
SVC_ORDER_URL=http://127.0.0.1:18082
SVC_PAYMENT_URL=http://127.0.0.1:18084
SVC_WX_URL=http://127.0.0.1:18084
SVC_ADMIN_ASSET_URL=http://127.0.0.1:18090
SVC_ADMIN_PLATFORM_URL=http://127.0.0.1:18091
SVC_INVOICE_URL=http://127.0.0.1:18091
SVC_ENTRY_URL=http://127.0.0.1:18091
DEBUG_RELOAD=false
SERVER_PORT_HTTP=18083
```

**绿** 将端口改为 `18182` / `18184` / `18190` / `18191` / 网关 `18183`。

各上游 `.env` 的 `SERVER_PORT_HTTP` 与上表一致。CI **不会**覆盖 `.env` / `shared-database.env`。

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
| `UTOO_STATIC_WEB` | 可选，默认 `/var/www/utoo-web` |
| `UTOO_SHARED_CONFIG` | 可选，默认 `/opt/utoo/config`（共享密钥目录） |

### 3. 远端 sudo

```text
# /etc/sudoers.d/utoo-gitlab-deploy
deploy ALL=(root) NOPASSWD: /bin/bash, /usr/bin/bash, /bin/systemctl, /usr/bin/systemctl, /bin/mkdir, /bin/rm, /bin/tar, /usr/bin/tar, /bin/chown, /usr/bin/find, /usr/bin/xargs, /bin/chmod, /usr/local/sbin/utoo-switch-active.sh, /usr/local/nginx/sbin/nginx
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
# 安装 deploy/nginx/utoo_upstream_server.conf.example + utoo-switch-active.sh.example
```

## 回滚

- 再跑一版旧 commit 的 Pipeline（打到当前空闲槽并切流），或
- 手动：`sudo /usr/local/sbin/utoo-switch-active.sh 18083`（或 `18183`）切回上一槽网关端口

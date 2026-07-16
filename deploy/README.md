# utoo GitLab CI/CD（微服务模式）

对齐 `factoryproductsystem2`：**Windows Shell Runner + SSH → Linux systemd 裸进程**。  
一次 `deploy_*` 发布：**6 个上游微服务 + 网关 + C 端 / 管理后台静态**（不做蓝绿）。

与本地一致：网关 `.env` 配置 `SVC_*_URL` 后必须启全部上游，否则对应域 **503**。

## 发布流程

1. 推送到 `dev` 或 `prod`
2. GitLab → **CI/CD → Pipelines**
3. 手动点 **`build_frontend_*`** → 成功后再点 **`deploy_*`**

| Job | 作用 |
|-----|------|
| `build_frontend_dev/prod` | `npm ci && npm run build`（`qd_test_front_v3` + `qd_admin_front`） |
| `deploy_dev/prod` | 同步 `qd_libs_common` → 6 上游 + 网关（pip / check / restart / `/health`）→ 静态目录 |

部署顺序（脚本内写死）：

1. `qd_svc_auth` → `qd-auth` `:18081`
2. `qd_svc_order` → `qd-order` `:18082`
3. `qd_svc_payment` → `qd-payment` `:18084`
4. `qd_svc_wx` → `qd-wx` `:18087`
5. `qd_svc_admin_asset` → `qd-admin-asset` `:18090`
6. `qd_svc_admin_platform` → `qd-admin-platform` `:18091`
7. `qd_test_server_django` → `qd-gateway` `:18083`
8. 静态：`/var/www/utoo-c`、`/var/www/utoo-admin`

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

## GitLab / Runner 配置

1. Windows Runner tag 已设为 **`emku-windows`**（与工厂 EMKU 共用）；Settings → CI/CD → Runners 确认该 tag 为绿色可用
2. 项目 **Settings → CI/CD → Variables**（建议按环境拆 `_DEV` / `_PROD`）：

| 变量 | 说明 |
|------|------|
| `DEPLOY_USER` | SSH 用户（如 `deploy`） |
| `DEPLOY_HOST` | 服务器 IP/域名 |
| `SSH_PRIVATE_KEY` | 私钥（脚本会规范化换行） |

可选：`DEPLOY_USER_DEV`、`DEPLOY_HOST_PROD` 等带后缀变量，脚本会按分支优先读取。

3. 远端用户需对 `/opt/utoo`、静态目录及下列 unit **免密 sudo**（可参考 EMKU 的 `sudoers.d`）：

```text
qd-auth qd-order qd-payment qd-wx qd-admin-asset qd-admin-platform qd-gateway
```

4. **不要**在 Variables 里配多行 `SSH_KNOWN_HOSTS`；脚本会自动 `ssh-keyscan`

本机调试：

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
后续若要对齐 EMKU，可再加 Nginx upstream 切换。

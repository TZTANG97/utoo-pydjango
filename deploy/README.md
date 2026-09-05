# utoo GitLab CI/CD（P5 发版分家 · UTOO 业务）

**本流水线只发 UTOO 产品**，与大平台 / EMKU 分开：独立 Runner tag（`utoo-windows`）、独立 Variables。

| | UTOO（本仓） | 大平台 | EMKU |
|--|--------------|--------|------|
| Runner | **`utoo-windows`**（须 `shell=powershell`） | `qd-mall-windows` | `emku-windows` |
| 发什么 | `platform/utoo_gateway`、`services/utoo_biz`、`utoo-web-front` | 中台 + 青岛 + admin-web | 工厂 |
| 运行槽 | 现网仍写 **`/opt/qd-mall-{blue\|green}`** 内 UTOO 子树 | 同槽发中台/青岛 | `/opt/emku-*` |
| 静态 | `/var/www/utoo-web` | `/var/www/qd-admin-web` | — |

## P4 / P5 强制

- **禁止**从本仓发中台五件套（`identity` / `order` / `payment` / `admin_asset` / `admin_platform`）— job `when: never`。
- 中台唯一发版源：大平台仓 `mall_qingdao_pydjango/platform/*`。
- **禁止**发青岛 `gateway` / `mall` / `admin-web`。
- 旧目录 `qd_test_server_django` / `qd_web_front` 已标 DEPRECATED，**不是**发版源。

## 活跃 Job

| Job | 代码 | 目标 |
|-----|------|------|
| `deploy_utoo_biz_*` | `services/utoo_biz` | `qd-utoo-biz-*` @ 18093/18193 |
| `deploy_utoo_gateway_*` | `platform/utoo_gateway` | `qd-gateway-*` @ 18083/18183 |
| `deploy_utoo_frontend_*` | `utoo-web-front` | `/var/www/utoo-web` |
| `deploy_all_*` | 上三者顺序 | biz → gateway → frontend |
| `deploy_gateway_*` / `deploy_frontend_*` | 兼容旧名 | 分别指向 gateway / frontend 上表 |

入口：`deploy/utoo-windows/ci-entry-*.cmd` → `powershell -File`。  
Runner 若被改成 bash：管理员运行 `C:\GitLab-Runner\fix-utoo-runner-admin.cmd`。

## 改哪仓

| 改动 | 仓 | 点谁 |
|------|-----|------|
| 愉兔菜单/me、官网、biz | **本仓** | `deploy_utoo_*` |
| 登录原子、实验单、库存、青岛经营 | **大平台仓** | `deploy_identity|order|asset|mall|...` |

本地 env：优先 `C:\ProgramData\qd-mall-deploy-{dev|prod}.env.ps1`（同机槽），否则 `utoo-deploy-*.env.ps1`。

# qd_svc_identity · 身份中台

与实验订单中台 `qd_svc_order` **并列**。

| 环境 | 进程端口 | 网关打的地址 |
|------|----------|--------------|
| 本机开发 | **18110** | `SVC_IDENTITY_URL=http://127.0.0.1:18110` |
| UTOO 生产蓝/绿 | **18081 / 18181** | `SVC_IDENTITY_URL=http://127.0.0.1:19081` |

登录（员工 / 会员密码）由本服务签发 JWT；青岛部门/角色/用户/菜单写、改密、数据范围也在本服务。UTOO 发版见仓库 `deploy/README.md`「身份中台首次上线」。

## 启动

```powershell
cd E:\utoo\utoo-pydjango\qd_svc_identity
.\.venv\Scripts\python.exe run.py
```

或仓库根：`.\scripts\start-identity.ps1`（`start-ms-dev.ps1` 已包含）。

健康检查：http://127.0.0.1:18110/health

## 切流

| 端 | 变量 | 效果 |
|----|------|------|
| 青岛 gateway | `IDENTITY_MID_SERVICE_URL=http://127.0.0.1:18110`（默认已开） | login/me/改密/数据范围/menus + 部门/角色/用户/菜单写 → 中台 |
| UTOO 本机 | `SVC_IDENTITY_URL=http://127.0.0.1:18110` | 员工/会员/小程序密码登录 → 中台 |
| UTOO 生产 | `SVC_IDENTITY_URL=http://127.0.0.1:19081` | 同上，经 Nginx 稳定口 |

JWT：青岛壳用 `MALL_JWT_SECRET` / `MALL_JWT_ISSUER=qd-mall-identity`；UTOO 用 `JWT_SECRET_KEY`。

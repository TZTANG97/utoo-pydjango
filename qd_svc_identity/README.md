# qd_svc_identity · 身份中台

与实验订单中台 `qd_svc_order` **并列**。默认端口 **18110**（避开青岛 rental :18088）。

| 项 | 值 |
|----|-----|
| 端口 | **18110** |
| 前缀 | `/api/v1/identity/` |
| 库 | `qd_pt_new` |
| JWT | `JWT_SECRET_KEY`；青岛壳另用 `MALL_JWT_SECRET` / `MALL_JWT_ISSUER` |

## 启动

```powershell
cd E:\utoo\utoo-pydjango\qd_svc_identity
python run.py
```

## 渠道

| X-Channel | 登录 | 菜单 |
|-----------|------|------|
| `mall_qd` | `sy_users`，返回青岛 `access_token` 形态 | `type=1` + `pt_type` 含 `1` |
| `admin` | `sy_users`，返回 UTOO `token/refreshToken` | `type=2` + `%2%` |
| `pc` / `wx` | `exp_user` 会员 | 空 |

## 切流

- 青岛 gateway：`IDENTITY_MID_SERVICE_URL=http://127.0.0.1:18110`（login/me/menus/permissions → 中台；组织写仍本地 :18081）
- UTOO 网关：`SVC_IDENTITY_URL=http://127.0.0.1:18110`（员工 login/main + 会员 login/me/refresh）

契约：`mall_qingdao_pydjango/docs/rewrite/identity-mid-platform-清单.md`

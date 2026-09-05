# utoo-web-front · 愉兔统一前端

单 SPA：**C 端 + 管理后台**（`#/admin`）。

| 入口 | Hash 路径 |
|------|-----------|
| C 端 | `#/home`、`#/b/...`、`#/login` |
| 管理后台 | `#/admin/login`、`#/admin/dashboard` |

本仓为**活跃发版**目录；旧 `utoo-pydjango/qd_web_front` 仅对照。

---

## 本地开发

先启动 **utoo_gateway :18083**：

```powershell
# 仓库根
.\scripts\start-dev.ps1
```

再启前端：

```powershell
cd utoo-web-front
npm ci   # 或 npm install
npm run dev
# 常见 http://127.0.0.1:9530 或 9540（以 vite.config 为准）
```

环境：`VITE_API_TARGET=http://127.0.0.1:18083`

---

## 生产构建

```powershell
npm run build
# dist/ → Nginx 单 root（如 /var/www/utoo-web）
```

---

## 鉴权

| 端 | Cookie | 请求头 |
|----|--------|--------|
| C 端 | `token` | `X-Channel: pc` |
| 后台 | `admin_token` | `X-Channel: admin` |

登录/me/菜单编排由 **utoo_gateway** 完成（方案 B）；identity 只提供基础凭证与用户原子字段。

---

## 分支

| 分支 | 说明 |
|------|------|
| `dev` | 日常开发、联调 |
| `prod` | 生产静态发版 |

---

## 相关

- [../platform/utoo_gateway/README.md](../platform/utoo_gateway/README.md)
- [../services/utoo_biz/README.md](../services/utoo_biz/README.md)
- [../docs/中台基础能力与各端业务边界-方案B.md](../docs/中台基础能力与各端业务边界-方案B.md)

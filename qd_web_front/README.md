# qd_web_front

统一前端（单 SPA）：**C 端 + 管理后台**。

| 入口 | Hash 路径 |
|------|-----------|
| C 端 | `#/home`、`#/b/...`、`#/login` |
| 管理后台 | `#/admin/login`、`#/admin/dashboard` |

本地开发：

```bash
npm ci
npm run dev
# http://127.0.0.1:9530
```

生产构建：

```bash
npm run build
# 产物 dist/ → 部署到 Nginx 单 root（如 /var/www/utoo-web）
```

鉴权隔离：

- C 端：cookie `token`，请求头 `X-Channel: pc`
- 后台：cookie `admin_token`，请求头 `X-Channel: admin`

旧目录 `qd_test_front_v3`、`qd_admin_front` 仅作对照，**请以本工程为准发版**。

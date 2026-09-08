# SolarAutoTest 台架操作手册（静态站）

内网公开的静态操作文档，挂在 UTOO 前端静态资源下。

## 路径

- 仓库：`utoo-pydjango`
- 目录：`utoo-web-front/public/autotest-docs/`
- 访问（前端发布后）：`https://uat.utoodev.laide.tech/autotest-docs/`

## 本地预览

```bash
cd utoo-web-front/public/autotest-docs
python -m http.server 8765
```

浏览器打开：`http://127.0.0.1:8765/`

（不要用 `file://` 直接打开，否则 `fetch` 加载 `nav.json` / 子页可能失败。）

## 结构

| 文件 | 作用 |
|------|------|
| `index.html` + `app.js` + `styles.css` | 壳：左侧目录 + 右侧内容 |
| `nav.json` | 菜单（连接方式 / 试验） |
| `pages/*.html` | 各章节正文碎片 |
| `media/` | 截图 |

## 新增试验页

1. 复制 `pages/test-overload.html` 为 `pages/test-xxx.html`，替换文案与截图。
2. 截图放入 `media/`。
3. 在 `nav.json` 的 `tests.children` 增加一项，`"ready": true`。

## Nginx 建议（避免被 SPA 回退成前端首页）

若站点根是 Vue SPA（`try_files ... /index.html`），请为文档目录单独加一段：

```nginx
location /autotest-docs/ {
    try_files $uri $uri/ /autotest-docs/index.html;
}
```

把静态文件随 `utoo-web` 发布到 `/var/www/utoo-web/autotest-docs/`（或与现网 root 一致即可）。

## 内网谁能访问（不是文档站单独开关）

手册**没有单独的「内网白名单」配置页**。能打开公司 UTOO 前端域名的人，就能打开 `/autotest-docs/`。

| 环节 | 说明 |
|------|------|
| 内容进仓 | `utoo-web-front/public/autotest-docs/` |
| 随发版 | 前端构建把 `public/` 原样打进静态资源 |
| 访问地址 | `https://uat.utoodev.laide.tech/autotest-docs/` |
| 谁能进 | 与 UTOO 站点本身一致（公司内网 / VPN / 现有登录与网关策略） |
| 可选 nginx | 仅当 SPA `try_files` 误吞路径时加一次 `location /autotest-docs/`（见上） |

日常改文档：改文件 → 合并 → 发 UTOO 前端即可，不必每次配 nginx。

## 为何放 public 而不是单独 docs 仓

- 仍是纯静态页，不绑 Vue 路由。
- 随现有前端构建/发布进内网域名，少开一套站点。
- 内容用 HTML 碎片 + `nav.json`，加试验只需改两个地方。

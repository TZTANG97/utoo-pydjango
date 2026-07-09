# qd_test_front_v3

**愉兔检测** 客户 PC 端 — 在 `qd_test_front`（Vue2）基础上升级技术栈，**页面与交互与旧版一致**，不是 IoT 项目 UI。

## 技术栈升级（非业务重写）

| 项 | Vue2 旧版 | Vue3 本工程 |
|----|-----------|-------------|
| 构建 | vue-cli / webpack | **Vite 6** |
| 框架 | Vue 2.6 | **Vue 3.5** |
| UI | Element UI | **Element Plus** |
| 路由 | vue-router 3 | **vue-router 4**（hash，与旧版一致） |
| 状态 | Vuex 3 | **Vuex 4**（模块结构沿用，便于迁移） |

源码自 `qd_test_front/src` 迁移：`views`、`layout`、`api`、`static`、样式等。

## 开发

```bash
cd E:\utoo\qd_test_front_v3
npm install
npm run dev
```

- 地址：http://localhost:9530
- 对接 Java：`.env.development` 中 `VITE_API_TARGET` 指向 UAT console（默认）
- 对接 Python：`VITE_API_TARGET=http://127.0.0.1:18083`

## 文档

- `E:\utoo\qd_test_server\docs\Vue3技术栈.md`
- `E:\utoo\qd_test_server\docs\重构计划.md`

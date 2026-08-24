# UTOO 检测平台 — Agent 上下文

## 工作区

打开 **`E:\utoo\utoo.code-workspace`** 或 **`E:\utoo\qd-platform.code-workspace`**（多根），不要只打开 Java 单文件夹。

## 仓库角色

| 目录 | 角色 |
|------|------|
| `qd_test_server` | Java，**只读对照** |
| `qd_test_server_django` | API **网关**，端口 **18083** |
| `qd_svc_identity` | 身份中台（本机 **18110** / 生产 **:19081**） |
| `qd_svc_*` | 微服务：identity / order / payment / admin_asset / admin_platform |
| `qd_libs_common` | 公共 Python 包 |
| `qd_worker` | Celery |
| `qd_test_server_py` | FastAPI，**冻结** |
| `qd_web_front` | Vue3 主前端（旧 `qd_test_front_v3` 已并入） |
| `E:\mall_qingdao_pydjango` | 青岛网关 :18080 + mall :18092 + **platform/** 中台 + utoo_gateway + utoo_biz + admin-web/utoo-web-front；Java `mall_qingdao` 只读 |

## 文档（权威）

**`E:\utoo\docs\`** — **第一入口**：**`大平台与UTOO-方向与交互.md`**；**方案 B**：**`中台基础能力与各端业务边界-方案B.md`**；写权：`微服务拆分与作用域.md`；现网：`现网架构说明.md`。

**已拍板**：大平台为主；近期同机；**方案 B** — 中台只基础接口，菜单/登录产品逻辑在各端业务。8 HTTP + Worker + utoo_biz。中途改架构须先问。

## 本地开发

一键：`E:\utoo\dev-start.bat` 或 `scripts\dev-all.ps1` → 前端 http://127.0.0.1:9530，网关 http://127.0.0.1:18083。详见 `docs/现网架构说明.md`。

## Cursor 规则

**`E:\utoo\.cursor\rules\`** — 平台微服务约定、**方案 B 边界（强制）**、Django 代码组织。

# qd_test_server_django

青岛检测平台 **Django + DRF + Celery** 主后端（D0 脚手架）。

| 目录 | 说明 |
|------|------|
| `E:\utoo\qd_test_server` | Java（只读） |
| `E:\utoo\qd_test_server_py` | FastAPI 参考实现（冻结） |
| **本项目** | Django 主开发 |
| `E:\utoo\qd_test_front_v3` | Vue3 前端 |

决策与迁移路线：`E:\utoo\qd_test_server\docs\Django技术栈与迁移决策.md`

## 快速启动

```powershell
cd E:\utoo\qd_test_server_django
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# 可从 qd_test_server_py\.env 复制数据库/Redis/微信等配置
python run.py
```

默认 **http://127.0.0.1:18083**（与 FastAPI 端口一致，前端 `VITE_API_TARGET` 可不变）。

## 健康检查

| URL | 说明 |
|-----|------|
| `GET /health` | 简单 JSON |
| `GET /` | 服务信息 |
| `GET /api/health/` | DRF 统一响应 `{code,message,data}` |

## Celery（D2 支付队列前可选）

```powershell
.\scripts\run_celery_worker.ps1
```

## 测试

```powershell
.\.venv\Scripts\pytest
```

## 目录结构

```
config/          # settings, urls, celery
apps/
  core/          # 健康检查、统一响应
  auth_pc/       # D1 登录 JWT
  pc_compat/     # .ajax 薄层
  orders/ payments/ invoices/ entry/ wx/
tasks/           # Celery 任务
tests/
```

## D1 接口（已实现）

| 方法 | 路径 |
|------|------|
| POST | `/api/auth/login` |
| POST | `/api/auth/refresh` |
| GET | `/api/auth/me` |
| GET | `/api/pc/getUserBasicInfo.ajax` |

## 下一步（D2）

订单、资产、支付等，从 `qd_test_server_py` 对照移植。

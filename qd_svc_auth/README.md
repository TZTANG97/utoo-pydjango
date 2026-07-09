# qd_svc_auth

**认证与用户** 微服务（MS-1）。

- **默认 HTTP 端口**：**18081**
- **职责**：登录、JWT 刷新、`/me`、用户基本信息
- **共享库**：`../qd_libs_common`（`qd_common.responses`、`password_java`）

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/auth/login` | C 端登录 |
| POST | `/api/auth/refresh` | 刷新 token |
| GET | `/api/auth/me` | 当前用户认证信息 |
| GET | `/api/auth/basic-info` | 用户基本信息（网关映射 `getUserBasicInfo.ajax`） |

## 启动

```powershell
cd E:\utoo\qd_svc_auth
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install -e ..\qd_libs_common
copy .env.example .env   # 或从网关复制 .env
.\.venv\Scripts\python.exe run.py
```

或：`E:\utoo\scripts\start-auth.ps1`

## 网关联调

在 `qd_test_server_django/.env` 或 `.env.local` 增加：

```env
SVC_AUTH_URL=http://127.0.0.1:18081
```

网关 `:18083` 将把 `/api/auth/*` 与 `getUserBasicInfo.ajax` 转发到本服务。未配置时仍走网关内置实现（单体模式）。

## 验证

```powershell
curl http://127.0.0.1:18081/health
.\.venv\Scripts\pytest
```

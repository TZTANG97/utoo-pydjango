# qd_svc_wx

**微信** 微服务（扫码登录、预约详情、意见反馈）。

- **默认 HTTP 端口**：18087
- **职责**：`/api/wx/*` 兼容接口

## 启动

```powershell
E:\utoo\scripts\start-wx.ps1
```

健康检查：`GET http://127.0.0.1:18087/health`

网关转发：在 `qd_test_server_django/.env` 设置 `SVC_WX_URL=http://127.0.0.1:18087`

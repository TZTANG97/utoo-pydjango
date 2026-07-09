# qd_svc_entry

**讨论区** 微服务（MS-3）。

- **默认 HTTP 端口**：18086
- **职责**：帖子列表/详情、发布/删除、评论、点赞/收藏等 `/api/entry/*` 接口。

## 启动

```powershell
E:\utoo\scripts\start-entry.ps1
```

## 验证

```powershell
GET http://127.0.0.1:18086/health
pytest
```

## 网关转发

```
SVC_ENTRY_URL=http://127.0.0.1:18086
```

共享响应库：`../qd_libs_common`。

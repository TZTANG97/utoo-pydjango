# qd_worker

**后台任务** 微服务占位仓。

- **默认 HTTP 端口**：—
- **职责**：Celery Worker / Beat：支付回调队列、超时关单等，无 HTTP 端口。

脚手架与网关转发约定见 `qd_test_server/docs/微服务拆分与仓库约定.md`。共享响应库：`../qd_libs_common`（`qd_common.responses`）。

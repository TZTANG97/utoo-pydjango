# qd_worker

**后台任务** 微服务占位仓。

- **默认 HTTP 端口**：—
- **职责**：Celery Worker / Beat：支付回调队列、超时关单等，无 HTTP 端口。

约定见 `E:\utoo\docs\现网架构说明.md`。共享响应库：`../qd_libs_common`（`qd_common.responses`）。

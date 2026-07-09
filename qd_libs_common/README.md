# qd_libs_common

QD 微服务共享 Python 包 **`qd_common`**。

## 安装（开发）

在各服务虚拟环境中：

```bash
pip install -e ../qd_libs_common
```

## 响应工具

```python
from qd_common.responses import api_ok, ajax_ok, ajax_fail
```

- **api_ok / api_fail**：`code` / `message` / `data`（新前端、DRF 常用）
- **ajax_ok / ajax_fail**：`res` / `resMsg` / `obj`（客户 PC `.ajax` 兼容）

修改响应契约时只改本仓，再升级各 `qd_svc_*` 依赖版本。

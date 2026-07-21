# qd_svc_auth（已废弃）

**C 端认证已并回网关 [`qd_test_server_django`](../qd_test_server_django) 进程内 `apps/auth_pc`。**

- 后台员工登录本来就在网关 `admin_auth`（`/api/vue/*`）。
- C 端 `/api/auth/*`、资料相关转发：清空 `SVC_AUTH_URL` 后走网关本地实现。
- **勿再**配置 `SVC_AUTH_URL`、勿再启动本目录（原 :18081）。

新功能请改网关 `apps/auth_pc` / `apps/pc_compat`。保留本目录仅作对照。

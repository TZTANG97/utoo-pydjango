# DEPRECATED（twin 本体）

- **日期**：2026-09-05
- **状态**：`UTOO_BIZ_SERVICE_URL` / biz 开启时，本包**不再**挂入 `api/_internal/*`；正式流量走 **mid（asset）/ utoo_biz**。
- **P3 INSTALLED_APPS**：biz 开时**不装**（`config.twin_install.TWIN_EMERGENCY_ONLY_APPS`）；未开 biz 时装入作 `_internal` / 公开 twin 应急。
- **约束**：勿新写功能；代码仅作未开 biz 时的应急 twin 与对照。**勿 git rm**；P5 前可只读对照。
- **权威清单**：[`docs/utoo-route-inventory.md`](../../../../docs/utoo-route-inventory.md) §4 / V4。

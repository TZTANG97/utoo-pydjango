# DEPRECATED（twin 本体）

- **日期**：2026-09-05
- **状态**：`UTOO_BIZ_SERVICE_URL` / biz 开启时，本包**不再**挂入 `api/_internal/*`；正式流量走 **mid（asset）/ utoo_biz**。
- **P3 INSTALLED_APPS**：**仍保留** —— 公开 GW-LOCAL 强依赖：
  - `api/labPerformanceSaleuser|adminLabSale/expOrderList.ajax`（`urls._lab_sale_perf_local_patterns`）
  - Asset 代理白名单本地回落（`admin_asset_forward._local_asset_fallback`）
  - Celery `tasks.refresh_*_stat_*` / `refresh_all_stat_snapshots`
- **约束**：勿新写功能；整包 twin 路由仅未开 biz 应急。**P5 前**再评估迁 asset / 卸装。
- **权威清单**：[`docs/utoo-route-inventory.md`](../../../../docs/utoo-route-inventory.md) §4 / V4。

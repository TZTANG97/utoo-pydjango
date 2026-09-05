# DEPRECATED（twin / `_internal` 本体）

- **日期**：2026-09-05
- **状态**：biz 开启时本包**不再**挂入 `api/_internal/pc/`，公开 `/api/pc/` 亦由 biz→mid 承接；正式流量走 **mid / utoo_biz**。
- **P3 INSTALLED_APPS**：**仍保留** —— 公开 GW-LOCAL 强依赖：`api/seller/swf_upload.ajax`（`urls._seller_patterns` → `views_seller`）。未开 biz 时另供 `_internal/pc` / `wx_mp` 别名应急。
- **约束**：勿新写 C 端产品功能。`wx_mp` 对 pc 视图的 **import 复用**（仅未开 biz 挂整包 urls）不代表可继续扩 twin。**P5 前**可把 seller 迁出后再卸装。
- **权威清单**：[`docs/utoo-route-inventory.md`](../../../../docs/utoo-route-inventory.md) §4 / V4。

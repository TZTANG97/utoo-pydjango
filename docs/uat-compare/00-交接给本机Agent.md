# 愉兔 UAT 新旧站对比 — 交接给本机 Cursor Agent

请在打开 **`E:\utoo\utoo.code-workspace`** 的前提下处理下列缺陷。  
权威对照环境：

| | URL |
|---|---|
| 新站（Python） | https://uat.utoodev.laide.tech |
| 旧站（Java） | https://uat.utoo.laide.tech |

代码主目录（Python 覆写）：**`E:\utoo\utoo-pydjango`**（远程公司 GitLab，只读对照 Java：`qd_test_server` / `E:\mall_qingdao` 等见 `E:\utoo\AGENTS.md`）。

本目录由 Grok Bot 在 UAT 点击/数据核对后生成。**优先修新站（utoodev）问题**；旧站仅作对照，除非清单写明旧站也要改。

---

## 已完成模块与清单文件

1. `实验室人员产出计划设定-缺陷清单.md` — 数字化中心相关  
2. `库存管理-缺陷清单.md` — `/#/admin/inventory/list`  
3. `仓库管理-缺陷清单.md` — `/#/admin/inventory/warehouses`  
4. `样品仓库管理-缺陷清单.md` — `/#/admin/inventory/sample-warehouses`  

（样品留存仓库管理等后续模块会继续追加到本目录。）

---

## 建议处理顺序（跨模块）

### P0
1. **库存数据口径**：新旧总量/样例大量不一致（见库存清单 BUG-INV-01/02/03）— 先确认是否同一数据源/租用过滤，再改代码  
2. **新站实验平台下拉「无数据」**（库存 BUG-INV-04）  
3. **样品仓库配置页新站无地块数据**（样品仓库 BUG-SWH-01）  
4. **仓库配置位置首屏数据不一致**（仓库 BUG-WH-02）  
5. **计划设定：旧站 NaN 时间 / 查看弹层空白 / 设定不预填**（计划设定 BUG-01/02/03）— 若只保新站，核对新站是否已规避  

### P1
6. **负责人展示 vs 检索**：列表显示姓名、搜索要编码 CS04；按「韩想」搜不到（仓库 BUG-WH-01；样品仓类似 04 vs U04）  
7. **清空筛选不自动重查**（计划设定、库存多处）  
8. 字段模型/文案对齐（状态、备注、手机 vs 联系电话等）

---

## 给 Agent 的约束

- 遵循 `E:\utoo\AGENTS.md` 与 `.cursor/rules`（方案 B 边界）  
- 改动落在 `utoo-pydjango`（及清单点名的前端 `utoo-web-front` / admin 视图）  
- 不要改 Java 只读对照仓，除非用户明确要求  
- 每修一类问题：说明根因、改动文件、如何在 UAT 复验  
- 库存「数据完全对不上」类：先查 API/过滤条件再改 UI  

---

## 用户如何 @ 你

在 Cursor 对话中附上本文件或整个文件夹：

`E:\utoo\docs\uat-compare\`

并说明：「按 00-交接给本机Agent.md 的 P0 顺序修新站缺陷」。

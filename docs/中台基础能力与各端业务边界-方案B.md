# 中台基础能力与各端业务边界 · 方案 B（已拍板）

> **状态**：已拍板（2026-08-24）  
> **取代**：原「登录/菜单/渠道筛选全部在 identity 中台完成」的默认做法（方案 A）  
> **权威配套**：[大平台与UTOO-方向与交互.md](./大平台与UTOO-方向与交互.md)、[微服务拆分与作用域.md](./微服务拆分与作用域.md)  
> **Cursor 规则**：`E:\utoo\.cursor\rules\platform-boundary-scheme-b.mdc`（**alwaysApply，强制**）

---

## 1. 拍板结论（一句话）

**中台只提供跨平台共用的「基础能力接口」与「主数据写权」；各端自己的产品逻辑（登录编排、菜单拼装与筛选、官网/小程序/后台交互）写在各自业务进程中，禁止把 UTOO/青岛独有产品堆进中台。**

---

## 2. 为什么要方案 B

| 问题（方案 A 现状） | 方案 B 目标 |
|---------------------|-------------|
| identity 同时承担「令牌/用户主数据」与「各端菜单产品逻辑」 | 中台偏「原子能力 + 写权」 |
| 愉兔官网/小程序能力被误当成「该进中台」 | UTOO 产品面归 UTOO 业务（网关 / `utoo_biz` / 前端） |
| 青岛经营与 UTOO 检测 C 端边界模糊 | 青岛经营归 mall；UTOO 检测产品归 UTOO |
| 网关本地 twin、兜底写库 | 网关只做 BFF；写库只在对应写进程 |

**不变底线**：共库 `qd_pt_new`、一张表一个写进程、禁止 twin 状态机、8 HTTP + Worker 形态不变。

---

## 3. 三层边界（强制）

```text
┌─────────────────────────────────────────────────────────────────┐
│ 中台 platform/*  （共用一份，只提供基础接口）                      │
│   identity · order · payment · asset · platform · worker        │
│   职责：主数据写权、令牌、领域状态机、支付/库存/发票写权            │
│   禁止：官网页面、小程序流程、某一端的菜单产品拼装                  │
└─────────────────────────────────────────────────────────────────┘
          ▲ HTTP 只读/写权接口                    ▲
          │                                       │
┌─────────┴──────────────┐            ┌───────────┴──────────────┐
│ 青岛业务                │            │ UTOO 业务                   │
│ gateway :18080         │            │ utoo_gateway :18083        │
│ mall :18092            │            │ utoo_biz :18093（愉兔独有）  │
│ admin-web              │            │ utoo-web-front / 小程序      │
│ 菜单拼装/登录编排/经营  │            │ 菜单拼装/登录编排/官网小程序  │
└────────────────────────┘            └────────────────────────────┘
```

---

## 4. 中台「只做什么」（identity 为例）

### 4.1 identity 中台 — 保留（基础能力）

| 能力 | 说明 | 典型接口形态 |
|------|------|--------------|
| 凭证校验 | 账号密码、刷新令牌、JWT 签发/校验 | `POST /auth/login`、`POST /auth/refresh` |
| 用户/员工主数据读 | 按 id/登录名查用户、部门、角色 **原始关系** | `GET /users/{id}`、`GET /roles/{id}` |
| 组织主数据写 | 部门/角色/用户/菜单 **CRUD**（后台配置用） | 组织写接口（仅管理端配置场景） |
| 权限数据读 | 角色-菜单 id 列表、数据范围 **原始数据** | `GET /roles/{id}/menu-ids`（原子，非树） |
| C 端客户 | `exp_user` 注册/绑定/基础资料 | 原子 CRUD |

**写表（唯一写进程）**：`sy_users`、`sy_role`、`sy_menu`、`sy_department` 及登录审计相关表。

### 4.2 identity 中台 — 迁出（产品逻辑 → 各端业务）

| 现可能在 identity 的逻辑 | 迁到 |
|--------------------------|------|
| 按 `X-Channel` 拼完整前端菜单树 | 青岛 → `gateway` 或 mall 模块；UTOO → `utoo_gateway` 或 `utoo_biz` |
| 「青岛只看 pt_type 含 1」的产品筛选 | **青岛网关 / mall** |
| 「UTOO 管理端 type=2」的产品筛选 | **愉兔网关 / utoo_biz** |
| C 端「管理菜单为空」的产品规则 | **愉兔网关 / utoo_biz** |
| 登录页流程（扫码、记住密码、跳转） | **各端前端 + 各端网关编排** |
| 登录成功后返回「前端专用 me 结构」 | **各端 BFF 组装**（中台只返用户原子字段） |

### 4.3 其它中台 — 边界不变

| 进程 | 中台保留 | 禁止放进中台 |
|------|----------|--------------|
| order | 实验单状态机、样品/复测写权 | UTOO 订单列表 UI 字段拼装 |
| payment | 支付、回调、余额扣减 | 愉兔充值页流程 |
| asset | 库存/台账写权 | 青岛销售页展示逻辑 |
| platform | 入驻/发票/运营配置写权 | 某一端开票向导 UI |

---

## 5. 各端业务「写什么」

### 5.1 青岛（大平台）

| 组件 | 端口 | 职责 |
|------|------|------|
| `gateway` | 18080 | BFF：鉴权透传、**青岛菜单树拼装**、转发中台/mall |
| `services/mall` | 18092 | 销售/采购/租赁/欢迎页等 **经营写权** |
| `admin-web` | — | 青岛后台 UI |

**菜单规则（产品逻辑，在青岛业务实现）**：

- 过滤条件：`sy_role.type = 1` 且 `sy_menu.pt_type` 含 `1`
- 从中台读取：角色、菜单 id 列表、菜单行 **原始数据**
- 在 **gateway 或 mall** 完成：树形拼装、隐藏项、排序、与前端路由映射

### 5.2 UTOO（愉兔）

| 组件 | 端口 | 职责 |
|------|------|------|
| `platform/utoo_gateway` | 18083 | BFF：历史 `.ajax` 兼容、**UTOO 菜单/me 拼装**、转发中台 |
| `services/utoo_biz` | 18093 | **愉兔独有**后端（讨论区、预约展示编排、官网聚合等） |
| `utoo-web-front` / 小程序 | 9530/9540 等 | 官网、C 端、管理端 UI |

**UTOO 产品面（必须在 UTOO 业务，禁止进中台）**：

- 对外官网、小程序页面与交互
- UTOO 管理端菜单筛选（`type=2` / `pt_type` 含 `2`）
- C 端个人中心、首页、实验分类展示编排
- 微信扫码登录 **页面流程**（令牌仍走 identity/payment 原子接口）

**`utoo_biz` 与 `utoo_gateway` 分工**：

| 放网关 | 放 utoo_biz |
|--------|-------------|
| 薄适配、路径兼容、聚合 1～2 个中台调用 | 有写表/有领域状态、UTOO 独有表 |
| 菜单/me 拼装（读中台后组装） | 讨论帖、预约咨询、运营页配置等 UTOO 域 |
| 禁止在网关写业务表 | 禁止复制 order/payment 状态机 |

### 5.3 与 mall 的对称关系

| 青岛 | UTOO |
|------|------|
| `mall` = 经营域进程 | **没有** second mall |
| 销售/采购/租赁 | 检测 C 端产品 + `utoo_biz` |
| 一般不写 `experiment_order*` | 实验单写权在 **order 中台** |

---

## 6. 调用链示例（方案 B）

### 6.1 青岛 admin 登录 + 菜单

```text
admin-web
  → POST /api/identity/auth/login        （gateway 转发 → identity 基础登录）
  → GET  /api/qd/menus/tree              （gateway 或 mall：读 identity 原子数据后拼装）
       └─ identity: GET role/menu 原始数据
       └─ gateway: 按 pt_type=1 过滤 + 建树
```

### 6.2 UTOO C 端登录 + 个人中心

```text
utoo-web-front
  → POST /api/pc/login...                （utoo_gateway：编排）
       └─ identity: 校验/签发
       └─ utoo_gateway: 返回 C 端 me 结构（非中台菜单树）
  → GET  /api/pc/center/...              （utoo_gateway / utoo_biz）
```

### 6.3 实验单领用（仍在中台）

```text
任一前端 → 各自网关 → order 中台（状态机）
禁止：gateway / utoo_biz / mall 本地写 experiment_order*
```

---

## 7. 写权表（更新后）

| 表族 | 唯一写进程 | 各端业务允许 |
|------|------------|--------------|
| `sy_*` 用户/角色/菜单/部门 | **identity** | 只读 + 拼装，**禁止**各端写 |
| `experiment_order*` | **order** | 只调接口 |
| 支付/余额 | **payment** | 只调接口 |
| 销售/采购/租赁 | **mall** | 青岛专属 |
| 库存/台账 | **asset** | 只调接口 |
| 入驻/发票 | **platform** | 只调接口 |
| UTOO 独有业务表（讨论、预约扩展等） | **utoo_biz** | UTOO 专属 |

---

## 8. 迁移路线（分阶段，禁止跳步）

### 阶段 M0 — 文档与规则（**已完成 2026-08-24**）

- [x] 拍板方案 B
- [x] 本文档 + Cursor 规则强制
- [x] 更新 [大平台与UTOO-方向与交互.md](./大平台与UTOO-方向与交互.md) 交互图
- [x] 更新 [微服务拆分与作用域.md](./微服务拆分与作用域.md) §3.1–3.3 网关/identity 作用域
- [x] 更新 [现网架构说明.md](./现网架构说明.md) 端口表（含 `utoo_biz :18093`）
- [x] 更新 [AGENTS.md](../AGENTS.md) 与 [README.md](./README.md) 入口

### 阶段 M1 — 契约拆分（1～2 周）

**identity 中台**

1. 梳理现有「菜单树 / me / login 响应」字段，拆成：
   - **基础 API**：用户、角色、menu-id 列表、部门
   - **Deprecated**：带渠道过滤的聚合菜单树（标记废弃日期）
2. 文档化 OpenAPI/对照表条目（补进 [API对照表.md](./API对照表.md)）

**青岛 gateway**

1. 新增 `/api/qd/menus/*`（或 mall 模块）实现菜单树拼装
2. admin-web 改调青岛 BFF，不再依赖 identity 聚合菜单

**愉兔 utoo_gateway**

1. 新增 UTOO 菜单/me 拼装层（admin / pc / wx 分路由）
2. 官网/小程序登录流程保留在网关+前端，identity 只收凭证

**验收**

- identity 停掉聚合菜单接口后，青岛/UTOO 各自菜单仍正常
- 停 identity → 登录失败 503；菜单接口不应 silently 走本地 twin

### 阶段 M2 — 清 twin 与兜底（2～4 周）

1. 列出 `utoo_gateway` 所有 `forward_*_first` 本地兜底路径
2. 缺接口 → **补到中台**，不是网关继续写
3. `utoo_biz` 接入第一批 UTOO 独有域（从讨论/预约等选 1 个试点）

### 阶段 M3 — 旧仓收口

1. `utoo-pydjango/qd_svc_*` 停止活跃发版
2. 所有中台改动只进 `mall_qingdao_pydjango/platform/`

---

## 9. 禁止清单（违反即退回）

| # | 禁止 | 原因 |
|---|------|------|
| F1 | 在 identity 新增「仅 UTOO 官网/小程序用」的产品接口 | 产品归 UTOO 业务 |
| F2 | 在 identity 新增「仅青岛 admin 用」的页面编排接口 | 产品归青岛业务 |
| F3 | 在 utoo_gateway 写 `experiment_order*` / 支付状态 | 写权在 order/payment |
| F4 | 在 mall 写库存/发票/实验单 | 写权在中台 |
| F5 | 各端复制一套 `sy_menu` / 用户表 | 主数据只在 identity 写 |
| F6 | 网关 `forward_*` 上游 404 时本地写库兜底 | 必须 503 或补中台接口 |
| F7 | 为 UTOO 再建一套 order/payment/identity 进程 | 8+1 形态不变 |
| F8 | 把青岛销售/采购写进 utoo_biz | 经营域归 mall |

---

## 10. Code Review 门禁（强制）

PR / 合并前自检：

1. **改动的进程是哪个？** 是否越界（见 §4、§5）
2. **是否写库？** 表是否属于该进程写权（§7）
3. **是否产品逻辑？** 若带 `pt_type`/渠道/UI 字段拼装，应在 gateway/mall/utoo_gateway/utoo_biz
4. **是否 twin？** 与 order/payment/identity 已有能力重复则拒绝
5. **是否补测？** 梳理 → 复写 → 交叉测试 → 前端按钮（见代码组织约定）

Agent / 人工开发：**不确定归属时必须先问用户**，禁止默认塞进中台。

---

## 11. 目录与发版归属

| 改什么 | 仓库路径 | 发版单元 |
|--------|----------|----------|
| 中台基础接口 | `mall_qingdao_pydjango/platform/{identity,order,payment,...}` | 对应中台进程 |
| 青岛菜单/登录编排 | `mall_qingdao_pydjango/gateway/`、`services/mall/` | gateway / mall |
| UTOO 菜单/登录编排 | `mall_qingdao_pydjango/platform/utoo_gateway/` | utoo_gateway |
| UTOO 独有业务 | `mall_qingdao_pydjango/services/utoo_biz/` | utoo_biz |
| UTOO 前端 | `mall_qingdao_pydjango/utoo-web-front/` | 前端静态 |
| 青岛前端 | `mall_qingdao_pydjango/admin-web/` | 前端静态 |
| 旧 UTOO 仓 | `utoo-pydjango/qd_svc_*` | **禁止活跃发版** |

---

## 12. 与现有文档的同步项

以下文件须与方案 B 一致（M0 内完成）：

| 文件 | 修改要点 | M0 |
|------|----------|-----|
| `大平台与UTOO-方向与交互.md` | §2 交互图：登录/菜单改为「各端 BFF + identity 基础」 | ✅ |
| `微服务拆分与作用域.md` | §3.3 identity：拆「基础 vs 产品」；§3.1/3.2 网关增加菜单职责 | ✅ |
| `现网架构说明.md` | 端口表增加 `utoo_biz :18093` | ✅ |
| `AGENTS.md` | 指向本文档 | ✅ |
| `.cursor/rules/platform-microservices.mdc` | 写权表与禁止项 | ✅ |
| `.cursor/rules/platform-boundary-scheme-b.mdc` | 新建，alwaysApply | ✅ |
| `mall-layering.mdc` | 菜单过滤归属 gateway/mall | ✅ |

---

## 13. 决策记录

| 日期 | 决策 |
|------|------|
| 2026-08-20 | 大平台为主、8+1、中台只提供接口（总原则） |
| 2026-08-24 | **方案 B**：中台基础能力 + 各端业务负责菜单/登录产品逻辑 |

---

## 14. 附录：快速判定表

**新需求来了，放哪？**

| 问题 | 是 → 去向 |
|------|-----------|
| 青岛和 UTOO 都要用，且涉及同一张表写？ | 中台（对应写进程） |
| 只有青岛经营用？ | mall |
| 只有 UTOO 官网/小程序/管理端用？ | utoo_gateway / utoo_biz / 前端 |
| 只是菜单怎么展示、登录后跳哪？ | 各端 BFF，不调中台新产品接口 |
| 只是读用户/角色/菜单 id？ | 调 identity **原子读接口**，在 BFF 拼装 |

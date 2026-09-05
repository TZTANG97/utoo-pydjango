# utoo_biz · 愉兔业务进程

**services/utoo_biz**，端口 **18103**（文档目标亦见 `:18093`；本地以 `start-dev.ps1 -IncludeUtoo` 为准）。

对标青岛 `services/mall:18092`：愉兔**独有**后端进本进程，**不要**往中台 `platform/order|identity|payment|…` 或青岛 `mall` 里塞 UTOO 产品逻辑。

本机随 `.\scripts\start-dev.ps1 -IncludeUtoo` 拉起。

## 数据流（2026-09-05 · 对齐现网 `2585fd5`）

```text
# 愉兔管理端 / C 端实验域（阶段 A）
utoo-web-front → utoo_gateway :18083/api/adminExperiment/*
              → utoo_biz :18103/api/adminExperiment/*
              → platform/order :18082（状态机，只写 order 进程；缺 URL→503）

# C 端 / 登录 / 小程序（阶段 B）
utoo-web-front / 小程序 → utoo_gateway :18083/api/pc|auth|wx|consult/*
                       → utoo_biz :18103
                       → order / payment / platform / identity
                       （userRoles = 本进程本地；consult = mid；
                         wx stubs 仅 → gateway /api/_internal/wx）

# 管理端 welcome / billing / 资金（阶段 C）
utoo-web-front → utoo_gateway :18083/api/vue/welcome.ajax
              → utoo_biz :18103 本地编排（shared.utoo_welcome，主路径无直 SQL）
              → order / identity / asset 原子 mid

             → /api/vue/{invoice|paymentapply|…}  网关 forward_*_first → 中台
             → /api/funds/*、/api/companyPay/* … → utoo_biz → admin_asset :18090
               （缺 asset URL→503；禁 silent _internal）

# 青岛 admin-web 实验订单
admin-web → gateway :18080/api/orders/utoo/*
         → utoo_biz :18103/api/v1/utoo/*
         → platform/order :18082
```

- 实验订单写逻辑仍在 `platform/order`；本进程做 JWT 改签 + **业务编排层**（list/audit 已有 scope/gate；其余多透传）。
- **welcome**：`BIZ_LOCAL`（非 `_internal`）；KPI/syslog/helper/汇率/公司账户走 mid。
- biz 开启时网关 `_internal` **仅 wx stubs**；勿再假定 welcome/billing/pc 回落 twin。
- 实验主数据（类目/项目/产品/品牌）增删改查经本进程转发中台 `adminExperiment/*` 接口。

---

## 方案 B 边界

| 放 utoo_gateway | 放 utoo_biz |
|-----------------|-------------|
| 薄适配、路径兼容、聚合 1～2 个中台调用 | 有写表、有领域状态、UTOO 独有表 |
| 菜单/me **拼装**（读 identity 原子后组装；勿堆进 identity） | welcome 编排、讨论帖、预约咨询产品规则等 |
| 禁止写业务表 | 禁止复制 order/payment 状态机 |

**不做**：写 `experiment_order*`（→ order）；写青岛销售/采购（→ mall）；菜单树 / welcome 聚合进 identity。

---

## 启动

```powershell
.\scripts\start-dev.ps1 -IncludeUtoo
```

健康检查：`GET http://127.0.0.1:18103/health`

阶段 B 冒烟：`.\scripts\test-utoo-consumer-api.ps1`（改代码后须重启 utoo_biz + utoo_gateway）

盘点文档：[../../docs/utoo-route-inventory.md](../../docs/utoo-route-inventory.md)、[../../docs/UTOO_INTERFACE_SPLIT_CHECKLIST.md](../../docs/UTOO_INTERFACE_SPLIT_CHECKLIST.md)

---

## 相关

- [../README.md](../README.md)
- [../../platform/utoo_gateway/README.md](../../platform/utoo_gateway/README.md)
- [../../docs/中台基础能力与各端业务边界-方案B.md](../../docs/中台基础能力与各端业务边界-方案B.md)

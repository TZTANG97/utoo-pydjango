# 小程序对接 Django 网关

## 目录

| 仓库目录 | 原路径 | 说明 |
|----------|--------|------|
| `qd_tz_mp` | `F:\xcx\tzxcx\qd_utoo_mp` | 途哲科技小程序 |
| `qd_utoo_mp` | `F:\xcx\utxcx\qd_test_mp` | 愉兔检测小程序 |

## 环境与联调

1. `$baseUrl`（见各 MP `utils/commonFuncs.js`）：
   - `release` / **`trial`（体验版）** → `https://utootesting.com/console`（须已在公众平台配置合法域名）
   - `develop`（开发版）→ `https://uat.utoodev.laide.tech/api`
2. 请求头：`token` + `uniapp: true` + `X-Channel: wx`
3. 微信开发者工具：可勾选**不校验合法域名**；真机体验版**不会**跳过校验。若体验版白屏/无数据而开调试又正常，多为合法域名未包含当前 `$baseUrl` 主机名
4. 若要本机联调：临时把 `commonFuncs.js` 的 develop 地址改回 `http://127.0.0.1:18083/api`，启动网关 `:18083`；业务页需上游时再启 `scripts/start-ms-dev.ps1`（order/payment/asset/platform）

### 环境变量（网关 `.env`）

```env
# 愉兔 / 途哲小程序一键登录
WEIXIN_MP_APPID=
WEIXIN_MP_SECRET=
WEIXIN_MP_TZ_APPID=
WEIXIN_MP_TZ_SECRET=
# 开发未配密钥时可用固定手机号走 phoneOneLogin
DEV_WX_PHONE=13900001111
DEV_SMS_CODE=111111

# PC 微信扫码登录（公众号）
WEIXIN_GZH_APPID=
WEIXIN_GZH_SECRET=
WEIXIN_GZH_TOKEN=          # 公众号后台「服务器配置」Token，默认 youtu
WEIXIN_GZH_MINI_THUMB_MEDIA_ID=   # 客服消息小程序卡片封面 media_id
WEIXIN_MP_AUTH_PAGEPATH=staffB/auth_phone/auth_phone
```

`SVC_WX_URL` **仅**转发：`WeChatQRCodeGenerator` / `qrScanStatusCheck` / `reservationDetail` / `addFeedBack`。  
`wechatconfig.ajax` **始终网关本地**（微信要求 echostr/XML，不能走 JSON 代理）；与生成/轮询进程须共用同一 `REDIS_URL`。  
其余 `/api/wx/*`（登录、资料、业务别名）走网关 `apps.wx_mp`。

公众号后台「服务器配置」URL：

```text
{CORS_HTTPS}/api/wx/wechatconfig.ajax
```

## 已实现（登录相关）

- `/api/index/userRoles.ajax`：登录后用户类型/权限 map（防 404 清 token）
- `/api/pc/getXcxBanner.ajax` / `getTuZheBanner.ajax`：小程序封面图
- 登录：`getVerifyCodeLogin` / `phoneCodeLogin` / `userLoginToken` / `phoneOneLogin` / `phoneOneLoginTZ`
- 资料：`getIdentifyData` / `clearBindData` / `myInfo` / `getbindstatus` / `updateNickName` / `checkLoginName`
- 途哲：`TuZhebannerList` / `selFirAndSecClassListTuZhe`
- 与 `pc_compat` 同名别名（响应转为 `{res,resMsg,obj}`）：支付/预约/发票/banner/分类等
- **PC 扫码登录闭环**：
  - `WeChatQRCodeGenerator.ajax` / `qrScanStatusCheck.ajax`（可转发 payment）
  - `wechatconfig.ajax`（公众号回调：ticket→openid、推小程序授权卡）
  - `getUserInfo.ajax` / `userInfoAdd.ajax` / `ticketIsExist.ajax`（小程序授权页）

## 明确 stub（返回「接口暂未实现」）

`getAuditOrderList` / `getAuditOrderList1` / `getLog` / `selBankList` / `selSecondClassList` / `signInIntegral`

已实现：`getOrderCount`（员工「我的实验」订单角标统计）；`scanCodeOperate` / `isFlag`（扫码业务）

账号绑定支线仍 stub：`bindaccount` / `bindaccountTZ` / `securebind`（非 PC 扫码主链，可暂用账号/验证码/一键登录）

## PC 扫码验收顺序

1. 配好 `WEIXIN_GZH_*`（及 payment 侧若开启 `SVC_WX_URL`）→ 登录页出二维码（不再 501）
2. 公众号服务器 URL 指向可公网网关 → 扫码后轮询变为 `SCANNED` / 已绑定用户直接登录
3. 新用户：公众号推卡 → 小程序 `auth_phone` → `getUserInfo` → `fill_info` → `userInfoAdd` → PC `LOGGED_IN`

## 非 `/wx` 路径

改 baseUrl 后，`/experimentOrder/*`、`/consult/*`、`/pc/*`、`/redeem/*` 等走网关已有前缀。  
已实现小程序账户统计：`funds/assetAccxcx.ajax`、`funds/assetAccountxcx.ajax`、`yesterdayIncomexcx.ajax`、`selExpSumByYearxcx.ajax`。  
已实现可用余额 / 转账用户：`funds/account_userId.htm`、`account_User.ajax`。  
已实现实验详情：`pc/xcxtestClassDetail.ajax`（Ajax 封装，对齐 `testClassDetail`）。  
尚未下沉的如 `digitalManage/*xcx` 等需另排期。

## 冒烟清单

- [ ] 验证码登录（`DEV_SMS_CODE`）
- [ ] 账号密码登录
- [ ] 一键登录（`DEV_WX_PHONE` 或真实 MP 密钥）
- [ ] 首页 banner / 分类（需 order 上游或关 `SVC_ORDER_URL` 走本地）
- [ ] 订单列表 `/experimentOrder/list.ajax`（需 order）
- [ ] 预支付（需 payment + 微信商户配置）

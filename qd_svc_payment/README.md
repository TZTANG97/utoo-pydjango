# qd_svc_payment

**支付 / 资产 / 微信兼容** 微服务。

- **默认 HTTP 端口**：18084
- **职责**：
  - 积分/账户、余额支付、微信预下单、支付回调（`pay.ajax` / `rechargePay.ajax` 等）
  - **已并入原 `qd_svc_wx`**：`/api/wx/*`（扫码登录、预约详情、意见反馈）

## 启动

```powershell
.\scripts\start-payment.ps1
# 或
python run.py
```

## 验证

```powershell
GET http://127.0.0.1:18084/health
pytest
```

## 网关转发

```env
SVC_PAYMENT_URL=http://127.0.0.1:18084
# 微信接口与支付同进程，勿再指向 18087
SVC_WX_URL=http://127.0.0.1:18084
```

扫码登录需配置：`WEIXIN_GZH_APPID` / `WEIXIN_GZH_SECRET`（或兼容 `WEIXIN_APPID` / `WEIXIN_SECRET`）。

~~`qd_svc_wx`（:18087）已废弃~~，勿再单独启动。

共享库：`../qd_libs_common`。

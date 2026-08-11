# UTOO × IOT 联调验收脚本（Phase A+B）

用法（PowerShell，填真实公网 HTTPS 基址，勿写对方 127.0.0.1）：

```powershell
$env:UTOO_BASE = "https://utoo.example.com"
$env:IOT_BASE  = "https://iot.example.com"
$env:IOT_HMAC_SECRET = "change-me-hmac-secret"
$env:IOT_APP_ID = "utoo-iot"
$env:IOT_SERVICE_TOKEN = "change-me-service-token"
# 可选：管理员 / 用户 JWT、测试订单
$env:UTOO_ADMIN_TOKEN = ""
$env:UTOO_USER_TOKEN = ""
$env:ORDER_ID = ""
$env:CHILD_ID = ""
$env:DEVICE_ID = "DEV-DEMO-001"

pwsh -File E:\utoo\scripts\utoo-iot-e2e-accept.ps1
```

脚本会检查：

1. 双方 health / 回调路径 TLS 可达  
2. HMAC 错误签名 → 期望 401  
3. 同 eventId 幂等（若已配置订单）  
4. register → start → finish → runs（需 Token + 订单参数）  

人工补完：

1. UTOO：授权 IOT 运维账号（错密拒绝）→ 设备列表仅见该账号设备  
2. 绑→register→IOT pending 可见；越权账号不可见  
3. IOT `/main/utoo-tasks`：开始=WS+start-run+tasks/start；UTOO 子行→38；回调失败时 IOT 明确失败  
4. 结束→子行 39；重复 eventId 幂等且不毒化  
5. 未领用（36）子行：started 回调自动补领用后进 38  
6. C 端「试验数据」曲线

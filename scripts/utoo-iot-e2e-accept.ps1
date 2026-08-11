# UTOO × IOT Phase A+B 联调验收（可脚本化部分）
# 详见 docs/UTOO-IOT验收清单.md

$ErrorActionPreference = "Continue"

function Require-Env([string]$Name) {
  $v = [Environment]::GetEnvironmentVariable($Name)
  if ([string]::IsNullOrWhiteSpace($v)) {
    Write-Host "SKIP/FAIL: 缺少环境变量 $Name" -ForegroundColor Yellow
    return $null
  }
  return $v.TrimEnd("/")
}

function Invoke-CurlJson {
  param(
    [string]$Method,
    [string]$Url,
    [hashtable]$Headers = @{},
    [string]$Body = $null,
    [switch]$SkipSsl
  )
  $args = @("-sS", "-o", "-", "-w", "`nHTTP_CODE:%{http_code}", "-X", $Method, $Url)
  if ($SkipSsl) { $args = @("-k") + $args }
  foreach ($k in $Headers.Keys) {
    $args += @("-H", ("{0}: {1}" -f $k, $Headers[$k]))
  }
  if ($null -ne $Body) {
    $args += @("-H", "Content-Type: application/json", "-d", $Body)
  }
  try {
    $out = & curl.exe @args 2>&1 | Out-String
    return $out
  } catch {
    return "ERROR: $($_.Exception.Message)`nHTTP_CODE:000"
  }
}

function Get-HmacHex([string]$Secret, [string]$StringToSign) {
  $hmac = New-Object System.Security.Cryptography.HMACSHA256
  $hmac.Key = [Text.Encoding]::UTF8.GetBytes($Secret)
  $hash = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($StringToSign))
  return ([BitConverter]::ToString($hash) -replace "-", "").ToLowerInvariant()
}

function Get-UnixTs {
  return [string][int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
}

Write-Host "=== 0. 网络互探 ===" -ForegroundColor Cyan
$utoo = Require-Env "UTOO_BASE"
$iot = Require-Env "IOT_BASE"
if (-not $utoo -or -not $iot) {
  Write-Host "请设置 UTOO_BASE / IOT_BASE 后重试。" -ForegroundColor Red
  exit 2
}

$healthIot = Invoke-CurlJson -Method GET -Url "$iot/nss/api/v1/health/utoo-bridge"
Write-Host "IOT health:`n$healthIot"

$cbProbe = Invoke-CurlJson -Method OPTIONS -Url "$utoo/api/iot/callback/experiment-event"
Write-Host "UTOO callback probe:`n$cbProbe"

Write-Host "`n=== 1. 错误签名应 401 ===" -ForegroundColor Cyan
$secret = Require-Env "IOT_HMAC_SECRET"
$appId = if ($env:IOT_APP_ID) { $env:IOT_APP_ID } else { "utoo-iot" }
$ts = Get-UnixTs
$nonce = [guid]::NewGuid().ToString("N")
$body = '{"eventId":"e2e-bad-sig","event":"started","orderId":"X","childId":1,"deviceId":"D","iotTaskId":"1"}'
$badHeaders = @{
  "X-IOT-App-Id" = $appId
  "X-IOT-Timestamp" = $ts
  "X-IOT-Nonce" = $nonce
  "X-IOT-Signature" = "deadbeef"
}
$bad = Invoke-CurlJson -Method POST -Url "$utoo/api/iot/callback/experiment-event" -Headers $badHeaders -Body $body
Write-Host $bad
if ($bad -match "HTTP_CODE:401") {
  Write-Host "PASS: bad signature -> 401" -ForegroundColor Green
} else {
  Write-Host "CHECK: 期望 401（若网关改写状态码请人工核对）" -ForegroundColor Yellow
}

if ($secret) {
  Write-Host "`n=== 2. 幂等：同一 eventId 连发两次 ===" -ForegroundColor Cyan
  $eventId = "e2e-idem-" + [guid]::NewGuid().ToString("N").Substring(0, 12)
  $orderId = if ($env:ORDER_ID) { $env:ORDER_ID } else { "E2E-NOOP" }
  $childId = if ($env:CHILD_ID) { $env:CHILD_ID } else { "1" }
  $deviceId = if ($env:DEVICE_ID) { $env:DEVICE_ID } else { "DEV-DEMO-001" }
  $payloadObj = @{
    eventId = $eventId
    event = "started"
    orderId = $orderId
    childId = [int]$childId
    deviceId = $deviceId
    iotTaskId = "e2e-task"
  }
  $raw = ($payloadObj | ConvertTo-Json -Compress)
  $ts2 = Get-UnixTs
  $nonce2 = [guid]::NewGuid().ToString("N")
  $sig = Get-HmacHex -Secret $secret -StringToSign ($ts2 + "`n" + $nonce2 + "`n" + $raw)
  $okHeaders = @{
    "X-IOT-App-Id" = $appId
    "X-IOT-Timestamp" = $ts2
    "X-IOT-Nonce" = $nonce2
    "X-IOT-Signature" = $sig
  }
  $r1 = Invoke-CurlJson -Method POST -Url "$utoo/api/iot/callback/experiment-event" -Headers $okHeaders -Body $raw
  Write-Host "First:`n$r1"
  # 重放：同 body + 新时间戳签名（业务幂等看 eventId）
  $ts3 = Get-UnixTs
  $nonce3 = [guid]::NewGuid().ToString("N")
  $sig3 = Get-HmacHex -Secret $secret -StringToSign ($ts3 + "`n" + $nonce3 + "`n" + $raw)
  $okHeaders2 = @{
    "X-IOT-App-Id" = $appId
    "X-IOT-Timestamp" = $ts3
    "X-IOT-Nonce" = $nonce3
    "X-IOT-Signature" = $sig3
  }
  $r2 = Invoke-CurlJson -Method POST -Url "$utoo/api/iot/callback/experiment-event" -Headers $okHeaders2 -Body $raw
  Write-Host "Second (same eventId):`n$r2"
  Write-Host "人工确认：第二次不应再次推进状态（返回幂等/已处理）" -ForegroundColor Yellow
}

$token = $env:IOT_SERVICE_TOKEN
if ($token -and $env:ORDER_ID -and $env:CHILD_ID -and $env:DEVICE_ID) {
  Write-Host "`n=== 3. register → start → finish → runs ===" -ForegroundColor Cyan
  $ext = "utoo-" + $env:ORDER_ID + "-" + $env:CHILD_ID
  $regBody = (@{
    externalId = $ext
    orderId = $env:ORDER_ID
    childId = [int]$env:CHILD_ID
    deviceId = $env:DEVICE_ID
    projectName = "e2e"
    sampleSummary = "e2e"
  } | ConvertTo-Json -Compress)
  $svcH = @{ "X-UTOO-Service-Token" = $token; Authorization = "Bearer $token" }
  $reg = Invoke-CurlJson -Method POST -Url "$iot/nss/api/v1/tasks/register" -Headers $svcH -Body $regBody
  Write-Host "register:`n$reg"
  if ($reg -match '"taskId"\s*:\s*"?(\d+)"?') {
    $taskId = $Matches[1]
    $st = Invoke-CurlJson -Method POST -Url "$iot/nss/api/v1/tasks/$taskId/start" -Headers $svcH -Body "{}"
    Write-Host "start:`n$st"
    $fn = Invoke-CurlJson -Method POST -Url "$iot/nss/api/v1/tasks/$taskId/finish" -Headers $svcH -Body "{}"
    Write-Host "finish:`n$fn"
    if ($fn -match '"iotRunId"\s*:\s*"([^"]+)"') {
      $runId = $Matches[1]
      $run = Invoke-CurlJson -Method GET -Url "$iot/nss/api/v1/runs/${runId}?includeSeries=1" -Headers $svcH
      Write-Host "runs:`n$run"
    }
  }
} else {
  Write-Host "`nSKIP register 链路：需 IOT_SERVICE_TOKEN + ORDER_ID + CHILD_ID + DEVICE_ID" -ForegroundColor Yellow
}

Write-Host "`n=== 人工验收（脚本外）===" -ForegroundColor Cyan
Write-Host "1) UTOO 管理端订单详情：绑定设备 → sync ok → 可重新下发"
Write-Host "2) IOT 打开 /main/utoo-tasks：选任务开始/结束（非盲开）"
Write-Host "3) C 端状态 38→39，点「试验数据」见 summary/series"
Write-Host "完成。按 docs/UTOO-IOT验收清单.md 勾选。"

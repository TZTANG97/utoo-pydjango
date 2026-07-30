# Read-only: fingerprint https://uat.utoodev.laide.tech/ against expected SPA markers.
$ErrorActionPreference = 'Stop'
$Base = if ($args[0]) { $args[0].TrimEnd('/') } else { 'https://uat.utoodev.laide.tech' }

$tmp = Join-Path $env:TEMP ('utoo_uat_index_{0}.html' -f [Guid]::NewGuid().ToString('N'))
$hdr = Join-Path $env:TEMP ('utoo_uat_index_{0}.hdr' -f [Guid]::NewGuid().ToString('N'))
& curl.exe -sS -D $hdr -o $tmp --max-time 30 "$Base/"
if ($LASTEXITCODE -ne 0) { throw "curl failed for $Base/" }

$headers = Get-Content -LiteralPath $hdr -Raw
$html = Get-Content -LiteralPath $tmp -Raw -Encoding utf8
Write-Host "URL: $Base/"
if ($headers -match '(?im)^Last-Modified:\s*(.+)$') { Write-Host ("Last-Modified: {0}" -f $Matches[1].Trim()) }
if ($html -notmatch 'src="/assets/(index-[^"]+\.js)"') { throw 'index.html has no assets/index-*.js' }
$asset = $Matches[1]
Write-Host "entry: /assets/$asset"

$jsPath = Join-Path $env:TEMP ('utoo_uat_{0}' -f $asset)
& curl.exe -sS -D $hdr -o $jsPath --max-time 60 "$Base/assets/$asset"
$jsHeaders = Get-Content -LiteralPath $hdr -Raw
if ($jsHeaders -notmatch '(?im)^Content-Type:\s*application/javascript') {
	throw "assets/$asset is not application/javascript (SPA try_files fallback?). Check nginx /assets/ location."
}
$text = [IO.File]::ReadAllText($jsPath, [Text.Encoding]::UTF8)
foreach ($n in @('ServiceConsultDetail', 'warehouse-config', 'InventoryWarehouseConfig')) {
	$ok = $text.IndexOf($n, [StringComparison]::Ordinal) -ge 0
	Write-Host ("{0}: {1}" -f $n, $(if ($ok) { 'OK' } else { 'MISSING' }))
	if (-not $ok) { throw "Marker missing: $n" }
}
Write-Host 'verify-uat-frontend.ps1: OK'

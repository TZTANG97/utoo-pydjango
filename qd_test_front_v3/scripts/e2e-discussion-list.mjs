/**
 * 讨论列表：条数、加载结束、无一直转圈
 * 需：9530 前端、18083 Python API
 */
import { chromium } from 'playwright'

const BASE = process.env.E2E_BASE || 'http://127.0.0.1:9530'
const API = process.env.E2E_API || 'http://127.0.0.1:18083'
const MOBILE = '18211984686'
const PASSWORD = '123456'

async function apiListAll() {
  const login = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: MOBILE, password: PASSWORD, loginType: '1' }),
  })
  const lb = await login.json()
  if (lb.code !== 0) throw new Error(`login failed: ${JSON.stringify(lb)}`)
  const token = lb.data.token
  const qs = new URLSearchParams({ draw: '1', start: '0', length: '-1' })
  const r = await fetch(`${API}/api/entry/commenttreebulder.ajax?${qs}`, {
    headers: { token, Authorization: `Bearer ${token}` },
  })
  const body = await r.json()
  if (body.code !== 0) throw new Error(`list failed: ${JSON.stringify(body)}`)
  const dt = body.data
  return {
    total: dt.recordsTotal,
    page: (dt.data || []).length,
    firstId: dt.data?.[0]?.id,
  }
}

async function main() {
  const api = await apiListAll()
  console.log('API length=-1:', api)
  if (api.page < 10) {
    console.error('FAIL: API should return at least 10 discussion posts')
    process.exit(1)
  }

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()

  // 讨论列表支持未登录访问（对齐 Java uncheckUrls）
  const listReq = page.waitForResponse(
    (res) =>
      res.url().includes('commenttreebulder') && res.status() === 200,
    { timeout: 60000 }
  )
  await page.goto(`${BASE}/#/discussion`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  const resp = await listReq
  const json = await resp.json()
  const apiRows = json?.data?.data?.length ?? json?.data?.length ?? 0
  console.log('Browser API rows in response:', apiRows)

  await page.waitForTimeout(2000)
  let itemCount = await page.locator('.post-card').count()
  const feedLoading = await page.locator('.feed-status').isVisible().catch(() => false)

  console.log('DOM post-card count (first page):', itemCount)
  console.log('feed loading visible:', feedLoading)

  if (itemCount !== 10 && api.total > 10) {
    console.error('FAIL: first page should load 10 posts, got', itemCount)
    process.exit(1)
  }
  if (itemCount < 1) {
    console.error('FAIL: no posts on first page')
    process.exit(1)
  }
  if (feedLoading) {
    console.error('FAIL: bottom spinner should clear after first page')
    process.exit(1)
  }

  if (api.total > 10) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await page.waitForTimeout(2500)
    const itemCount2 = await page.locator('.post-card').count()
    console.log('DOM post-card count (after scroll):', itemCount2)
    if (itemCount2 <= itemCount) {
      console.error('FAIL: scroll should load more posts')
      process.exit(1)
    }
    itemCount = itemCount2
  }

  await browser.close()
  console.log('OK discussion list paginated, total loaded:', itemCount)
  process.exit(0)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})

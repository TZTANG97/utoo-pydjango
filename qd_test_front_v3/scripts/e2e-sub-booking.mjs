/**
 * E2E：登录 → 实验详情 → 立即预约 → 填表提交 → 我的预约 → 预约详情
 * 需 9530 前端、18083 Python 后端
 */
import { chromium } from 'playwright'

const BASE = process.env.E2E_BASE || 'http://127.0.0.1:9530'
const API = process.env.E2E_API || 'http://127.0.0.1:18083'
const MOBILE = process.env.TEST_LOGIN_MOBILE || '18211984686'
const PASSWORD = process.env.TEST_LOGIN_PASSWORD || '123456'
const MARK = `e2e-booking-${Date.now()}`

async function apiLogin() {
  const r = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: MOBILE, password: PASSWORD, loginType: '1' }),
  })
  const body = await r.json()
  if (body.code !== 0) throw new Error(`login failed: ${JSON.stringify(body)}`)
  return body.data.token
}

async function pickTestId(token) {
  const r = await fetch(`${API}/api/pc/expMakeList.ajax`, {
    headers: { token, Authorization: `Bearer ${token}` },
  })
  const body = await r.json()
  if (body.code !== 0 || !body.data?.length) {
    throw new Error('expMakeList empty')
  }
  const id = body.data[0].id
  const det = await fetch(`${API}/api/pc/testClassDetail.ajax?id=${id}`, {
    headers: { token, Authorization: `Bearer ${token}` },
  })
  const detBody = await det.json()
  return { id, special_type: detBody.data?.special_type }
}

async function loginUi(page) {
  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  const accountBtn = page.locator('img.account-login')
  if (await accountBtn.isVisible().catch(() => false)) {
    await accountBtn.click()
    await page.waitForTimeout(400)
  }
  await page.getByPlaceholder('请输入手机号').fill(MOBILE)
  await page.locator('input[type="password"]').first().fill(PASSWORD)
  await page.locator('.slider').click()
  await page.getByRole('button', { name: /登\s*录/ }).click()
  await page.waitForTimeout(2500)
}

async function fillBasicForm(page) {
  const dialog = page.locator('.el-dialog').filter({ hasText: '预约实验' })
  await dialog.waitFor({ state: 'visible', timeout: 15000 })
  await dialog.locator('.el-form-item').filter({ hasText: '姓名' }).locator('input').first().fill('E2E测试用户')
  await dialog.locator('.el-form-item').filter({ hasText: '手机号' }).locator('input').first().fill(MOBILE)
  const companyItem = dialog.locator('.el-form-item').filter({ hasText: '公司' })
  if (await companyItem.count()) {
    await companyItem.locator('input').first().fill('E2E测试公司')
  }
  const textarea = dialog.locator('textarea')
  if (await textarea.count()) {
    await textarea.first().fill(MARK)
  }
}

async function main() {
  const token = await apiLogin()
  const { id, special_type } = await pickTestId(token)
  console.log('test class id:', id, 'special_type:', special_type)

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()

  await loginUi(page)
  const hash = await page.evaluate(() => window.location.hash)
  if (!hash.includes('/b')) {
    console.warn('login hash:', hash)
  }

  await page.goto(`${BASE}/#/test_detail/${id}`, { waitUntil: 'networkidle', timeout: 60000 })
  await page.getByRole('button', { name: '立即预约' }).waitFor({ state: 'visible', timeout: 30000 })
  await page.getByRole('button', { name: '立即预约' }).click()

  await page.waitForTimeout(800)
  const dialogVisible = await page
    .locator('.el-dialog')
    .filter({ hasText: '预约实验' })
    .isVisible()
    .catch(() => false)
  if (!dialogVisible) {
    await page.screenshot({ path: 'e2e-sub-booking-no-dialog.png', fullPage: true })
    throw new Error('预约弹窗未打开，已保存 e2e-sub-booking-no-dialog.png')
  }

  await fillBasicForm(page)

  const dialog = page.locator('.el-dialog').filter({ hasText: '预约实验' })

  if (special_type === 1) {
    const sampleName = dialog.locator('.el-form-item').filter({ hasText: '名称/类型' }).locator('input').first()
    if (await sampleName.isVisible().catch(() => false)) {
      await sampleName.fill('E2E样品A')
    }
    const gold = dialog.locator('.el-form-item').filter({ hasText: '喷金' }).locator('input').first()
    if (await gold.isVisible().catch(() => false)) {
      await gold.fill('默认喷金')
    }
    await dialog.getByRole('button', { name: /确\s*定/ }).click()
  } else {
    await dialog.getByRole('button', { name: /确\s*定/ }).click()
  }

  await page.waitForTimeout(3000)
  const success = page.locator('.el-notification').filter({ hasText: /预约成功|提交成功/ })
  const okNotify = await success.first().isVisible().catch(() => false)
  console.log('success notification:', okNotify)

  await page.goto(`${BASE}/#/b/sub`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.waitForTimeout(2500)
  const tableText = await page.locator('.el-table').innerText().catch(() => '')
  const inList = tableText.includes(MARK) || tableText.includes('E2E')
  console.log('found in 我的预约:', inList)

  await browser.close()

  const listRes = await fetch(
    `${API}/api/pc/myExpMakeList.ajax?draw=1&start=0&length=20`,
    { headers: { token, Authorization: `Bearer ${token}` } }
  )
  const listBody = await listRes.json()
  const row = (listBody.data?.data || []).find((x) => (x.content || '').includes(MARK))
  if (!row) {
    console.error('API list missing booking marker')
    process.exit(1)
  }
  const detRes = await fetch(`${API}/api/wx/reservationDetail.ajax?id=${row.id}`, {
    headers: { token, Authorization: `Bearer ${token}` },
  })
  const det = await detRes.json()
  if (det.code !== 0) {
    console.error('reservationDetail failed', det)
    process.exit(1)
  }
  console.log('reservationDetail ok, consult id:', row.id)
  if (!okNotify) {
    console.warn('WARN: UI success toast not seen (API path OK)')
  }
  console.log('OK e2e-sub-booking')
  process.exit(0)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})

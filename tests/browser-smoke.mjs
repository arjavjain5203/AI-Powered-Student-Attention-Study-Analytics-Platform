/** Isolated browser QA using the local MongoDB server and a synthetic camera. */
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { createServer } from 'node:net'
import { closeSync, existsSync, mkdirSync, openSync, writeFileSync, writeSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright-core'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const backend = path.join(root, 'backend')
const qa = path.join(root, '.local', 'browser-qa')
mkdirSync(qa, { recursive: true })
const videoFile = path.join(qa, 'synthetic-camera.y4m')
if (!existsSync(videoFile)) {
  const file = openSync(videoFile, 'w')
  writeSync(file, 'YUV4MPEG2 W320 H240 F10:1 Ip A0:0 C420jpeg\n')
  const frame = Buffer.concat([Buffer.from('FRAME\n'), Buffer.alloc(320 * 240, 140),
    Buffer.alloc(160 * 120, 128), Buffer.alloc(160 * 120, 128)])
  for (let i = 0; i < 300; i++) writeSync(file, frame)
  closeSync(file)
}
const chrome = process.env.PLAYWRIGHT_CHROME_EXECUTABLE || [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
].find(existsSync)
if (!chrome) throw new Error('Set PLAYWRIGHT_CHROME_EXECUTABLE to a Chrome or Edge executable')

async function freePort() {
  const server = createServer()
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  const port = server.address().port
  await new Promise(resolve => server.close(resolve))
  return port
}
async function ready(url) {
  for (let attempt = 0; attempt < 70; attempt++) {
    try { if ((await fetch(url)).ok) return } catch { /* Server is starting. */ }
    await new Promise(resolve => setTimeout(resolve, 300))
  }
  throw new Error(`Server did not start: ${url}`)
}
function start(command, args, cwd, env) {
  const child = spawn(command, args, { cwd, env, windowsHide: true, stdio: 'pipe' })
  child.stderr.on('data', data => { if (/ERROR|Traceback/i.test(String(data))) process.stderr.write(data) })
  return child
}
async function nav(page, label) {
  if (await page.getByRole('button', { name: 'Open menu' }).isVisible()) await page.getByRole('button', { name: 'Open menu' }).click()
  await page.locator('.nav-item').filter({ hasText: label }).click()
}
function monitor(page) {
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => {
    if (message.type() === 'error' && !message.text().startsWith('INFO: Created TensorFlow Lite XNNPACK')) errors.push(message.text())
  })
  return errors
}

const apiPort = await freePort()
const webPort = await freePort()
const database = `study_attention_browser_qa_${randomBytes(6).toString('hex')}`
const origin = `http://127.0.0.1:${webPort}`
const apiOrigin = `http://127.0.0.1:${apiPort}`
const mongoUri = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/?directConnection=true'
const reviewToken = randomBytes(32).toString('hex')
const api = start('python', ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(apiPort)], backend, {
  ...process.env, MONGO_URI: mongoUri, MONGO_DB: database,
  JWT_SECRET: randomBytes(32).toString('hex'), REVIEW_ADMIN_TOKEN: reviewToken, CORS_ORIGINS: origin,
})
const vite = start(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', String(webPort)], root, {
  ...process.env, VITE_API_BASE_URL: apiOrigin,
})
let browser
const report = { database, viewports: [], routes: [], visualPayload: null, fakeCamera: false, errors: [] }
try {
  await ready(`${apiOrigin}/api/health/db`)
  await ready(origin)
  browser = await chromium.launch({ executablePath: chrome, headless: true, args: [
    '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--no-sandbox',
    `--use-file-for-fake-video-capture=${videoFile}`,
  ] })
  report.browser = { executable: path.basename(chrome), version: browser.version() }
  const context = await browser.newContext({ permissions: ['camera'], viewport: { width: 1440, height: 900 } })
  await context.addInitScript(() => {
    window.__cameraCalls = 0
    window.__cameraEvents = []
    document.addEventListener('visibilitychange', () => window.__cameraEvents.push({ type: 'visibility', state: document.visibilityState, at: performance.now() }))
    const original = navigator.mediaDevices?.getUserMedia?.bind(navigator.mediaDevices)
    if (original) navigator.mediaDevices.getUserMedia = async (...args) => {
      window.__cameraCalls += 1
      const stream = await original(...args)
      window.__lastCameraStream = stream
      stream.getTracks().forEach(track => {
        window.__cameraEvents.push({ type: 'created', state: track.readyState, at: performance.now() })
        track.addEventListener('ended', () => window.__cameraEvents.push({ type: 'ended', state: track.readyState, at: performance.now() }))
      })
      return stream
    }
  })
  const page = await context.newPage()
  const errors = monitor(page)
  const cameraAssetUrls = []
  page.on('request', request => { if (request.url().includes('/mediapipe/')) cameraAssetUrls.push(request.url()) })
  page.on('response', response => { if (response.status() >= 400) console.error('HTTP error:', response.status(), response.url()) })
  await page.goto(origin)
  await page.getByRole('heading', { name: 'Sign in' }).waitFor()
  assert.equal(await page.getByRole('button', { name: /Switch to demo|Switch to recorded data/ }).count(), 0)
  assert.equal(await page.locator('.nav-item').filter({ hasText: 'Recorded workspace' }).count(), 0)
  assert.equal(await page.evaluate(() => window.__cameraCalls), 0)
  for (const width of [375, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    await page.waitForTimeout(350)
    const dimensions = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth }))
    assert.ok(dimensions.document <= dimensions.viewport + 1, 'Sign-in overflow at ' + width)
    report.viewports.push({ mode: 'sign-in', width, ...dimensions })
  }
  const keyboardTarget = page.locator('.nav-item').filter({ hasText: 'Analytics' })
  await keyboardTarget.focus()
  await page.keyboard.press('Enter')
  await page.getByRole('heading', { name: 'Study analytics' }).waitFor()
  report.keyboardNavigation = true
  for (const label of ['Study session', 'Analytics', 'AI study coach', 'Goals & challenges', 'Achievements', 'Profile & settings', 'Overview']) {
    await nav(page, label)
    assert.ok(await page.locator('main h1').isVisible())
    report.routes.push(label)
  }
  await page.getByRole('button', { name: 'Create an account' }).click()
  await page.getByLabel('Name', { exact: true }).fill('Browser QA')
  const email = 'qa-' + randomBytes(4).toString('hex') + '@example.com'
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill('Browser-QA-password-123')
  await page.getByRole('button', { name: 'Register' }).click()
  await page.getByText('Browser QA · study workspace').waitFor()
  await nav(page, 'Study session')
  await page.getByLabel('Subject').fill('Synthetic camera QA')
  await page.getByRole('button', { name: 'Create session' }).click()
  const timer = page.getByRole('timer', { name: 'Active study session time' })
  await timer.waitFor()
  assert.equal(await timer.innerText(), '00:00:00')
  await page.waitForTimeout(1200)
  assert.equal(await timer.innerText(), '00:00:00', 'Camera setup time must not count')
  await page.getByRole('button', { name: 'Start camera and timer' }).click()
  await page.getByRole('button', { name: 'Stop monitoring' }).waitFor({ timeout: 30000 })
  await page.waitForFunction(() => document.querySelector('[role="timer"]')?.textContent !== '00:00:00', null, { timeout: 5000 })
  report.liveStudyTimer = true
  for (const width of [375, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    await page.waitForTimeout(350)
    await page.screenshot({ path: path.join(qa, 'session-' + width + '.png'), fullPage: true })
    const dimensions = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth }))
    assert.ok(dimensions.document <= dimensions.viewport + 1, 'Session overflow at ' + width)
    report.viewports.push({ mode: 'session', width, ...dimensions })
  }
  const first = await page.waitForResponse(response => response.url().endsWith('/visual-records') && response.request().method() === 'POST', { timeout: 25000 })
  assert.equal(first.status(), 201, await first.text())
  const payload = first.request().postDataJSON()
  assert.deepEqual(Object.keys(payload).sort(), ['algorithm_version', 'face_samples', 'forward_samples', 'total_samples', 'valid_samples'])
  report.visualPayload = payload
  report.fakeCamera = true
  const second = await page.waitForResponse(response => response.url().endsWith('/visual-records') && response.request().method() === 'POST', { timeout: 20000 })
  assert.equal((await second.json()).potential_visual_event, 'face_not_visible')
  await page.getByRole('heading', { name: 'Camera alert: study timer paused' }).waitFor()
  const pausedTime = await timer.innerText()
  await page.waitForTimeout(1200)
  assert.equal(await timer.innerText(), pausedTime, 'Automatic camera alert must pause time')
  report.provisionalEvent = 'face_not_visible'
  await page.getByRole('button', { name: 'False alarm' }).click()
  await page.waitForFunction(() => document.querySelector('video[aria-label="False alarm clip preview"]')?.readyState >= 1, null, { timeout: 5000 })
  const send = page.getByRole('button', { name: 'Send clip and continue' })
  assert.equal(await send.isEnabled(), false, 'Clip upload requires an explicit agreement')
  await page.getByRole('checkbox', { name: /I agree to send this clip/ }).check()
  assert.equal(await send.isEnabled(), true, 'Rolling clip must be available after consent')
  await send.click()
  await page.getByRole('heading', { name: 'Camera alert: study timer paused' }).waitFor({ state: 'detached' })
  const adminResponse = await fetch(apiOrigin + '/api/admin/false-alarms', { headers: { 'X-Review-Token': reviewToken } })
  assert.equal(adminResponse.status, 200)
  const reports = await adminResponse.json()
  assert.equal(reports.length, 1)
  assert.equal(reports[0].clip_shared, true)
  const clipResponse = await fetch(apiOrigin + '/api/admin/false-alarms/' + reports[0].id + '/clip', { headers: { 'X-Review-Token': reviewToken } })
  assert.equal(clipResponse.status, 200)
  assert.ok((await clipResponse.arrayBuffer()).byteLength > 4)
  report.falseAlarmClip = true
  await nav(page, 'Profile & settings')
  await page.getByRole('heading', { name: 'Your false-alarm reports' }).waitFor()
  page.once('dialog', dialog => dialog.accept())
  await page.getByRole('button', { name: 'Delete report' }).click()
  await page.getByText('No reports submitted.').waitFor()
  assert.equal((await fetch(apiOrigin + '/api/admin/false-alarms/' + reports[0].id + '/clip', { headers: { 'X-Review-Token': reviewToken } })).status, 404)
  report.studentClipDeletion = true
  await nav(page, 'Study session')
  await page.getByRole('button', { name: 'Start camera and timer' }).click()
  await page.getByRole('button', { name: 'Pause', exact: true }).waitFor()
  const beforeResume = await timer.innerText()
  await page.waitForFunction(previous => document.querySelector('[role="timer"]')?.textContent !== previous, beforeResume, { timeout: 5000 })
  await page.getByRole('button', { name: 'Pause', exact: true }).click()
  const manualPauseTime = await timer.innerText()
  await page.waitForTimeout(1200)
  assert.equal(await timer.innerText(), manualPauseTime)
  report.manualPause = true
  await page.evaluate(() => {
    window.__allowedGetUserMedia = navigator.mediaDevices.getUserMedia
    navigator.mediaDevices.getUserMedia = async () => { throw new DOMException('Denied for browser QA', 'NotAllowedError') }
  })
  await page.getByRole('button', { name: 'Start camera and timer' }).click()
  await page.getByText('Camera permission was denied. The study timer remains paused.').waitFor()
  assert.equal(await timer.innerText(), manualPauseTime)
  await page.evaluate(() => { navigator.mediaDevices.getUserMedia = window.__allowedGetUserMedia })
  report.permissionDenied = true
  await page.getByRole('button', { name: 'End session' }).click()
  await page.getByText('Open study block · ended').waitFor()
  await page.reload()
  await page.getByRole('heading', { name: 'Sign in' }).waitFor()
  assert.equal(await page.evaluate(() => window.__cameraCalls), 0)
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill('Browser-QA-password-123')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await nav(page, 'Study session')
  await page.getByText('Open study block · ended').waitFor()
  report.reload = true
  await page.route(apiOrigin + '/api/profile', route => route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"Database unavailable"}' }))
  await page.getByRole('button', { name: /Refresh/ }).click()
  await page.getByText('Database unavailable').waitFor()
  await page.unroute(apiOrigin + '/api/profile')
  await page.getByRole('button', { name: /Refresh/ }).click()
  await page.getByText('Browser QA · study workspace').waitFor()
  report.databaseFailure = true
  await page.route(apiOrigin + '/api/profile', route => route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"Invalid or expired token"}' }))
  await page.getByRole('button', { name: /Refresh/ }).click()
  await page.getByRole('heading', { name: 'Sign in' }).waitFor()
  await page.getByText('Your sign-in expired. Please sign in again.').waitFor()
  await page.unroute(apiOrigin + '/api/profile')
  report.errors = errors.filter(message => !['401 (Unauthorized)', '503 (Service Unavailable)'].some(expected => message.includes(expected)))
  assert.deepEqual(report.errors, [])
  console.log(JSON.stringify(report, null, 2))
  await context.close()
} finally {
  await browser?.close().catch(() => {})
  api.kill(); vite.kill()
  const cleanup = spawnSync('python', ['-c', 'import os; from pymongo import MongoClient; c=MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=3000); c.drop_database(os.environ["MONGO_DB"]); c.close()'], {
    cwd: backend, env: { ...process.env, MONGO_URI: mongoUri, MONGO_DB: database }, encoding: 'utf8', windowsHide: true,
  })
  if (cleanup.status !== 0) process.stderr.write(`QA database cleanup failed: ${cleanup.stderr}\n`)
  writeFileSync(path.join(qa, 'last-run.json'), JSON.stringify(report, null, 2))
}

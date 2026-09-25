// Mobile-first viewport check for VocabSwipe. See tests/ui/README.md.
//
// Drives headless Chromium through the public pages, the dashboard and the
// game at phone, tablet and desktop sizes. It fails on horizontal overflow,
// page scroll in the game, off-screen controls, broken swipe/keyboard/button
// answers, a missing finish screen, a menu that does not close, or console
// errors. Screenshots go to tests/ui/shots/ for a human look.
//
//   node tests/ui/viewport_check.js [320|375|390|430|tablet|desktop]

const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const env = process.env;
const OUT = env.SHOTS_DIR || path.join(__dirname, 'shots');
const BASE = env.BASE_URL || 'http://127.0.0.1:8123';
const BIG_LIST = env.BIG_LIST || '2';     // 60 words, owned by the demo user
const SMALL_LIST = env.SMALL_LIST || '3'; // 10 words, public
const USER = env.UI_USER || 'demo';
const PASS = env.UI_PASS || 'demo-pass-123';
// Any Chromium works: set CHROME_PATH, or let playwright-core use its own download.
const EXE = env.CHROME_PATH || undefined;

fs.mkdirSync(OUT, { recursive: true });

const sizes = [
  { name: '320', width: 320, height: 640, mobile: true },
  { name: '375', width: 375, height: 667, mobile: true },
  { name: '390', width: 390, height: 844, mobile: true },
  { name: '430', width: 430, height: 932, mobile: true },
  { name: 'tablet', width: 768, height: 1024, mobile: true },
  { name: 'desktop', width: 1280, height: 800, mobile: false },
];
const only = process.argv[2];

async function metrics(page) {
  return page.evaluate(() => ({
    hOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    vScroll: document.documentElement.scrollHeight - window.innerHeight,
  }));
}

(async () => {
  const browser = await chromium.launch(EXE ? { executablePath: EXE } : {});
  const problems = [];

  for (const s of sizes) {
    if (only && only !== s.name) continue;
    const ctx = await browser.newContext({
      viewport: { width: s.width, height: s.height },
      isMobile: s.mobile, hasTouch: s.mobile, deviceScaleFactor: 1,
    });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });

    // Public pages
    for (const [label, url] of [['home', '/'], ['explore', '/explore/'], ['login', '/login/'], ['signup', '/signup/']]) {
      await page.goto(BASE + url);
      const m = await metrics(page);
      if (m.hOverflow > 0) problems.push(`${s.name} ${label}: horizontal overflow ${m.hOverflow}px`);
      await page.screenshot({ path: `${OUT}/${s.name}-${label}.png`, fullPage: true });
    }

    // Guest game
    await page.goto(`${BASE}/game/?list_id=${SMALL_LIST}`);
    await page.waitForSelector('.vocab-card');
    await page.screenshot({ path: `${OUT}/${s.name}-guest-game.png` });

    // Log in and dashboard
    await page.goto(BASE + '/login/');
    await page.fill('input[name=username]', USER);
    await page.fill('input[name=password]', PASS);
    await page.click('button[type=submit].btn-primary');
    await page.waitForURL('**/dashboard/');
    let m = await metrics(page);
    if (m.hOverflow > 0) problems.push(`${s.name} dashboard: horizontal overflow ${m.hOverflow}px`);
    await page.screenshot({ path: `${OUT}/${s.name}-dashboard.png`, fullPage: true });
    await page.click('details.menu summary');
    await page.waitForTimeout(400);
    await page.screenshot({ path: `${OUT}/${s.name}-dashboard-menu.png` });
    await page.mouse.click(5, 300);
    if (await page.$('details.menu[open]')) problems.push(`${s.name}: list menu did not close on outside click`);

    // Game layout
    await page.goto(`${BASE}/game/?list_id=${BIG_LIST}`);
    await page.waitForSelector('.vocab-card');
    m = await metrics(page);
    if (m.hOverflow > 0 || m.vScroll > 0) problems.push(`${s.name} game: overflow h=${m.hOverflow} v=${m.vScroll}`);
    const box = await page.locator('.vocab-card:last-child').boundingBox();
    const ctrl = await page.locator('#game-controls').boundingBox();
    if (ctrl.y + ctrl.height > s.height + 1) problems.push(`${s.name} game: controls below the fold`);
    await page.screenshot({ path: `${OUT}/${s.name}-game.png` });

    // Swipe right: stamp shows mid-drag, release reveals and saves the answer
    const cx = box.x + box.width / 2, cy = box.y + box.height / 2;
    await page.mouse.move(cx, cy);
    await page.mouse.down();
    await page.mouse.move(cx + 70, cy + 10, { steps: 6 });
    await page.waitForTimeout(50);
    await page.screenshot({ path: `${OUT}/${s.name}-game-drag.png` });
    const statusReq = page.waitForRequest(r => r.url().includes('/status/') && r.method() === 'POST');
    await page.mouse.move(cx + 160, cy + 10, { steps: 4 });
    await page.mouse.up();
    await statusReq;
    await page.waitForTimeout(500);
    if (!await page.$('.vocab-card:last-child.is-revealed')) problems.push(`${s.name}: swipe did not reveal`);
    await page.screenshot({ path: `${OUT}/${s.name}-game-revealed.png` });

    // Next button, then keyboard answer and Space
    await page.click('#btn-next');
    await page.waitForTimeout(300);
    let prog = await page.textContent('#progress-text');
    if (!prog.startsWith('2 /')) problems.push(`${s.name}: Next button, progress ${prog}`);
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(100);
    await page.keyboard.press('Space');
    await page.waitForTimeout(300);
    prog = await page.textContent('#progress-text');
    if (!prog.startsWith('3 /')) problems.push(`${s.name}: keyboard, progress ${prog}`);

    // Buttons, and a double tap on Next must not skip a card
    await page.click('#btn-known');
    await page.click('#btn-next');
    await page.click('#btn-next').catch(() => {});
    await page.waitForTimeout(300);
    prog = await page.textContent('#progress-text');
    if (!prog.startsWith('4 /')) problems.push(`${s.name}: buttons/double tap, progress ${prog}`);
    const known = await page.textContent('#score-known');
    const review = await page.textContent('#score-unknown');
    if (known !== '2' || review !== '1') problems.push(`${s.name}: scores ${known}/${review}, expected 2/1`);

    // Timer mode, then finish the small deck with the buttons
    await page.goto(`${BASE}/game/?list_id=${SMALL_LIST}&mode=timer`);
    await page.waitForSelector('.vocab-card');
    await page.screenshot({ path: `${OUT}/${s.name}-game-timer.png` });
    const deckSize = parseInt((await page.textContent('#progress-text')).split('/')[1], 10);
    for (let i = 0; i < deckSize; i++) {
      await page.click(i % 3 ? '#btn-known' : '#btn-unknown');
      await page.click('#btn-next');
      await page.waitForTimeout(140);
    }
    await page.waitForSelector('#completion-screen:not(.hidden)', { timeout: 3000 })
      .catch(() => problems.push(`${s.name}: finish screen not shown`));
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${OUT}/${s.name}-game-done.png` });

    if (errors.length) problems.push(`${s.name}: console errors: ${errors.join(' | ')}`);
    await ctx.close();
  }

  await browser.close();
  console.log(problems.length ? problems.join('\n') : 'NO PROBLEMS');
  if (problems.length) process.exitCode = 1;
})().catch(e => { console.error(e); process.exit(1); });

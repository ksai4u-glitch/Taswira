/* Review quick fixes (18 Nov 2026): the phone opens in cinema view with a Chapters drawer, Zomo stays
   small in a corner on a phone, the state snapshots hold their own date, and names on the map do not
   collide. node tests/history_phone_cinema_browser.cjs <built HTML> <local dependency directory> */
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), { chromium } = require('playwright');
const [html, deps] = process.argv.slice(2);
if (!html || !deps) throw Error('Usage: node tests/history_phone_cinema_browser.cjs <built HTML> <local dependency directory>');

async function open(context, keepStorage) {
  const page = await context.newPage(), errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/*', r => {
    const u = r.request().url();
    const n = u.includes('leaflet.css') ? 'leaflet.css' : u.includes('leaflet.js') ? 'leaflet.js'
      : u.includes('d3-array') ? 'd3-array.js' : u.includes('d3-geo') ? 'd3-geo.js' : null;
    if (n) return r.fulfill({ contentType: n.endsWith('.css') ? 'text/css' : 'application/javascript', body: fs.readFileSync(path.join(deps, n)) });
    if (u.startsWith('https://taswira.test/')) return r.fulfill({ contentType: 'text/html', body: fs.readFileSync(html, 'utf8') });
    return r.abort();
  });
  if (!keepStorage) await page.addInitScript(() => { if (!sessionStorage.getItem('kept')) { localStorage.clear(); sessionStorage.setItem('kept', 1); } });
  await page.goto('https://taswira.test/history.html');
  await page.waitForFunction(() => window.taswira && state.drawn !== null);
  await page.evaluate(() => window.taswira.ready());
  await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
  return { page, errors };
}
// Shows a scene as it is near its end while playing
const playTo = (page, ch, sc, frac) => page.evaluate(([ch, sc, frac]) => {
  const ci = DATA.chapters.findIndex(c => c.id === ch), si = DATA.chapters[ci].scenes.findIndex(s => s.id === sc);
  goTo(ci, si, { live: true, animate: false }); state.t = lead() + scene().duration * frac;
  frame(performance.now()); return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
}, [ch, sc, frac]);
const boxesOf = (page, sel) => page.evaluate(sel => [...document.querySelectorAll(sel)].filter(el => {
  for (let n = el; n && n !== document.body; n = n.parentElement) {
    const cs = getComputedStyle(n);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < 0.05) return false;
  }
  return el.getClientRects().length;
}).map(el => { const r = el.getBoundingClientRect(); return { t: el.textContent.trim(), x: r.left, y: r.top, r: r.right, b: r.bottom }; }), sel);
const clashes = list => {
  const out = [];
  for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) {
    const a = list[i], b = list[j];
    if (Math.min(a.r, b.r) - Math.max(a.x, b.x) > 1 && Math.min(a.b, b.b) - Math.max(a.y, b.y) > 1) out.push(`${a.t} / ${b.t}`);
  }
  return out;
};

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
  try {
    // A phone opens in cinema view: no header of chapter buttons, Play and Chapters in the controls
    const phone = await browser.newContext({ viewport: { width: 390, height: 844 } });
    let { page, errors } = await open(phone);
    assert.ok(await page.evaluate(() => document.body.classList.contains('theatre-mode')), 'a phone opens in cinema view');
    assert.equal(await page.locator('header').isVisible(), false);
    assert.equal(await page.locator('#viewer-status').isVisible(), true, 'the draft label stays in view');
    assert.match(await page.locator('#viewer-status').textContent(), /Unreviewed draft/);
    assert.equal(await page.locator('#play').isVisible(), true);
    assert.equal(await page.locator('#chapters-open').isVisible(), true);
    assert.ok(await page.locator('#mapwrap').evaluate(el => el.clientHeight) > 550, 'the map fills most of the phone');
    // The controls keep to two rows: the scenes, then the buttons
    const rows = new Set(await page.locator('#controls > :visible').evaluateAll(els => els.map(el => Math.round(el.getBoundingClientRect().top))));
    assert.ok(rows.size <= 2, `controls take ${rows.size} rows`);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));

    // The drawer lists every chapter, marks the current one and jumps to the one picked
    await page.click('#chapters-open');
    assert.equal(await page.locator('#chapter-drawer').isVisible(), true);
    assert.equal(await page.locator('#drawer-list button').count(), await page.evaluate(() => DATA.chapters.length));
    assert.equal(await page.locator('#drawer-list button[aria-current="true"]').count(), 1);
    await page.locator('#drawer-list button', { hasText: 'Nok' }).click();
    assert.equal(await page.locator('#chapter-drawer').isVisible(), false);
    assert.equal(await page.evaluate(() => chapter().id), 'nok');
    assert.equal(await page.evaluate(() => document.body.classList.contains('theatre-mode')), true);
    await page.click('#chapters-open'); await page.click('#drawer-close');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'chapters-open');

    // Zomo is small and in the bottom corner of the map, beside the narration
    await playTo(page, 'hausa', 'kano-people', 0.5);
    const g = await page.locator('#story-guide').boundingBox(), m = await page.locator('#mapwrap').boundingBox();
    assert.ok(g.height <= 72, `Zomo is ${g.height}px tall on a phone`);
    assert.ok(m.x + m.width - (g.x + g.width) < 20 && m.y + m.height - (g.y + g.height) < 70, 'Zomo sits in the bottom right corner');
    assert.deepEqual(errors, []);

    // Leaving cinema on a phone is remembered
    await page.click('#cinema-toggle');
    assert.equal(await page.locator('header').isVisible(), true);
    await page.close();
    ({ page, errors } = await open(phone, true));
    assert.equal(await page.evaluate(() => document.body.classList.contains('theatre-mode')), false, 'a phone that left cinema stays out of it');
    await phone.close();

    // A desktop opens as before, with the chapters in the header
    const desk = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    ({ page, errors } = await open(desk));
    assert.equal(await page.evaluate(() => document.body.classList.contains('theatre-mode')), false);
    assert.equal(await page.locator('#chapters-open').isVisible(), false);
    await page.click('#cinema-toggle');
    assert.equal(await page.locator('#chapters-open').isVisible(), true, 'cinema on a desktop also has the drawer');
    await page.click('#cinema-toggle');

    // A state snapshot holds its own date: 1 October 1996 never runs on to a later year
    for (const frac of [0.3, 0.6, 0.95]) {
      await playTo(page, 'states', '1996', frac);
      assert.equal(await page.locator('#hud-year').textContent(), '1 October 1996');
    }
    await playTo(page, 'states', '1991', 0.9);
    assert.equal(await page.locator('#hud-year').textContent(), '27 August 1991');

    // Names do not collide: state names in 1996, and the conquest's dates and town names
    await playTo(page, 'states', '1996', 0.95);
    assert.deepEqual(clashes(await boxesOf(page, '.state-name:not(.old)')), [], 'state names collide');
    for (const [ctx, w, h] of [[desk, 1440, 900], [null, 390, 844]]) {
      let p = page;
      if (!ctx) { const c = await browser.newContext({ viewport: { width: w, height: h } }); ({ page: p } = await open(c)); }
      await playTo(p, 'sokoto', 'conquest', 0.98);
      const dates = await boxesOf(p, '.move-label.date:not(.hx-hidden) .lab-c');
      assert.ok(dates.length >= 4, `${w}px: conquest dates shown`);
      assert.deepEqual(clashes(dates), [], `${w}px: conquest dates collide`);
      const names = await boxesOf(p, '.site-label:not(.hx-crowded)');
      const mixed = clashes(dates.concat(names)).filter(c => !clashes(dates).includes(c));
      assert.deepEqual(mixed, [], `${w}px: a town name covers a date`);
    }
    assert.deepEqual(errors, []);
    console.log('PASS: phone opens in cinema with a Chapters drawer, small Zomo in the corner, snapshot dates held, names clear of each other.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });

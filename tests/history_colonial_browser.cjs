/* The colonial chapter in the real player: railways drawn when they open, trains on them, steamers
   leaving the ports, dated beats on the counter and a calm scene about conquest.
   node tests/history_colonial_browser.cjs <built HTML> <local dependency directory>

   While "Iron roads to the north" plays, each railway is hidden until its appear moment and fully
   drawn a few seconds later; a train runs only on a line already open. The ports show anchors and
   ships leave Port Harcourt for the sea. The conquest scene paints nothing on the effects canvas.
   The year shows each beat's date, ending on 1 October 1960. Seeking the 1920x1080 video twice
   gives identical pixels, and no page errors occur on a desktop or a phone. */
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), { chromium } = require('playwright');
const [html, deps] = process.argv.slice(2);
if (!html || !deps) throw Error('Usage: node tests/history_colonial_browser.cjs <built HTML> <local dependency directory>');

async function open(browser, viewport) {
  const page = await browser.newPage({ viewport }), errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/*', r => {
    const u = r.request().url();
    const n = u.includes('leaflet.css') ? 'leaflet.css' : u.includes('leaflet.js') ? 'leaflet.js'
      : u.includes('d3-array') ? 'd3-array.js' : u.includes('d3-geo') ? 'd3-geo.js' : null;
    if (n) return r.fulfill({ contentType: n.endsWith('.css') ? 'text/css' : 'application/javascript', body: fs.readFileSync(path.join(deps, n)) });
    return r.abort();
  });
  await page.addInitScript(() => { try { localStorage.clear(); } catch {} });
  await page.setContent(fs.readFileSync(html, 'utf8'));
  await page.waitForFunction(() => window.taswira && state.drawn !== null);
  await page.evaluate(() => window.taswira.ready());
  return { page, errors };
}
const go = (page, scene, live) => page.evaluate(([scene, live]) => {
  const c = DATA.chapters.findIndex(ch => ch.id === 'colonial'), s = DATA.chapters[c].scenes.findIndex(sc => sc.id === scene);
  setPlaying(false); goTo(c, s, { animate: false, live }); frame(performance.now());
}, [scene, live]);

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined, args: ['--no-sandbox'] });
  try {
    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      const { page, errors } = await open(browser, viewport);
      await go(page, 'rail-north', true);
      const drawing = await page.evaluate(() => {
        const at = t => { state.t = lead() + t; frame(performance.now());
          return fx.draws.filter(d => d.el.classList.contains('hx-rail')).map(d => d.el.classList.contains('hx-hidden') ? 0 : (d.el.style.strokeDashoffset === '' ? 1 : 0.5)); };
        const rails = fx.rails.map(r => r.at);
        return { before: at(2.0), early: at(7.0), later: at(14.0), end: at(35), rails, years: [1, 9, 17, 24].map(t => { state.t = lead() + t; frame(performance.now()); return $('hud-year').textContent; }) };
      });
      // three layers per railway, three railways in the scene
      assert.equal(drawing.before.length, 9);
      assert.deepEqual(drawing.before, Array(9).fill(0), 'no railway before it opens');
      assert.deepEqual(drawing.early.slice(0, 3), [1, 1, 1], 'Lagos to Ibadan drawn by 7 s');
      assert.deepEqual(drawing.early.slice(3), Array(6).fill(0), 'the northern lines are not yet open');
      assert.deepEqual(drawing.end, Array(9).fill(1), 'every line drawn by the end');
      assert.equal(drawing.rails.length, 3, 'a train for each line, once it is open');
      assert.deepEqual(drawing.years, ['1896 to 1901', '1907 to 1911', '1911 and 1912', '1911 or 1916 · sources differ']);

      // Ports: anchors, and ships leaving Port Harcourt
      await go(page, 'coal-port', false);
      const port = await page.evaluate(() => ({ anchors: document.querySelectorAll('.hx-mark svg circle[cy="-5"]').length,
        ships: fx.points.filter(p => p.seaward).map(p => p.id) }));
      assert.equal(port.anchors, 1);
      assert.deepEqual(port.ships, ['port-harcourt']);

      // Conquest stays calm: nothing on the effects canvas
      await go(page, 'resistance', true);
      const calm = await page.evaluate(() => { state.t = lead() + 6; frame(performance.now()); paint(performance.now());
        const cv = document.querySelector('#fx'), d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
        let lit = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) lit++; return lit; });
      assert.equal(calm, 0, 'no effects over the conquest scene');
      assert.deepEqual(errors, [], `no page errors at ${viewport.width}px`);
      await page.close();
    }

    const { page, errors } = await open(browser, { width: 1920, height: 1080 });
    const shot = async (scene, t) => { await page.evaluate(([s, t]) => taswira.seek('colonial', s, t), [scene, t]); await page.waitForTimeout(150); return page.screenshot(); };
    assert.ok((await shot('network', 20)).equals(await shot('network', 20)), 'seeking twice gives identical pixels, trains included');
    const train = await page.evaluate(() => {
      const cv = document.querySelector('#fx'), d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
      let warm = 0; for (let i = 0; i < d.length; i += 4) if (d[i + 3] > 60 && d[i] > 180 && d[i + 1] > 150) warm++; return warm; });
    assert.ok(train > 200, `trains and lamps on the open lines (${train} bright pixels)`);
    const end = await page.evaluate(() => { taswira.seek('colonial', 'network', 33); return $('hud-year').textContent; });
    assert.equal(end, '1 October 1960');
    assert.deepEqual(errors, [], 'no page errors in the video');
    console.log('PASS: railways hidden until they open and drawn by the end, a train on each open line, dated beats with the Jebba dispute, an anchor and steamers at Port Harcourt, a calm conquest scene, exact repeat frames, ending on 1 October 1960.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });

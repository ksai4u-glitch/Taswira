/* The civil-war chapter in the real player.
   node tests/history_civil_war_browser.cjs <built HTML> <local dependency directory>

   The scenes about coups, killings, war, hunger and the aftermath paint nothing on the effects
   canvas at any moment, and their places appear without the pop and rise animation. The year
   shows each beat's own date. Places appear at their dated moments, and a taken capital goes
   faint. Seeking the 1920x1080 video twice gives identical pixels, and no page errors occur on
   a desktop or a phone. */
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), { chromium } = require('playwright');
const [html, deps] = process.argv.slice(2);
if (!html || !deps) throw Error('Usage: node tests/history_civil_war_browser.cjs <built HTML> <local dependency directory>');

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

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined, args: ['--no-sandbox'] });
  try {
    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      const { page, errors } = await open(browser, viewport);
      const result = await page.evaluate(() => {
        const c = DATA.chapters.findIndex(ch => ch.id === 'civil-war'), out = {};
        for (const sid of ['crisis', 'war', 'blockade', 'end']) {
          const s = DATA.chapters[c].scenes.findIndex(sc => sc.id === sid);
          setPlaying(false); goTo(c, s, { animate: false, live: true });
          let lit = 0, pops = 0; const years = [];
          for (const b of scene().beats) {
            for (const dt of [0.2, 1.5]) {
              state.t = lead() + b.at + dt; frame(performance.now()); paint(performance.now());
              const cv = document.querySelector('#fx'), d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
              for (let i = 3; i < d.length; i += 4) if (d[i] > 0) lit++;
              pops += document.querySelectorAll('#map .hx-pop, #map .hx-rise').length;
            }
            years.push($('hud-year').textContent);
          }
          out[sid] = { lit, pops, years };
        }
        // Enugu goes faint after it is taken; Asaba is not on the map before its beat
        const s = DATA.chapters[c].scenes.findIndex(sc => sc.id === 'war');
        setPlaying(false); goTo(c, s, { animate: false, live: true });
        const pt = id => fx.points.find(p => p.id === id);
        state.t = lead() + 10; frame(performance.now());
        out.asabaEarly = pt('asaba').els.every(el => el.classList.contains('hx-hidden'));
        state.t = lead() + 22; frame(performance.now());
        out.enuguFaint = parseFloat(pt('enugu').els[0].style.opacity || '1') < 0.9;
        return out;
      });
      for (const sid of ['crisis', 'war', 'blockade', 'end']) {
        assert.equal(result[sid].lit, 0, `${sid}: nothing painted on the effects canvas`);
        assert.equal(result[sid].pops, 0, `${sid}: no pop or rise animations`);
      }
      assert.deepEqual(result.war.years, ['6 to 14 July 1967', 'August to 22 September 1967', '4 October 1967',
        '5 to 7 October 1967', '17 October 1967 to 19 May 1968']);
      assert.equal(result.end.years[1], '15 January 1970');
      assert.ok(result.asabaEarly, 'Asaba is not on the map before its beat');
      assert.ok(result.enuguFaint, 'Enugu goes faint once it is taken');
      assert.deepEqual(errors, [], `no page errors at ${viewport.width}px`);
      await page.close();
    }
    const { page, errors } = await open(browser, { width: 1920, height: 1080 });
    const shot = async t => { await page.evaluate(t => taswira.seek('civil-war', 'blockade', t), t); await page.waitForTimeout(150); return page.screenshot(); };
    assert.ok((await shot(20)).equals(await shot(20)), 'seeking twice gives identical pixels');
    assert.deepEqual(errors, [], 'no page errors in the video');
    console.log('PASS: no effects or pop animations over the crisis, war, blockade and aftermath, dated beats on the counter, Asaba and Enugu at their dates, exact repeat frames, no page errors.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });

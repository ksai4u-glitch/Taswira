/* The deep-time additions in the real player: Africa's volcanoes, the birth of the Sahara, the
   green Sahara's lake, moving water on the rivers and places lighting up as they are named.
   node tests/history_deep_fire_browser.cjs <built HTML> <local dependency directory>

   Jumped to, the volcano scene shows five volcano cones with their names. While it plays, the
   year shows each beat's own date, the places named in the narration light up (one entry per
   named volcano), and the erupting volcanoes throw embers at their dated moments. Seeking the
   1920x1080 video twice to the same moment gives identical pixels. In the green Sahara, Lake
   Mega-Chad grows with the rains and shrinks as they fail. The rivers on the historical
   background are loaded for moving water, and no page errors occur on a desktop or a phone. */
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), { chromium } = require('playwright');
const [html, deps] = process.argv.slice(2);
if (!html || !deps) throw Error('Usage: node tests/history_deep_fire_browser.cjs <built HTML> <local dependency directory>');

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
      // Jumped to: every volcano is on the map as a cone with its name
      const jumped = await page.evaluate(() => {
        const c = DATA.chapters.findIndex(ch => ch.id === 'deep'), s = DATA.chapters[c].scenes.findIndex(sc => sc.id === 'fire-below');
        setPlaying(false); goTo(c, s, { animate: false }); frame(performance.now());
        const labels = [...document.querySelectorAll('.site-label')].filter(l => !l.closest('.hx-hidden')).map(l => l.textContent);
        return { cones: document.querySelectorAll('.hx-mark svg path[d^="M-11 9"]').length, labels, year: $('hud-year').textContent,
                 mentions: fx.mentions.map(m => m.id), rivers: flowRivers.length };
      });
      assert.equal(jumped.cones, 5, 'five volcano cones');
      for (const name of ['Biu Plateau', 'Mount Cameroon', 'Ethiopian', 'Kilimanjaro', 'Nyiragongo'])
        assert.ok(jumped.labels.some(l => l.includes(name)), `${name} is labelled`);
      assert.equal(jumped.year, 'about 66 million years ago to today', 'a jumped-to scene shows its whole date label');
      for (const id of ['biu-plateau', 'mount-cameroon', 'ethiopian-traps', 'kilimanjaro', 'nyiragongo'])
        assert.ok(jumped.mentions.includes(id), `${id} lights up when the narration names it`);
      assert.ok(jumped.rivers > 50, 'the larger rivers are loaded for moving water');

      // Playing: each beat shows its own date; a place named before it appears waits for it
      const playing = await page.evaluate(() => {
        const out = [];
        for (const t of [1, 5, 12, 18, 23]) {
          setPlaying(false); state.t = lead() + t; setPlaying(true); setPlaying(false);
          frame(performance.now()); out.push($('hud-year').textContent);
        }
        const mc = fx.mentions.find(m => m.id === 'mount-cameroon'), appear = scene().appear['mount-cameroon'];
        return { years: out, mcAfterAppear: mc.at > appear };
      });
      assert.deepEqual(playing.years, ['about 66 million years ago to today', 'from about 66 or about 30 million years ago: sources differ',
        'about 31 to 29 million years ago', 'about 2.5 million years ago', '1999 to 2021']);
      assert.ok(playing.mcAfterAppear, 'a mention waits until its place is on the map');

      // The green Sahara's lake: small, then large with the rains, then small again
      const lake = await page.evaluate(() => {
        const c = DATA.chapters.findIndex(ch => ch.id === 'deep'), s = DATA.chapters[c].scenes.findIndex(sc => sc.id === 'green-sahara');
        setPlaying(false); goTo(c, s, { animate: false, live: true });
        const r = t => { state.t = lead() + t; frame(performance.now()); return Math.round(fx.lakes[0].area.getRadius() / 1000); };
        const d = scene().duration;
        return [r(0.2), r(d * 0.5), r(d - 0.2)];
      });
      assert.ok(lake[1] > lake[0] * 3 && lake[1] > lake[2] * 3, `Lake Mega-Chad grows and shrinks (${lake.join(' → ')} km)`);
      assert.deepEqual(errors, [], `no page errors at ${viewport.width}px`);
      await page.close();
    }

    // In the video, an eruption frame is identical when sought twice, and it is bright at the volcano
    const { page, errors } = await open(browser, { width: 1920, height: 1080 });
    const shot = async t => { await page.evaluate(t => taswira.seek('deep', 'fire-below', t), t); await page.waitForTimeout(150); return page.screenshot(); };
    const a = await shot(10.1), b = await shot(10.1);
    assert.ok(a.equals(b), 'seeking twice to an eruption gives identical pixels');
    const embers = await page.evaluate(() => {
      const ll = DATA.chapters.find(c => c.id === 'deep').features['mount-cameroon'].coordinates;
      const p = map.latLngToContainerPoint(ll), cv = document.querySelector('#fx'), d = window.devicePixelRatio || 1;
      const data = cv.getContext('2d').getImageData((p.x - 40) * d, (p.y - 90) * d, 80 * d, 90 * d).data;
      let warm = 0;
      for (let i = 0; i < data.length; i += 4) if (data[i + 3] > 40 && data[i] > 180 && data[i] > data[i + 2] + 60) warm++;
      return warm;
    });
    assert.ok(embers > 150, `embers and glow above Mount Cameroon while it erupts (${embers} warm pixels)`);
    await page.evaluate(() => taswira.seek('deep', 'sahara-born', 12));
    await page.evaluate(() => taswira.seek('deep', 'green-sahara', 20));
    assert.deepEqual(errors, [], 'no page errors in the video');
    console.log('PASS: volcano cones and names, dated beats on the counter, named places lighting up, eruption embers with exact repeat frames, Lake Mega-Chad growing and shrinking, river water loaded, no page errors.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });

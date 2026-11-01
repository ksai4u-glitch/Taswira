/* The Kanem-Bornu chapter in the real player.
   node tests/history_kanem_browser.cjs <built HTML> <local dependency directory>

   Every scene, jumped to, shows its full date label. While a scene plays, each place waits for its
   "appear" moment and a faded place (Kanem after the move west, Ngazargamu after 1808) goes faint.
   Scenes whose narrated dates jump show their date label while playing, not a rolling year.
   The scenes about war and death draw no celebratory canvas effects. On a desktop and a phone,
   playing and with reduced motion, there are no page errors. In the 1920×1080 video, place names
   stay clear of the caption, caution, credit and bars, and seeking twice gives identical pixels. */
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), { chromium } = require('playwright');
const [html, deps] = process.argv.slice(2);
if (!html || !deps) throw Error('Usage: node tests/history_kanem_browser.cjs <built HTML> <local dependency directory>');

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

const SETUP = `
  var C = DATA.chapters.findIndex(ch => ch.id === 'kanem'), CH = DATA.chapters[C], F = CH.features;
  var box = e => { const q = e.getBoundingClientRect(); return { x: q.left, y: q.top, r: q.right, b: q.bottom }; };
  var hit = (a, b) => Math.min(a.r, b.r) - Math.max(a.x, b.x) > 1 && Math.min(a.b, b.b) - Math.max(a.y, b.y) > 1;
  var seen = e => !e.classList.contains('hx-hidden') && !e.classList.contains('hx-crowded') && getComputedStyle(e).visibility !== 'hidden';
`;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
  try {
    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      const { page, errors } = await open(browser, viewport);
      const where0 = `${viewport.width}px`;
      await page.evaluate(SETUP);
      const order = await page.evaluate(() => DATA.chapters.map(c => c.id));
      assert.ok(order.indexOf('nok') < order.indexOf('kanem') && order.indexOf('kanem') < order.indexOf('hausa'), `${where0}: Kanem-Bornu sits between Nok and the Hausa cities`);
      const run = await page.evaluate(() => CH.scenes.map((SC, S) => {
        setPlaying(false); goTo(C, S, { animate: false });
        const jumped = { hud: $('hud-year').textContent, want: SC.when.label };
        goTo(C, S, { animate: false, live: true });
        const places = SC.show.filter(id => F[id].kind === 'point');
        const steps = [];
        for (let t = 0; t <= SC.duration - 0.05; t += 0.5) {
          setPlaying(true); state.t = lead() + t; setPlaying(false);
          frame(performance.now());
          const hidden = Object.fromEntries(places.map((id, i) => [id, fx.points[i].els.every(el => el.classList.contains('hx-hidden'))]));
          const faded = fx.fades.map(f => +(f.els[0].style.opacity || 1));
          steps.push({ t, hidden, faded, hud: $('hud-year').textContent });
        }
        const calm = SC.sensitive ? paint(performance.now()) === false : true;
        return { id: SC.id, jumped, label: SC.clock === 'label' ? SC.when.label : null, appear: SC.appear || {}, fade: SC.fade || {}, steps, calm };
      }));
      for (const sc of run) {
        const where = `${where0} ${sc.id}`;
        assert.equal(sc.jumped.hud, sc.jumped.want, `${where}: a jumped-to scene shows its date label`);
        assert.ok(sc.calm, `${where}: a sensitive scene draws no celebratory effects`);
        for (const f of sc.steps) {
          if (sc.label) assert.equal(f.hud, sc.label, `${where} t=${f.t}: a label-clock scene shows its label, not a rolling year`);
          for (const [id, at] of Object.entries(sc.appear)) assert.equal(f.hidden[id], f.t < at, `${where} t=${f.t}: ${id} appears at ${at} s`);
          Object.values(sc.fade).forEach((at, i) => assert.ok(f.t < at ? f.faded[i] === 1 : f.t < at + 0.8 || f.faded[i] < 0.6,
            `${where} t=${f.t}: a place fades after ${at} s (${f.faded[i]})`));
        }
      }
      assert.ok(run.some(sc => Object.keys(sc.fade).length), `${where0}: some place fades`);
      await page.emulateMedia({ reducedMotion: 'reduce' });
      const reduced = await page.evaluate(() => CH.scenes.map((SC, S) => { goTo(C, S, { animate: false }); return $('hud-year').textContent === SC.when.label; }));
      assert.ok(reduced.every(Boolean), `${where0}: reduced motion shows every scene complete`);
      assert.deepEqual(errors, [], `page errors at ${where0}`);
      await page.close();
    }

    // The 1920×1080 video
    const { page, errors } = await open(browser, { width: 1920, height: 1080 });
    await page.evaluate(SETUP);
    const settle = () => page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
    const scenes = await page.evaluate(() => CH.scenes.map(s => [s.id, s.duration]));
    const found = [];
    let named = 0;
    for (const [id, duration] of scenes) {
      for (let t = 3; t < duration; t += 3) {
        await page.evaluate(([id, t]) => taswira.seek('kanem', id, t), [id, t]);
        await settle();
        const r = await page.evaluate(([id, t]) => {
          document.getAnimations().forEach(a => { try { a.finish(); } catch {} });
          const wrap = box(map.getContainer());
          const bars = [...document.querySelectorAll('.lb, #video-caption, #video-caution, #video-credit, #video-tools, #exit-video')]
            .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden' && !e.hidden).map(e => ({ id: e.id || e.className, ...box(e) }));
          const things = [...document.querySelectorAll('.site-label, .town-label')].filter(seen).map(e => ({ name: e.textContent, ...box(e) }));
          const out = [];
          for (const q of things) {
            if (q.x < wrap.x || q.r > wrap.r || q.y < wrap.y || q.b > wrap.b) out.push(`${id} t=${t}: ${q.name} is cut by the frame`);
            for (const b of bars) if (hit(q, b)) out.push(`${id} t=${t}: ${q.name} is under ${b.id}`);
          }
          return { out, n: things.length };
        }, [id, t]);
        found.push(...r.out);
        named += r.n;
      }
    }
    assert.ok(named > 50, `video: names should be on screen (${named})`);
    assert.deepEqual(found, [], 'video: names stay clear of the overlays');
    const shot = async (id, t) => { await page.evaluate(([id, t]) => taswira.seek('kanem', id, t), [id, t]); await settle(); return page.locator('#mapwrap').screenshot(); };
    for (const [id, t] of [['kanem-east', 20], ['bornu', 31], ['sayfawa-end', 15]]) {
      const a = await shot(id, t); await shot('sayfawa', 5); assert.ok(a.equals(await shot(id, t)), `video: seeking to ${id} ${t} s twice must give identical pixels`);
    }
    await page.evaluate(() => taswira.exitVideo());
    assert.deepEqual(errors, [], 'page errors in the video');
    await page.close();
  } finally { await browser.close(); }
  console.log('PASS: Kanem-Bornu: chapter order, date labels, places at their moments, fades, calm sensitive scenes, reduced motion, names clear of the video overlays, exact repeat frames.');
})().catch(e => { console.error(e); process.exitCode = 1; });

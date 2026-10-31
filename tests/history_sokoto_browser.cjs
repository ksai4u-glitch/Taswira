/* The Sokoto Caliphate chapter: the jihad, the emirates and the conquest of 1903.
   node tests/history_sokoto_browser.cjs <built HTML> <local dependency directory>

   In the jihad and emirates scenes, played in quarter seconds on a desktop (Cinema and normal) and a
   phone, the year counter shows each beat's own label, each place and allegiance tie waits for its
   moment, each note shows only in its window, and Alkalawa goes faint only after it falls. In the
   conquest scene each town stays hatched (claimed on paper) until the campaign's dated stop reaches
   it, then turns solid, and the counter shows that stop's year. No celebratory effects are drawn over
   these scenes. In the 1920×1080 video, names and notes stay clear of the caption, caution, credit
   and bars once the camera has settled, and seeking twice gives identical pixels. */
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), { chromium } = require('playwright');
const [html, deps] = process.argv.slice(2);
if (!html || !deps) throw Error('Usage: node tests/history_sokoto_browser.cjs <built HTML> <local dependency directory>');

async function open(browser, viewport, mode) {
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
  if (mode !== 'normal') await page.click(`#${mode}-toggle`);
  return { page, errors };
}

const SETUP = `
  var C = DATA.chapters.findIndex(ch => ch.id === 'sokoto'), F = DATA.chapters[C].features;
  var pick = id => { const sc = DATA.chapters[C].scenes.find(s => s.id === id); return { sc, s: DATA.chapters[C].scenes.indexOf(sc) }; };
  var still = (sc, t) => (sc.camera_path || []).every(c => t < c.at || t > c.at + c.dur + 0.2) && t > 1.5;
  var box = e => { const q = e.getBoundingClientRect(); return { x: q.left, y: q.top, r: q.right, b: q.bottom }; };
  var hit = (a, b) => Math.min(a.r, b.r) - Math.max(a.x, b.x) > 1 && Math.min(a.b, b.b) - Math.max(a.y, b.y) > 1;
  var seen = e => !e.classList.contains('hx-hidden') && !e.classList.contains('hx-crowded') && getComputedStyle(e).visibility !== 'hidden';
`;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
  try {
    for (const [viewport, mode] of [[{ width: 1440, height: 900 }, 'cinema'], [{ width: 1440, height: 900 }, 'normal'], [{ width: 390, height: 844 }, 'normal']]) {
      const { page, errors } = await open(browser, viewport, mode);
      const where0 = `${viewport.width}px ${mode}`;
      await page.evaluate(SETUP);
      assert.deepEqual(await page.evaluate(() => DATA.chapters.map(c => c.id).slice(3, 6)), ['hausa', 'sokoto', 'states']);
      for (const id of ['jihad', 'emirates']) {
        const run = await page.evaluate(id => {
          const { sc, s } = pick(id);
          const places = sc.show.filter(f => F[f].kind === 'point');
          const notes = () => fx.labels.filter(l => l.el.classList.contains('note-label'));
          setPlaying(false); goTo(C, s, { animate: false, live: true });
          const out = [];
          let celebrated = false;
          for (let t = 0; t <= sc.duration - 0.05; t += 0.25) {
            setPlaying(true); state.t = lead() + t; setPlaying(false);
            const cam = captureCamera(t); map.setView(cam.center, cam.zoom, { animate: false });
            frame(performance.now());
            celebrated = celebrated || paint(performance.now()) !== false;
            const beat = directedBeat(sc, t).beat;
            const hidden = Object.fromEntries(places.map((p, i) => [p, fx.points[i].els.every(el => el.classList.contains('hx-hidden'))]));
            for (const d of fx.draws) if (d.id) hidden[d.id] = d.el.classList.contains('hx-hidden');
            const shown = notes().map(l => !l.el.classList.contains('hx-hidden'));
            const faded = fx.fades.map((f, i) => ({ id: Object.keys(sc.fade || {})[i], op: +(f.els[0].style.opacity || 1) }));
            out.push({ t, hud: $('hud-year').textContent, when: beat.when, hidden, shown, faded });
          }
          return { out, appear: sc.appear, notes: sc.notes, fade: sc.fade || {}, celebrated, sensitive: $('mapwrap').dataset.sensitive };
        }, id);
        assert.equal(run.sensitive, 'true', `${where0} ${id}: the scene is marked sensitive`);
        assert.equal(run.celebrated, false, `${where0} ${id}: no celebratory canvas effects over the jihad`);
        for (const f of run.out) {
          const where = `${where0} ${id} t=${f.t}`;
          assert.equal(f.hud, f.when.label, `${where}: the counter must show the beat's own label`);
          for (const [fid, at] of Object.entries(run.appear)) if (Math.abs(f.t - at) > 0.01) assert.equal(f.hidden[fid], f.t < at, `${where}: ${fid} appears at ${at} s`);
          run.notes.forEach((n, i) => Math.min(Math.abs(f.t - n.at), Math.abs(f.t - n.until)) > 0.01 && assert.equal(f.shown[i], f.t >= n.at && f.t < n.until, `${where}: note "${n.text}" shows from ${n.at} to ${n.until} s`));
          for (const [fid, at] of Object.entries(run.fade)) {
            const op = (f.faded.find(x => x.id === fid) || { op: 1 }).op;
            assert.ok(f.t < at ? op === 1 : f.t < at + 0.8 || Math.abs(op - 0.45) < 0.01, `${where}: ${fid} fades after ${at} s (${op})`);
          }
        }
      }

      // The conquest: hatched on paper until the dated stop, then solid
      const conquest = await page.evaluate(() => {
        const { sc, s } = pick('conquest');
        setPlaying(false); goTo(C, s, { animate: false, live: true });
        const clock = sc.campaign_clock, out = [];
        for (const [fid, stops] of Object.entries(clock.campaigns)) for (const stop of stops) {
          state.t = lead() + stop.at - 0.3; frame(performance.now());
          const f = fx.flips.find(x => x.id === stop.id);
          const before = !f.held.classList.contains('hx-hidden');
          state.t = lead() + stop.at + 0.05; frame(performance.now());
          out.push({ id: stop.id, campaign: fid, before, after: !f.held.classList.contains('hx-hidden'), year: state.shownYear, want: stop.year,
                     hud: $('hud-year').textContent, celebrated: paint(performance.now()) !== false });
        }
        return { out, flips: fx.flips.length };
      });
      assert.equal(conquest.flips, 5, `${where0}: five towns change hands`);
      for (const c of conquest.out) {
        assert.equal(c.before, false, `${where0}: ${c.id} is still on paper just before its stop`);
        assert.equal(c.after, true, `${where0}: ${c.id} turns solid at its stop`);
        assert.equal(c.hud, String(Math.floor(c.want)), `${where0}: the counter shows ${c.id}'s year`);
        assert.equal(c.celebrated, false, `${where0}: no victory glow at ${c.id}`);
      }
      assert.deepEqual(errors, [], `page errors at ${where0}`);
      await page.close();
    }

    // The 1920×1080 video
    const { page, errors } = await open(browser, { width: 1920, height: 1080 }, 'normal');
    await page.evaluate(SETUP);
    const settle = () => page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
    const found = [];
    let named = 0, moments = 0;
    for (const id of ['jihad', 'emirates', 'conquest']) {
      const times = await page.evaluate(id => { const { sc } = pick(id); const ts = []; for (let t = 2; t < sc.duration; t += 1) if (still(sc, t)) ts.push(t); return ts; }, id);
      moments += times.length;
      for (const t of times) {
        await page.evaluate(([id, t]) => taswira.seek('sokoto', id, t), [id, t]);
        await settle();
        const r = await page.evaluate(([id, t]) => {
          document.getAnimations().forEach(a => { try { a.finish(); } catch {} });
          const wrap = box(map.getContainer());
          const bars = [...document.querySelectorAll('.lb, #video-caption, #video-caution, #video-credit, #video-tools, #exit-video')]
            .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden' && !e.hidden).map(e => ({ id: e.id || e.className, ...box(e) }));
          const things = [...document.querySelectorAll('.town-label, .site-label')].filter(seen).map(e => ({ name: e.textContent, ...box(e) }))
            .concat([...document.querySelectorAll('.note-label:not(.hx-hidden) .lab-c')].map(e => ({ name: `note "${e.textContent}"`, ...box(e) })));
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
    assert.ok(moments > 60 && named > 200, `video: names should be on screen (${moments} moments, ${named} names)`);
    assert.deepEqual(found, [], 'video: names and notes stay clear of the overlays');
    const shot = async (id, t) => { await page.evaluate(([id, t]) => taswira.seek('sokoto', id, t), [id, t]); await settle(); return page.locator('#mapwrap').screenshot(); };
    for (const [id, t] of [['jihad', 5], ['jihad', 47], ['emirates', 27], ['conquest', 30]]) {
      const a = await shot(id, t); await shot('emirates', 9); assert.ok(a.equals(await shot(id, t)), `video: seeking to ${id} ${t} s twice must give identical pixels`);
    }
    await page.evaluate(() => taswira.exitVideo());
    assert.deepEqual(errors, [], 'page errors in the video');
    await page.close();
  } finally { await browser.close(); }
  console.log('PASS: Sokoto: beat labels on the counter, places, ties and notes at their moments, Alkalawa faint after its fall, towns solid only at their dated stops, no celebratory effects, names clear of the video overlays, exact repeat frames.');
})().catch(e => { console.error(e); process.exitCode = 1; });

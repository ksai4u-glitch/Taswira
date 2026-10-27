/* The Kano scene: a city that grows part by part, each part at its own date.
   node tests/history_kano_browser.cjs <built HTML> <local dependency directory>

   While the scene plays, the year counter shows each beat's own date and what it rests on, and no
   part of the city is visible while the counter shows an earlier date than the part's. Oral
   tradition shows only under an undated label and leaves before the next dated beat. Jumped to,
   the scene shows the finished city without the oral-tradition frame or the disputed dashed line.
   Far out, the city becomes its small glyph, and Katsina joins it only for the pull-back. On a
   desktop, a short laptop and a phone, the city's own names are never drawn under the buttons, notes,
   year, caption, guide or the city's name plate, and never cut by the map's edge. */
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), { chromium } = require('playwright');
const [html, deps] = process.argv.slice(2);
if (!html || !deps) throw Error('Usage: node tests/history_kano_browser.cjs <built HTML> <local dependency directory>');

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

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
  try {
    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      const { page, errors } = await open(browser, viewport, 'cinema');

      const timeline = await page.evaluate(() => {
        const c = DATA.chapters.findIndex(ch => ch.id === 'hausa'), sc = DATA.chapters[c].scenes.find(s => s.id === 'kano');
        const s = DATA.chapters[c].scenes.indexOf(sc), city = DATA.chapters[c].features['kano-city'];
        const parts = Object.fromEntries(city.monument.parts.map(p => [p.id, p]));
        setPlaying(false); goTo(c, s, { animate: false, live: true });
        const out = [];
        for (let t = 0; t <= sc.duration - 0.05; t += 0.25) {
          setPlaying(true); state.t = lead() + t; setPlaying(false);
          const cam = captureCamera(t); map.setView(cam.center, cam.zoom, { animate: false });   // the camera at this moment
          frame(performance.now());
          const beat = directedBeat(sc, t).beat;
          const shown = [...document.querySelectorAll('.hx-assemblage:not(.hx-glyph) [data-set-part]')]
            .filter(el => parts[el.dataset.setPart] && +el.style.opacity > 0.01).map(el => el.dataset.setPart);
          const katsina = fx.points[1].els.every(el => el.classList.contains('hx-hidden'));
          out.push({ t, hud: $('hud-year').textContent, when: beat.when, shown, glyph: !!document.querySelector('.hx-assemblage.hx-glyph'), katsinaHidden: katsina });
        }
        goTo(c, s, { animate: false });
        frame(performance.now());
        const done = [...document.querySelectorAll('.hx-assemblage [data-set-part]')].map(el => ({ id: el.dataset.setPart, o: +el.style.opacity }));
        return { out, parts, done, hudDone: $('hud-year').textContent, label: sc.when.label, appear: sc.appear.katsina };
      });

      const { out, parts } = timeline;
      let before = [];
      for (const f of out) {
        const where = `${viewport.width}px t=${f.t}`;
        assert.equal(f.hud, f.when.label, `${where}: the counter must show the beat's own dated label`);
        for (const id of f.shown) {
          const p = parts[id];
          if (p.natural) continue;
          if (p.oral) assert.equal(f.when.basis, 'oral', `${where}: oral tradition ${id} shows under a dated label`);
          // Under an undated tradition the earlier city stays, but nothing dated arrives
          else if (f.when.basis === 'oral') assert.ok(before.includes(id), `${where}: ${id} arrives under an undated tradition`);
          else assert.ok(f.when.from >= p.year, `${where}: ${id} (${p.year}) shows under "${f.hud}"`);
        }
        before = f.shown;
        if (f.when.basis === 'oral') assert.doesNotMatch(f.hud, /\d/, `${where}: oral tradition must carry no date`);
        assert.equal(f.katsinaHidden, f.t < timeline.appear, `${where}: Katsina joins only for the pull-back`);
      }
      // Each part appears in its turn, and the finished city has every part but the passing ones
      for (const p of Object.values(parts)) {
        assert.ok(out.some(f => f.shown.includes(p.id)), `${viewport.width}px: ${p.id} never appears while playing`);
      }
      for (const d of timeline.done) {
        const p = parts[d.id] || parts[d.id.replace(/-names$/, '')];
        assert.equal(d.o, p.until != null ? 0 : 1, `${viewport.width}px: finished city, ${d.id}`);
      }
      assert.equal(timeline.hudDone, timeline.label, 'A jumped-to scene shows the whole scene label');
      assert.ok(out.at(-1).glyph && !out.find(f => f.t < 39.4).glyph, 'The city becomes its glyph only in the pull-back');

      // Exact repeat frames on the export clock
      await page.click('#cinema-toggle');
      const shot = async t => { await page.evaluate(t => taswira.seek('hausa', 'kano', t), t); await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))); return page.locator('#mapwrap').screenshot(); };
      for (const t of [12, 27.5, 37]) {
        const a = await shot(t); await shot(4); assert.ok(a.equals(await shot(t)), `${viewport.width}px: seeking to ${t} s twice must give identical pixels`);
      }
      await page.evaluate(() => taswira.exitVideo());
      assert.deepEqual(errors, [], `page errors at ${viewport.width}px`);
      await page.close();
    }

    // The city's names stay whole wherever they are drawn
    for (const [viewport, mode] of [[{ width: 1440, height: 900 }, 'cinema'], [{ width: 1024, height: 700 }, 'details'], [{ width: 390, height: 844 }, 'normal']]) {
      const { page, errors } = await open(browser, viewport, mode);
      const found = await page.evaluate(() => {
        const c = DATA.chapters.findIndex(ch => ch.id === 'hausa'), sc = DATA.chapters[c].scenes.find(s => s.id === 'kano');
        const edge = e => { const q = e.getBoundingClientRect(); return { x: q.left, y: q.top, r: q.right, b: q.bottom }; };
        const hit = (a, b) => Math.min(a.r, b.r) - Math.max(a.x, b.x) > 1 && Math.min(a.b, b.b) - Math.max(a.y, b.y) > 1;
        const seen = e => { for (let n = e; n && n !== document.body; n = n.parentElement) { const cs = getComputedStyle(n); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < 0.3) return false; } return true; };
        const out = [];
        let named = 0;
        setPlaying(false); goTo(c, DATA.chapters[c].scenes.indexOf(sc), { animate: false, live: true });
        for (let t = 0.5; t < sc.duration; t += 1) {
          setPlaying(true); state.t = lead() + t; setPlaying(false);
          const cam = captureCamera(t); map.setView(cam.center, cam.zoom, { animate: false });
          document.getAnimations().forEach(a => { try { a.finish(); } catch {} });   // the setting's entrance, at its end
          for (let i = 0; i < 3; i++) { frame(performance.now()); paint(performance.now()); }
          const wrap = edge(map.getContainer()), plate = fx.sets[0]?.marker.getTooltip().getElement();
          const blocks = [...document.querySelectorAll('#view-tools, #ov-notes > *, #hud, #ov-lower > *, #story-guide, .leaflet-control-zoom')]
            .filter(seen).map(e => ({ id: e.id || e.className, ...edge(e) })).filter(q => q.r - q.x > 2);
          if (plate && seen(plate) && !plate.classList.contains('hx-crowded')) blocks.push({ id: 'the name plate', ...edge(plate) });
          for (const e of document.querySelectorAll('.hx-assemblage:not(.hx-glyph) .set-svg text')) {
            if (!seen(e)) continue;
            const q = edge(e);
            if (q.r - q.x < 1) continue;
            named++;
            if (q.x < wrap.x || q.r > wrap.r || q.y < wrap.y || q.b > wrap.b) out.push(`t=${t}: ${e.textContent} is cut by the map's edge`);
            for (const b of blocks) if (hit(q, b)) out.push(`t=${t}: ${e.textContent} is under ${b.id}`);
          }
        }
        return { out, named };
      });
      assert.ok(found.named > 40, `${viewport.width}px ${mode}: the city's names should be on screen`);
      assert.deepEqual(found.out, [], `${viewport.width}px ${mode}: names must stay whole`);
      assert.deepEqual(errors, [], `page errors at ${viewport.width}px ${mode}`);
      await page.close();
    }
  } finally { await browser.close(); }
  console.log('PASS: dated beats on the counter, no part before its date, undated oral tradition, finished city, glyph pull-back, exact repeat frames and whole names in three layouts.');
})().catch(e => { console.error(e); process.exitCode = 1; });

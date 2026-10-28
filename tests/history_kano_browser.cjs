/* The Kano scenes: a city that grows part by part, each part at its own date, and a second scene
   that carries on from the city as it stood in 1438 and fills it with people.
   node tests/history_kano_browser.cjs <built HTML> <local dependency directory>

   While a scene plays, the year counter shows each beat's own date and what it rests on, and no
   part of the city is visible while the counter shows an earlier date than the part's. Oral
   tradition shows only under an undated label and leaves before the next dated beat. The second
   scene opens on the standing city, whole, without Rumfa's parts, which rise again at their date.
   Jumped to, a scene shows the finished city without its passing parts (the oral-tradition frame,
   the disputed dashed line, the count of captive towns). Far out, the city becomes its small glyph,
   and the other places join it only for the pull-back. On a desktop, a short laptop and a phone, the
   city's own names are never drawn under the buttons, notes, year, caption, guide or the city's name
   plate, and never cut by the map's edge. */
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

// Each scene, its city, when it pulls back, and moments to seek twice on the export clock
const SCENES = [{ scene: 'kano', city: 'kano-city', pull: 39.4, seek: [12, 27.5, 37] },
                { scene: 'kano-people', city: 'kano-life', pull: 44, seek: [10.5, 17, 33] }];

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
  try {
    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) for (const S of SCENES) {
      const { page, errors } = await open(browser, viewport, 'cinema');
      const where0 = `${viewport.width}px ${S.scene}`;

      const timeline = await page.evaluate(S => {
        const c = DATA.chapters.findIndex(ch => ch.id === 'hausa'), sc = DATA.chapters[c].scenes.find(s => s.id === S.scene);
        const s = DATA.chapters[c].scenes.indexOf(sc), city = DATA.chapters[c].features[S.city];
        const places = sc.show.filter(id => DATA.chapters[c].features[id].kind === 'point');
        const parts = Object.fromEntries(city.monument.parts.map(p => [p.id, p]));
        setPlaying(false); goTo(c, s, { animate: false, live: true });
        const out = [];
        for (let t = 0; t <= sc.duration - 0.05; t += 0.25) {
          setPlaying(true); state.t = lead() + t; setPlaying(false);
          const cam = captureCamera(t); map.setView(cam.center, cam.zoom, { animate: false });   // the camera at this moment
          frame(performance.now());
          const beat = directedBeat(sc, t).beat;
          const lit = [...document.querySelectorAll('.hx-assemblage:not(.hx-glyph) [data-set-part]')]
            .filter(el => parts[el.dataset.setPart.replace(/-names$/, '')]).map(el => [el.dataset.setPart, +el.style.opacity]);
          const shown = lit.filter(([id, o]) => parts[id] && o > 0.01).map(([id]) => id);
          const hidden = Object.fromEntries(Object.keys(sc.appear).map(id => [id, fx.points[places.indexOf(id)].els.every(el => el.classList.contains('hx-hidden'))]));
          out.push({ t, hud: $('hud-year').textContent, when: beat.when, shown, lit, glyph: !!document.querySelector('.hx-assemblage.hx-glyph'), hidden });
        }
        goTo(c, s, { animate: false });
        frame(performance.now());
        const done = [...document.querySelectorAll('.hx-assemblage [data-set-part]')].map(el => ({ id: el.dataset.setPart, o: +el.style.opacity }));
        return { out, parts, done, hudDone: $('hud-year').textContent, label: sc.when.label, appear: sc.appear };
      }, S);

      const { out, parts } = timeline;
      let before = [];
      for (const f of out) {
        const where = `${where0} t=${f.t}`;
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
        for (const [id, hidden] of Object.entries(f.hidden)) assert.equal(hidden, f.t < timeline.appear[id], `${where}: ${id} joins only for the pull-back`);
      }
      // A city that carries on from a base opens on the standing city, whole and named, as soon as
      // the camera has come in from the previous scene's pull-back
      const standing = Object.values(parts).filter(p => p.standing).map(p => p.id);
      if (standing.length) {
        const first = Object.fromEntries(out.find(f => !f.glyph).lit);
        for (const [id, o] of Object.entries(first)) {
          const p = parts[id.replace(/-names$/, '')];
          assert.equal(o, p.standing ? 1 : 0, `${where0} t=0: ${id} ${p.standing ? 'stands from the start' : 'has not arrived yet'}`);
        }
        assert.ok(standing.includes('first-wall') && !standing.includes('palace') && !parts.tradition, `${where0}: the city as it stood, without Rumfa's parts or the passing ones`);
      }
      // Each part appears in its turn, and the finished city has every part but the passing ones
      for (const p of Object.values(parts)) {
        assert.ok(out.some(f => f.shown.includes(p.id)), `${where0}: ${p.id} never appears while playing`);
      }
      for (const d of timeline.done) {
        const p = parts[d.id] || parts[d.id.replace(/-names$/, '')];
        assert.equal(d.o, p.until != null ? 0 : 1, `${where0}: finished city, ${d.id}`);
      }
      assert.equal(timeline.hudDone, timeline.label, `${where0}: a jumped-to scene shows the whole scene label`);
      assert.ok(out.at(-1).glyph && out.filter(f => f.t < S.pull && f.glyph).every(f => f.t < 1),
        `${where0}: the city becomes its glyph only in the pull-back (and while the camera arrives from the one before)`);

      // Exact repeat frames on the export clock
      await page.click('#cinema-toggle');
      const shot = async t => { await page.evaluate(([sid, t]) => taswira.seek('hausa', sid, t), [S.scene, t]); await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))); return page.locator('#mapwrap').screenshot(); };
      for (const t of S.seek) {
        const a = await shot(t); await shot(4); assert.ok(a.equals(await shot(t)), `${where0}: seeking to ${t} s twice must give identical pixels`);
      }
      await page.evaluate(() => taswira.exitVideo());
      assert.deepEqual(errors, [], `page errors at ${where0}`);
      await page.close();
    }

    // The city's names stay whole wherever they are drawn
    for (const [viewport, mode] of [[{ width: 1440, height: 900 }, 'cinema'], [{ width: 1024, height: 700 }, 'details'], [{ width: 390, height: 844 }, 'normal']]) for (const S of SCENES) {
      const { page, errors } = await open(browser, viewport, mode);
      const found = await page.evaluate(S => {
        const c = DATA.chapters.findIndex(ch => ch.id === 'hausa'), sc = DATA.chapters[c].scenes.find(s => s.id === S.scene);
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
      }, S);
      assert.ok(found.named > 40, `${viewport.width}px ${mode} ${S.scene}: the city's names should be on screen`);
      assert.deepEqual(found.out, [], `${viewport.width}px ${mode} ${S.scene}: names must stay whole`);
      assert.deepEqual(errors, [], `page errors at ${viewport.width}px ${mode} ${S.scene}`);
      await page.close();
    }
  } finally { await browser.close(); }
  console.log('PASS: both Kano scenes: dated beats on the counter, no part before its date, undated oral tradition, the standing city, finished city, glyph pull-back, exact repeat frames and whole names in three layouts.');
})().catch(e => { console.error(e); process.exitCode = 1; });

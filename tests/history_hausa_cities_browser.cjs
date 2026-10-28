/* The Hausa cities scene: separate walled towns, never one kingdom, each named beside its own town.
   node tests/history_hausa_cities_browser.cjs <built HTML> <local dependency directory>

   While the scene plays, the year counter shows each beat's own label, with no date under the oral
   tradition. Each town, tie and note waits for its moment; an oral-tradition note shows only under
   the tradition, and every other note only under a dated beat. Rano goes faint after Kano takes it.
   The disputed tie to Bornu is left dashed and the documented one solid. On a desktop and a phone,
   every town name shown sits level with its own town, with no other town between them, and clear
   of the notes. In the 1920×1080 video, once the camera has settled, names and notes are never under
   its caption, caution, credit or bars, nor cut by the frame, and seeking twice gives identical pixels. */
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), { chromium } = require('playwright');
const [html, deps] = process.argv.slice(2);
if (!html || !deps) throw Error('Usage: node tests/history_hausa_cities_browser.cjs <built HTML> <local dependency directory>');

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

// In the page: the scene, and the moments when its camera is still (not between two shots)
const SETUP = `
  var C = DATA.chapters.findIndex(ch => ch.id === 'hausa'), SC = DATA.chapters[C].scenes.find(s => s.id === 'hausa-cities');
  var F = DATA.chapters[C].features, S = DATA.chapters[C].scenes.indexOf(SC);
  var still = t => SC.camera_path.every(c => t < c.at || t > c.at + c.dur + 0.2) && t > 1.5;
  var box = e => { const q = e.getBoundingClientRect(); return { x: q.left, y: q.top, r: q.right, b: q.bottom }; };
  var hit = (a, b) => Math.min(a.r, b.r) - Math.max(a.x, b.x) > 1 && Math.min(a.b, b.b) - Math.max(a.y, b.y) > 1;
  var seen = e => !e.classList.contains('hx-hidden') && !e.classList.contains('hx-crowded') && getComputedStyle(e).visibility !== 'hidden';
  var towns = () => fx.points.filter(pt => pt.els.some(e => e.classList?.contains('hx-town')))
    .map(pt => ({ pt, el: pt.els.find(e => e.classList.contains('hx-town')), label: pt.els.find(e => e.classList?.contains('town-label')) }));
`;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
  try {
    for (const [viewport, mode] of [[{ width: 1440, height: 900 }, 'cinema'], [{ width: 1440, height: 900 }, 'normal'], [{ width: 390, height: 844 }, 'normal']]) {
      const { page, errors } = await open(browser, viewport, mode);
      const where0 = `${viewport.width}px ${mode}`;
      await page.evaluate(SETUP);
      const run = await page.evaluate(() => {
        const places = SC.show.filter(id => F[id].kind === 'point');
        const notes = fx => fx.labels.filter(l => l.el.classList.contains('note-label'));
        setPlaying(false); goTo(C, S, { animate: false, live: true });
        const out = [], layout = [];
        let named = 0;
        for (let t = 0; t <= SC.duration - 0.05; t += 0.25) {
          setPlaying(true); state.t = lead() + t; setPlaying(false);
          const cam = captureCamera(t); map.setView(cam.center, cam.zoom, { animate: false });
          frame(performance.now());
          const beat = directedBeat(SC, t).beat;
          const hidden = Object.fromEntries(places.map((id, i) => [id, fx.points[i].els.every(el => el.classList.contains('hx-hidden'))]));
          for (const d of fx.draws) if (d.id) hidden[d.id] = d.el.classList.contains('hx-hidden');
          const ties = Object.fromEntries(fx.draws.filter(d => d.id).map(d => [d.id, { dash: d.el.style.strokeDasharray.replace(/,\s*/g, ' '), len: d.el.getAttribute('pathLength') }]));
          const shown = notes(fx).map(l => !l.el.classList.contains('hx-hidden'));
          const rano = fx.fades.length === 1 ? +(fx.fades[0].els[0].style.opacity || 1) : null;
          out.push({ t, hud: $('hud-year').textContent, when: beat.when, hidden, ties, shown, rano });
          // Where the names sit, once the camera has settled and the towns have risen
          if (!still(t) || Math.abs(t * 2 - Math.round(t * 2)) > 0.01) continue;
          document.getAnimations().forEach(a => { try { a.finish(); } catch {} });
          for (let i = 0; i < 3; i++) { frame(performance.now()); paint(performance.now()); }
          const all = towns().filter(x => !x.el.classList.contains('hx-hidden')).map(x => ({ ...x, tb: (q => ({ x: q.left, y: q.top, r: q.right, b: q.bottom }))(townBox(x.el)) }));
          const noteBoxes = [...document.querySelectorAll('.note-label:not(.hx-hidden) .lab-c')].map(box);
          for (const x of all) {
            if (!x.label || !seen(x.label)) continue;
            const q = box(x.label), mid = (q.y + q.b) / 2, name = x.label.textContent;
            named++;
            if (mid < x.tb.y || mid > x.tb.b) layout.push(`t=${t}: ${name} is not level with its town`);
            const gap = { x: Math.min(q.r, x.tb.r), r: Math.max(q.x, x.tb.x), y: q.y, b: q.b };
            for (const o of all) if (o !== x && (hit(o.tb, gap) || hit(o.tb, q))) layout.push(`t=${t}: another town stands between ${name} and its town`);
            if (gap.r - gap.x > 60) layout.push(`t=${t}: ${name} is ${Math.round(gap.r - gap.x)}px from its town`);
            for (const n of noteBoxes) if (hit(n, q)) layout.push(`t=${t}: ${name} is under a note`);
          }
        }
        const appear = SC.appear, ns = SC.notes, fade = SC.fade.rano, dashed = Object.keys(appear).filter(id => F[id].kind === 'link' && F[id].status === 'disputed');
        return { out, layout, appear, ns, fade, dashed, named };
      });
      const { out, appear, ns } = run;
      for (const f of out) {
        const where = `${where0} t=${f.t}`;
        assert.equal(f.hud, f.when.label, `${where}: the counter must show the beat's own label`);
        if (f.when.basis === 'oral') assert.doesNotMatch(f.hud, /\d/, `${where}: oral tradition must carry no date`);
        for (const [id, at] of Object.entries(appear)) assert.equal(f.hidden[id], f.t < at, `${where}: ${id} appears at ${at} s`);
        ns.forEach((n, i) => {
          assert.equal(f.shown[i], f.t >= n.at && f.t < n.until, `${where}: note "${n.text}" shows from ${n.at} to ${n.until} s`);
          if (f.shown[i]) assert.equal(f.when.basis === 'oral', !!n.oral, `${where}: note "${n.text}" ${n.oral ? 'is tradition' : 'is dated'}`);
        });
        assert.ok(f.t < run.fade ? f.rano === 1 : f.t < run.fade + 0.8 || Math.abs(f.rano - 0.45) < 0.01, `${where}: Rano fades after ${run.fade} s (${f.rano})`);
        for (const [id, tie] of Object.entries(f.ties)) if (f.t > appear[id] + 1.3) {
          const disputed = run.dashed.includes(id);
          assert.equal(tie.dash, disputed ? '7 6' : '', `${where}: ${id} is ${disputed ? 'dashed' : 'solid'} once drawn`);
          if (disputed) assert.equal(tie.len, null, `${where}: a dashed tie drops pathLength, which would scale its dashes`);
        }
      }
      assert.ok(run.dashed.length === 1 && Object.keys(out[0].ties).length === 2, `${where0}: two tribute ties, one disputed`);
      assert.ok(run.named > 100, `${where0}: town names should be on screen (${run.named})`);
      assert.deepEqual(run.layout, [], `${where0}: each town's name sits beside its own town`);
      assert.deepEqual(errors, [], `page errors at ${where0}`);
      await page.close();
    }

    // The 1920×1080 video
    const { page, errors } = await open(browser, { width: 1920, height: 1080 }, 'normal');
    await page.evaluate(SETUP);
    const settle = () => page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
    const found = [];
    let named = 0;
    const times = await page.evaluate(() => { const ts = []; for (let t = 0.5; t < SC.duration; t += 0.5) if (still(t)) ts.push(t); return ts; });
    for (const t of times) {
      await page.evaluate(t => taswira.seek('hausa', 'hausa-cities', t), t);
      await settle();
      const r = await page.evaluate(t => {
        document.getAnimations().forEach(a => { try { a.finish(); } catch {} });
        const wrap = box(map.getContainer());
        const bars = [...document.querySelectorAll('.lb, #video-caption, #video-caution, #video-credit, #video-tools, #exit-video')]
          .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden' && !e.hidden).map(e => ({ id: e.id || e.className, ...box(e) }));
        const things = [...document.querySelectorAll('.town-label, .site-label')].filter(seen).map(e => ({ name: e.textContent, ...box(e) }))
          .concat([...document.querySelectorAll('.note-label:not(.hx-hidden) .lab-c')].map(e => ({ name: `note "${e.textContent}"`, ...box(e) })));
        const out = [];
        for (const q of things) {
          if (q.x < wrap.x || q.r > wrap.r || q.y < wrap.y || q.b > wrap.b) out.push(`t=${t}: ${q.name} is cut by the frame`);
          for (const b of bars) if (hit(q, b)) out.push(`t=${t}: ${q.name} is under ${b.id}`);
        }
        return { out, n: things.length };
      }, t);
      found.push(...r.out);
      named += r.n;
    }
    assert.ok(times.length > 40 && named > 300, `video: names should be on screen (${times.length} moments, ${named} names)`);
    assert.deepEqual(found, [], 'video: names and notes stay clear of the overlays');
    const shot = async t => { await page.evaluate(t => taswira.seek('hausa', 'hausa-cities', t), t); await settle(); return page.locator('#mapwrap').screenshot(); };
    for (const t of [3, 17, 36, 58]) {
      const a = await shot(t); await shot(9); assert.ok(a.equals(await shot(t)), `video: seeking to ${t} s twice must give identical pixels`);
    }
    await page.evaluate(() => taswira.exitVideo());
    assert.deepEqual(errors, [], 'page errors in the video');
    await page.close();
  } finally { await browser.close(); }
  console.log('PASS: Hausa cities: beat labels, undated tradition, towns, ties and notes at their moments, Rano faint, the disputed tie dashed, names beside their own towns on desktop and phone, clear of the video overlays, exact repeat frames.');
})().catch(e => { console.error(e); process.exitCode = 1; });

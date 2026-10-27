/* Composition checks for the history player: what sits on top of the map must never collide.
   node tests/history_layout_browser.cjs <built HTML> <local dependency directory>

   For every scene, in the normal, details-hidden and cinema layouts, on a desktop, a small laptop
   and a phone, while playing (start, middle, end) and after a jump, this checks that the visible
   overlays (title strips, narration, year, guide, notes, controls, credits) do not overlap each
   other and stay inside the map. It also checks that architectural settings follow the map's zoom:
   zooming out shrinks them with the land, and far out they become a small glyph. */
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), { chromium } = require('playwright');
const [html, deps] = process.argv.slice(2);
if (!html || !deps) throw Error('Usage: node tests/history_layout_browser.cjs <built HTML> <local dependency directory>');

const OVERLAYS = ['#view-tools', '#viewer-status', '#assembly-note', '#lower', '#tour-strip', '#story-caption',
  '#hud', '#story-guide', '.leaflet-control-zoom', '.leaflet-control-attribution', '#globe-credit'];

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
  if (mode === 'details') await page.click('#details-toggle');
  if (mode === 'cinema') await page.click('#cinema-toggle');
  await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
  return { page, errors };
}

// The boxes of the overlays that can be seen right now, in page pixels
function boxes(selectors) {
  const wrap = document.getElementById('mapwrap').getBoundingClientRect();
  const out = [];
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (!el || el.hidden) continue;
    let hidden = false, fading = false;
    for (let n = el; n && n !== document.body; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < 0.05) { hidden = true; break; }
      if (+cs.opacity < 0.99) fading = true;
    }
    if (hidden) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2 || !el.textContent.trim() && sel !== '#story-guide') continue;
    out.push({ sel, x: r.left, y: r.top, r: r.right, b: r.bottom, fading });
  }
  return { wrap: { x: wrap.left, y: wrap.top, r: wrap.right, b: wrap.bottom }, out };
}

function collisions({ wrap, out }) {
  const found = [];
  for (const a of out) {     // an overlay still sliding in may start beyond the edge
    if (!a.fading && (a.x < wrap.x - 1 || a.y < wrap.y - 1 || a.r > wrap.r + 1 || a.b > wrap.b + 1)) found.push(`${a.sel} leaves the map`);
  }
  for (let i = 0; i < out.length; i++) for (let j = i + 1; j < out.length; j++) {
    const a = out[i], b = out[j];
    const w = Math.min(a.r, b.r) - Math.max(a.x, b.x), h = Math.min(a.b, b.b) - Math.max(a.y, b.y);
    if (w > 1 && h > 1) found.push(`${a.sel} overlaps ${b.sel} by ${Math.round(w)}×${Math.round(h)} px`);
  }
  return found;
}

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
  const problems = [];
  let checked = 0;
  try {
    for (const viewport of [{ width: 1440, height: 900 }, { width: 1024, height: 700 }, { width: 390, height: 844 }]) {
      for (const mode of ['normal', 'details', 'cinema']) {
        const { page, errors } = await open(browser, viewport, mode);
        const scenes = await page.evaluate(() => DATA.chapters.flatMap((c, ci) => c.scenes.map((s, si) => ({ ci, si, id: c.id + '/' + s.id, d: s.duration }))));
        for (const sc of scenes) {
          for (const t of ['jump', 0.6, 3.2, sc.d * 0.5, sc.d - 0.4]) {
            const found = await page.evaluate(({ sc, t, OVERLAYS, boxesSrc, collisionsSrc }) => {
              const boxes = eval('(' + boxesSrc + ')'), collisions = eval('(' + collisionsSrc + ')');
              setPlaying(false);
              goTo(sc.ci, sc.si, { animate: false, live: t !== 'jump' });
              if (t !== 'jump') { setPlaying(true); state.t = lead() + t; setPlaying(false); }
              frame(performance.now()); paint(performance.now());
              return collisions(boxes(OVERLAYS));
            }, { sc, t, OVERLAYS, boxesSrc: boxes.toString(), collisionsSrc: collisions.toString() });
            checked++;
            for (const f of found) problems.push(`${viewport.width}px ${mode} ${sc.id} t=${t}: ${f}`);
          }
        }
        assert.deepEqual(errors, [], `page errors at ${viewport.width}px ${mode}`);
        await page.close();
      }
    }

    // Architecture follows the map: at the authored camera it is a close-up; zooming out shrinks it
    // with the land, and far out it becomes a small glyph that never covers the continent.
    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      for (const mode of ['normal', 'cinema']) {
        const { page } = await open(browser, viewport, mode);
        const sets = await page.evaluate(() => DATA.chapters.flatMap((c, ci) => c.scenes.map((s, si) => ({ ci, si, id: s.id,
          set: s.monuments !== false && (s.show || []).some(f => c.features[f]?.monument?.setting) }))).filter(s => s.set));
        assert.ok(sets.length >= 3, 'expected the three architectural settings');
        for (const sc of sets) {
          const sizes = await page.evaluate(sc => {
            setPlaying(false); goTo(sc.ci, sc.si, { animate: false });
            const z0 = cameraOf(chapter(), scene()).zoom, out = [];
            for (const dz of [0, -1, -2, -3]) {
              map.setZoom(z0 + dz, { animate: false }); frame(performance.now());
              const el = document.querySelector('.hx-monument'), m = map.getSize();
              if (!el) { out.push({ dz, w: 0, h: 0, glyph: false, missing: true, mw: m.x, mh: m.y }); continue; }
              const r = el.getBoundingClientRect();
              out.push({ dz, w: r.width, h: r.height, glyph: el.classList.contains('hx-glyph'), mw: m.x, mh: m.y });
            }
            return out;
          }, sc);
          const [a, b, c] = sizes;
          if (sizes.some(s => s.missing)) { problems.push(`${viewport.width}px ${mode} ${sc.id}: architecture missing at some zoom`); continue; }
          if (a.w > a.mw * 0.9 || a.h > a.mh * 0.9) problems.push(`${viewport.width}px ${mode} ${sc.id}: close-up is larger than the map (${Math.round(a.w)}×${Math.round(a.h)})`);
          if (!(b.glyph || Math.abs(b.w / a.w - 0.5) < 0.08)) problems.push(`${viewport.width}px ${mode} ${sc.id}: one step out, width ${Math.round(a.w)} → ${Math.round(b.w)} (should halve)`);
          if (!(c.glyph || c.w <= a.w * 0.3)) problems.push(`${viewport.width}px ${mode} ${sc.id}: two steps out, still ${Math.round(c.w)} px wide`);
          for (const s of sizes.filter(s => s.dz <= -3)) if (!s.glyph) problems.push(`${viewport.width}px ${mode} ${sc.id}: no glyph three steps out`);
        }
        await page.close();
      }
    }
  } finally { await browser.close(); }
  if (problems.length) {
    // Group by kind of problem, with how often it happened and the first place it did
    const kinds = new Map();
    for (const p of problems) {
      const kind = p.replace(/^\S+ \S+ \S+ t=\S+: /, '').replace(/^\S+ \S+ \S+: /, '').replace(/ by .*| \(.*|[0-9]+ → [0-9]+|still [0-9]+/g, '');
      const k = kinds.get(kind) || { n: 0, first: p };
      k.n++; kinds.set(kind, k);
    }
    for (const [kind, k] of [...kinds].sort((a, b) => b[1].n - a[1].n)) console.error(`${String(k.n).padStart(5)} × ${kind}   e.g. ${k.first}`);
    console.error(`FAIL: ${problems.length} layout problems in ${checked} states`);
    process.exitCode = 1;
  } else console.log(`PASS: ${checked} scene states with no overlapping overlays; architecture follows the map's zoom.`);
})().catch(e => { console.error(e); process.exitCode = 1; });

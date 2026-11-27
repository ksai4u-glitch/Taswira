/* Optional browser checks. Usage: node tests/director_browser.cjs /path/to/preview.html */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium } = require('playwright');

(async () => {
  const pageHtml = fs.readFileSync(process.argv[2], 'utf8');
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [], requests = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => requests.push(request.url()));
    await page.setContent(pageHtml);
    await page.evaluate(() => document.fonts.ready);
    assert.equal(await page.locator('#scenes button').count(), 7);
    assert.equal(await page.locator('#year').textContent(), '600 million years ago');
    const allScenes = await page.evaluate(() => JSON.parse(document.getElementById('director-data').textContent).chapters.map(c => c.scenes.length));
    for (let chapter = 0; chapter < allScenes.length; chapter++) {
      for (let scene = 0; scene < allScenes[chapter]; scene++) {
        await page.evaluate(args => TaswiraDirector.seek(args), { chapter, scene, progress: .5 });
        assert.ok((await page.locator('#caption').textContent()).length > 10);
      }
    }
    // Revisit a time after a different scene: pixels must be identical.
    const at = { chapter: 0, scene: 2, progress: .65 };
    const first = await page.evaluate(args => { TaswiraDirector.seek(args); return document.getElementById('world').toDataURL(); }, at);
    await page.evaluate(() => TaswiraDirector.seek({ chapter: 1, scene: 0, progress: .3 }));
    const repeated = await page.evaluate(args => { TaswiraDirector.seek(args); return document.getElementById('world').toDataURL(); }, at);
    assert.equal(first, repeated, 'Seeking must not depend on the previous scene or wall clock');
    await page.locator('#sources').click();
    assert.equal(await page.getByRole('dialog', { name: 'Behind this scene' }).count(), 1);
    assert.ok((await page.locator('#evidence-content').textContent()).includes('Sources disagree on when the last land link broke'),
      'Scene-level disputes must appear alongside their sources');
    await page.keyboard.press('Escape');
    const markerChangesPixels = await page.evaluate(() => {
      TaswiraDirector.seek({ chapter: 0, scene: 4, progress: .5 });
      const before = document.getElementById('world').toDataURL();
      const sc = DATA.chapters[0].scenes[4], saved = sc.show;
      sc.show = saved.filter(id => id !== 'enugu-coal');
      TaswiraDirector.seek({ chapter: 0, scene: 4, progress: .5 });
      const after = document.getElementById('world').toDataURL();
      sc.show = saved;
      return before !== after;
    });
    assert.equal(markerChangesPixels, true, 'The sourced coal-swamp site must be drawn on the globe');
    await page.evaluate(args => TaswiraDirector.seek(args), at);
    await page.locator('#scrub').evaluate(el => { el.value = 750; el.dispatchEvent(new Event('input')); });
    assert.equal(await page.evaluate(() => TaswiraDirector.getState().progress), .75);
    await page.locator('#sources').click();
    assert.equal(await page.locator('#evidence').evaluate(el => el.open), true);
    assert.ok(await page.locator('#evidence-content a').count());
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#evidence').evaluate(el => el.open), false);
    await page.locator('#play').click();
    await page.waitForFunction(() => TaswiraDirector.getState().progress > .75);
    await page.locator('#play').click();
    const paused = await page.evaluate(() => TaswiraDirector.getState().progress);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.equal(await page.evaluate(() => TaswiraDirector.getState().progress), paused);
    await page.evaluate(() => TaswiraDirector.seek({ chapter: 1, scene: 5, progress: .9999 }));
    await page.locator('#play').click();
    await page.waitForFunction(() => !TaswiraDirector.getState().playing);
    assert.equal(await page.evaluate(() => TaswiraDirector.getState().progress), 1);
    assert.equal(await page.evaluate(() => { try { TaswiraDirector.seek({ chapter: -1 }); return false; } catch { return true; } }), true);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => TaswiraDirector.seek({}));
    await page.waitForFunction(() => document.getElementById('world').width <= 780);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), 390, 'Phone layout must not overflow');
    assert.equal(await page.locator('.draft').isVisible(), true);
    await page.emulateMedia({ reducedMotion: 'reduce' });
    assert.equal(await page.evaluate(() => TaswiraDirector.getState().playing), false);
    await page.locator('#next-chapter').click();
    assert.equal(await page.evaluate(() => TaswiraDirector.getState().chapter), 1);
    await page.locator('#scenes button').nth(1).focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => document.activeElement.closest('#scenes') !== null), true,
      'Scene selection must retain keyboard focus');
    await page.setViewportSize({ width: 320, height: 568 });
    await page.evaluate(() => TaswiraDirector.seek({ chapter: 1, scene: 0 }));
    assert.ok(await page.locator('.hero').evaluate(el => el.getBoundingClientRect().bottom < 460),
      'Narrow-phone introduction must finish before the mapped site labels');
    assert.equal(requests.length, 0, 'Offline preview must make no network requests');
    assert.deepEqual(errors, []);
    console.log('PASS: all 13 scenes; identical seek frames; scrubber; evidence dialog; play/pause/end; input validation; phone layout; reduced motion; zero network requests.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

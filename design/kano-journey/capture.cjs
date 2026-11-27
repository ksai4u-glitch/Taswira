/* Export the Kano journey mock-ups to PNG.
 * From the repo root:  python -m http.server 8765   (in one terminal)
 *                      node design/kano-journey/capture.cjs   (in another)
 * Writes design/kano-journey/screens/<frame id>.png at 1x (desktop 1440x900, phone 390x844).
 */
const { chromium } = require('playwright');
const path = require('node:path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 2000, height: 1200 }, deviceScaleFactor: 1 });
  await p.goto('http://127.0.0.1:8765/design/kano-journey/kano-journey.html', { waitUntil: 'load' });
  for (const id of ['d1','p1','d2','p2','d3','p3','d4','p4','d5','p5']) {
    await p.locator('#' + id).screenshot({ path: path.join(__dirname, 'screens', id + '.png') });
  }
  await b.close();
})();

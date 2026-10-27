/* Actual-player UI and assembly regressions: built HTML + local dependencies. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
const p=await b.newPage({viewport:{width:1440,height:900}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.route('**/*',r=>{let u=r.request().url(),n=u.includes('leaflet.css')?'leaflet.css':u.includes('leaflet.js')?'leaflet.js':u.includes('d3-array')?'d3-array.js':u.includes('d3-geo')?'d3-geo.js':null;return n?r.fulfill({contentType:n.endsWith('css')?'text/css':'application/javascript',body:fs.readFileSync(path.join(process.argv[3],n))}):r.abort();});
await p.setContent(fs.readFileSync(process.argv[2],'utf8'));await p.waitForFunction(()=>window.taswira);if(await p.evaluate(()=>!!taswira.ready))await p.evaluate(()=>taswira.ready());
assert.equal(await p.locator('#details-toggle').count(),1,'The real player needs a reversible details toggle');
const before=await p.locator('#mapwrap').evaluate(el=>el.clientWidth);await p.locator('#details-toggle').click();
assert.equal(await p.locator('#card').isVisible(),false);assert.equal(await p.locator('#details-toggle').getAttribute('aria-expanded'),'false');
assert.ok(await p.locator('#mapwrap').evaluate(el=>el.clientWidth)>before+300);assert.equal(await p.locator('#story-caption').isVisible(),true);
await p.locator('#cinema-toggle').click();assert.equal(await p.locator('header').isVisible(),false);assert.equal(await p.locator('#viewer-status').isVisible(),true);assert.equal(await p.locator('#controls').isVisible(),true);
await p.keyboard.press('Escape');assert.equal(await p.locator('header').isVisible(),true);
await p.locator('#details-toggle').click();assert.equal(await p.locator('#card').isVisible(),true);
await p.evaluate(()=>{goTo(1,8,{live:true,animate:false});state.t=6;frame(performance.now());});
assert.ok(await p.locator('.hx-assemblage [data-set-part]').count()>=8,'A city scene must assemble multiple distinct components');
const t=await p.evaluate(()=>state.t);await p.locator('#details-toggle').click();assert.equal(await p.evaluate(()=>state.t),t,'Hiding details must preserve the scene clock');
await p.evaluate(()=>taswira.seek('africa','zimbabwe',7));await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));const first=await p.locator('#mapwrap').screenshot();
await p.evaluate(()=>taswira.seek('nok','iron',4));await p.evaluate(()=>taswira.seek('africa','zimbabwe',7));await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));assert.ok(first.equals(await p.locator('#mapwrap').screenshot()),'Layered city and guide must use one exact clock');
await p.evaluate(()=>taswira.exitVideo());await p.setViewportSize({width:390,height:844});await p.locator('#cinema-toggle').click();assert.ok(await p.locator('#mapwrap').evaluate(el=>el.clientHeight)>400);assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.ok(await p.evaluate(()=>{const g=document.getElementById('story-guide').getBoundingClientRect();return [...document.querySelectorAll('.site-label')].every(el=>{const r=el.getBoundingClientRect();return r.right<=g.left||r.left>=g.right||r.bottom<=g.top||r.top>=g.bottom;});}),'The phone guide must not cover the architectural site label');
await p.keyboard.press('Escape');await p.emulateMedia({reducedMotion:'reduce'});await p.evaluate(()=>goTo(1,8,{animate:false}));assert.ok(await p.locator('.hx-assemblage [data-set-part]').evaluateAll(els=>els.every(el=>getComputedStyle(el).opacity==='1')),'Reduced motion gets the completed city');
await p.evaluate(()=>{goTo(DATA.chapters.findIndex(c=>c.id==='nok'),DATA.chapters.find(c=>c.id==='nok').scenes.findIndex(s=>s.id==='iron'),{animate:false});setTheatre(true);});assert.match(await p.locator('#viewer-status').textContent(),/Disputed evidence/,'Cinema must preserve feature-level uncertainty');
assert.deepEqual(errors,[]);console.log('PASS: reversible details/cinema, captions/caveats, preserved clock, multi-part city, exact repeat frames, phone space and complete reduced motion.');
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

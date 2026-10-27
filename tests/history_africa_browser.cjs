/* node tests/history_africa_browser.cjs <built HTML> <local dependencies> */
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
const p=await b.newPage({viewport:{width:1440,height:900}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.route('**/*',r=>{const u=r.request().url(),n=u.includes('leaflet.css')?'leaflet.css':u.includes('leaflet.js')?'leaflet.js':u.includes('d3-array')?'d3-array.js':u.includes('d3-geo')?'d3-geo.js':null;return n?r.fulfill({contentType:n.endsWith('.css')?'text/css':'application/javascript',body:fs.readFileSync(path.join(process.argv[3],n))}):r.abort();});
await p.setContent(fs.readFileSync(process.argv[2],'utf8'));await p.waitForFunction(()=>window.taswira);
assert.ok(await p.evaluate(()=>DATA.chapters.some(ch=>ch.id==='africa')),'The approved Africa tour must be in the actual player');
assert.deepEqual(await p.evaluate(()=>DATA.chapters.map(c=>c.id)),['deep','africa','nok','states','key']);
const snapshotYear=await p.evaluate(()=>{goTo(1,1,{live:true,animate:false});state.shownYear=-3100;goTo(1,2,{live:true,animate:false});state.t=.8;frame(performance.now());return state.shownYear;});assert.equal(snapshotYear,-250,'A rising monument must not inherit the prior snapshot’s year');
await p.evaluate(()=>taswira.seek('africa','origins',8));assert.match(await p.locator('#hud-year').textContent(),/300,000 years ago/);
await p.evaluate(()=>taswira.seek('africa','egypt',8));assert.match(await p.locator('#hud-year').textContent(),/3100 BCE/);
for(const id of ['meroe','aksum','zimbabwe']){await p.evaluate(id=>taswira.seek('africa',id,5),id);assert.equal(await p.locator('.hx-monument').count(),1);}
for(const id of ['zoom-africa','west-africa','niger-benue']){await p.evaluate(id=>taswira.seek('africa',id,6),id);await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));const one=await p.locator('#mapwrap').screenshot();await p.evaluate(()=>taswira.seek('nok','iron',3));await p.evaluate(id=>taswira.seek('africa',id,6),id);await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));assert.ok(one.equals(await p.locator('#mapwrap').screenshot()),id+' must seek to identical pixels');}
const entry=await p.evaluate(()=>{taswira.seek('africa','niger-benue',0);return captureCamera(0);});assert.deepEqual(entry.center,[6.5,6.5]);assert.equal(entry.zoom,5.6);
await p.evaluate(()=>taswira.seek('africa','songhai',8));assert.equal(await p.locator('#hud-year').textContent(),'1495');
await p.evaluate(()=>taswira.seek('africa','west-africa',10));assert.ok(await p.locator('.hx-river').count()>0);assert.equal(await p.evaluate(()=>modernTiles._map!=null),false);
await p.setViewportSize({width:390,height:844});await p.evaluate(()=>taswira.seek('africa','origins',4));assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
await p.evaluate(()=>{taswira.exitVideo();goTo(1,2,{animate:false});});assert.equal(await p.locator('#hud').isVisible(),false,'The phone tour must not overlay duplicate year/title text');await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));assert.ok(await p.evaluate(()=>{const a=document.querySelector('.hx-monument').getBoundingClientRect(),b=document.getElementById('tour-strip').getBoundingClientRect();return a.bottom<=b.top||a.top>=b.bottom;}),'Compact phone strip must leave the monument visible');await p.emulateMedia({reducedMotion:'reduce'});
await p.evaluate(()=>{goTo(DATA.chapters.findIndex(c=>c.id==='africa'),0,{animate:false});});assert.match(await p.locator('#hud-year').textContent(),/300,000/);
assert.deepEqual(errors,[]);console.log('PASS: Africa tour order, years-ago/BCE clock shift, dated monuments, river reveal, repeated exact frames, mobile and reduced motion.');
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

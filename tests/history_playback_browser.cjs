/* Usage matches history_browser.cjs: built HTML, dependency directory. */
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:900}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',route=>{
      const url=route.request().url();
      const name=url.includes('leaflet.css')?'leaflet.css':url.includes('leaflet.js')?'leaflet.js':url.includes('d3-array')?'d3-array.js':url.includes('d3-geo')?'d3-geo.js':null;
      return name?route.fulfill({contentType:name.endsWith('css')?'text/css':'application/javascript',body:fs.readFileSync(path.join(process.argv[3],name),'utf8')}):route.abort();
    });
    await page.setContent(fs.readFileSync(process.argv[2],'utf8'));
    await page.waitForFunction(()=>typeof state!=='undefined'&&state.drawn);
    const jump = await page.evaluate(()=>{
      const c=DATA.chapters.findIndex(c=>c.id==='nok');goTo(c,1,{animate:false});
      return {shown:document.getElementById('hud-year').textContent,want:scene().when.label,year:state.shownYear,end:scene().when.to};
    });
    assert.equal(jump.shown,jump.want,'A finished jumped-to scene must show its date range');
    assert.equal(jump.year,jump.end);
    await page.emulateMedia({reducedMotion:'reduce'});
    const reduced=await page.evaluate(()=>{
      const c=DATA.chapters.findIndex(c=>c.id==='key'),s=DATA.chapters[c].scenes.findIndex(s=>s.id==='taken');
      goTo(c,s,{live:true,animate:false});frame(performance.now());
      return {shown:document.getElementById('hud-year').textContent,want:scene().when.label,allHeld:fx.flips.every(f=>!f.held.classList.contains('hx-hidden'))};
    });
    assert.equal(reduced.shown,reduced.want);assert.ok(reduced.allHeld);
    await page.emulateMedia({reducedMotion:'no-preference'});
    const arrivals=await page.evaluate(()=>{
      const c=DATA.chapters.findIndex(c=>c.id==='key'),s=DATA.chapters[c].scenes.findIndex(s=>s.id==='taken');
      goTo(c,s,{live:true,animate:false});
      return scene().campaign_clock.campaigns['conquest-1903'].map(stop=>{
        state.t=lead()+stop.at;frame(performance.now());
        const f=fx.flips.find(f=>f.id===stop.id);
        return {id:stop.id,year:state.shownYear,want:stop.year,at:f.at,wantAt:stop.at,held:!f.held.classList.contains('hx-hidden'),hud:document.getElementById('hud-year').textContent};
      });
    });
    for(const stop of arrivals){assert.ok(Math.abs(stop.year-stop.want)<1e-8,stop.id+' counter date');assert.equal(stop.at,stop.wantAt);assert.ok(stop.held);assert.equal(stop.hud,String(Math.floor(stop.want)));}
    const calm=await page.evaluate(()=>paint(performance.now()));assert.equal(calm,false,'Violence scenes must not draw celebratory canvas effects');
    const ping=await page.evaluate(()=>{
      const c=DATA.chapters.findIndex(c=>c.id==='key'),s=DATA.chapters[c].scenes.findIndex(s=>s.id==='salt');
      goTo(c,s,{live:true,animate:false});state.t=scene().duration;frame(performance.now());
      const el=document.querySelector('.hx-ping');return !el||getComputedStyle(el).animationName==='none';
    });
    assert.ok(ping,'Sensitive trade scenes must not retain decorative CSS pulses');
    const advance=await page.evaluate(()=>{
      const results=[];
      for(const id of ['deep','africa','nok','hausa','sokoto','states']){
        const c=DATA.chapters.findIndex(c=>c.id===id);goTo(c,DATA.chapters[c].scenes.length-1,{live:true,animate:false});
        state.playing=true;state.t=scene().duration+lead()+1;state.last=performance.now();loop(performance.now());
        results.push({chapter:chapter().id,playing:state.playing});setPlaying(false);
      }return results;
    });
    assert.deepEqual(advance,[{chapter:'africa',playing:true},{chapter:'nok',playing:true},{chapter:'hausa',playing:true},{chapter:'sokoto',playing:true},{chapter:'states',playing:true},{chapter:'states',playing:false}]);
    assert.ok(await page.locator('#chapters button').last().textContent().then(t=>t.includes('reference')));
    await page.locator('#chapters button').last().click();
    assert.equal(await page.evaluate(()=>chapter().id),'key');
    assert.deepEqual(errors,[]);
    console.log('PASS: jump range, reduced-motion completion, dated arrivals/control/HUD, calm campaign rendering, reference-skipping playback and reference navigation.');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});

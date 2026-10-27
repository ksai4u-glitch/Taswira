/* Capture-mode regression checks; built HTML and local dependency directory. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require('playwright');
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try{
    const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',route=>{
      const u=route.request().url(),name=u.includes('leaflet.css')?'leaflet.css':u.includes('leaflet.js')?'leaflet.js':u.includes('d3-array')?'d3-array.js':u.includes('d3-geo')?'d3-geo.js':null;
      return name?route.fulfill({contentType:name.endsWith('css')?'text/css':'application/javascript',body:fs.readFileSync(path.join(process.argv[3],name),'utf8')}):route.abort();
    });
    await page.setContent(fs.readFileSync(process.argv[2],'utf8'));
    await page.waitForFunction(()=>typeof state!=='undefined'&&state.drawn);
    assert.ok(await page.evaluate(()=>typeof window.taswira?.seek==='function'),'The main player needs a public seek API');
    const motion=await page.evaluate(()=>{taswira.seek('nok','iron',2.1);return [...document.querySelectorAll('#mapwrap .hx-furnace')].some(el=>getComputedStyle(el).animationName!=='none');});
    assert.ok(motion,'Video export must preserve the furnace animation, not remove it');
    const phases=[];
    for(const t of [2.1,2.4])phases.push(await page.evaluate(t=>{taswira.seek('nok','iron',t);return getComputedStyle(document.querySelector('.hx-furnace')).filter;},t));
    assert.notEqual(phases[0],phases[1],'Furnace flicker must advance on the export clock');
    const flash=await page.evaluate(()=>{taswira.seek('states','1976',6);const item=fx.states.find(s=>s.code==='NG-FC');return {age:state.t-item.at,filter:getComputedStyle(item.el).filter};});
    assert.ok(flash.age>1.1);assert.equal(flash.filter,'none','A future pulse must not freeze an earlier colour flash at its first frame');
    for(const [chapter,scene,t] of [['deep','south-atlantic',7],['nok','iron',6],['states','1991',5],['key','taken',20]]){
      await page.evaluate(args=>taswira.seek(...args),[chapter,scene,t]);
      await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      const first=await page.locator('#mapwrap').screenshot();
      await page.evaluate(()=>taswira.seek('deep','gondwana',12));
      await page.evaluate(args=>taswira.seek(...args),[chapter,scene,t]);
      await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      const second=await page.locator('#mapwrap').screenshot();
      assert.ok(first.equals(second),`${chapter}/${scene}: repeated exact-time seeks must produce identical pixels`);
      assert.equal(await page.locator('#mapwrap').evaluate(el=>el.getBoundingClientRect().width),1920);
      assert.equal(await page.locator('#mapwrap').evaluate(el=>el.getBoundingClientRect().height),1080);
      assert.ok((await page.locator('#video-credit').textContent()).length>10);
      assert.ok((await page.locator('#video-caution').textContent()).includes('Unreviewed draft'));
    }
    assert.equal(await page.evaluate(()=>{try{taswira.seek('missing',0,1);return false;}catch{return true;}}),true);
    assert.equal(await page.evaluate(()=>{try{taswira.seek('deep',0,NaN);return false;}catch{return true;}}),true);
    await page.evaluate(()=>taswira.seek('deep','south-atlantic',15));
    await page.evaluate(()=>taswira.exitVideo());
    assert.equal(await page.locator('#card').isVisible(),true);
    assert.equal(await page.evaluate(()=>captureClock),null);
    assert.ok(await page.evaluate(()=>Math.abs(gcam.lat)<=90&&Math.abs(gcam.lon)<=540&&Number.isFinite(gcam.k)),'Exiting capture must reset the globe clock');
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(()=>taswira.seek('deep','gondwana',0));
    assert.ok(await page.locator('#video-opening .intro-deck').evaluate(el=>el.getBoundingClientRect().bottom<=innerHeight),'Phone opening text must fit in the viewport');
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Phone video opening must not overflow horizontally');
    await page.evaluate(()=>taswira.seek('nok','iron',6));
    assert.ok(await page.evaluate(()=>Number.isFinite(map.getCenter().lat)&&Number.isFinite(map.getCenter().lng)),'Mobile preview must normalize Leaflet camera centers');
    await page.keyboard.press('Escape');
    assert.equal(await page.evaluate(()=>captureClock),null);
    await page.locator('#videobtn').click();
    assert.equal(await page.evaluate(()=>document.activeElement.id),'video-time');
    assert.equal(await page.locator('#video-caption').getAttribute('aria-hidden'),null);
    await page.locator('#video-time').evaluate(el=>{el.value=4;el.dispatchEvent(new Event('input'));});
    assert.equal(await page.evaluate(()=>state.t),4);
    await page.keyboard.press('Escape');
    assert.deepEqual(errors,[]);
    console.log('PASS: main-player seek API, pixel-identical globe/map/snapshot/campaign frames, 1080p layout, captions/credits/draft caveats, invalid input and normal-mode restoration.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

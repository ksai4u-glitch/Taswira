/* Phone layout, keyboard, contrast and chart-text checks for the built conflict map.
   node tests/map_phone_a11y_browser.cjs docs/index.html <folder with leaflet.js, leaflet.css, leaflet-heat.js> [screenshots folder]
   Set CHROMIUM to a browser path if Playwright's own Chromium isn't installed. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const [,,page,libs,shots]=process.argv;
const shot=async(p,name)=>{if(shots){fs.mkdirSync(shots,{recursive:true});await p.screenshot({path:path.join(shots,name+'.png')});}};
const lib=n=>fs.readFileSync(path.join(libs,n));
async function open(browser,viewport,theme){
  const phone=viewport.width<500;
  const ctx=await browser.newContext({viewport,deviceScaleFactor:phone?2:1,isMobile:phone,hasTouch:phone});
  await ctx.addInitScript(t=>{try{localStorage.setItem('taswira-theme',t);localStorage.removeItem('taswira-map-panel');}catch{}},theme);
  const p=await ctx.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.route('**/*',r=>{const u=r.request().url(),n=u.includes('leaflet-heat')?'leaflet-heat.js':u.includes('leaflet.css')?'leaflet.css':u.includes('leaflet.js')?'leaflet.js':null;
    if(u==='http://taswira.test/')return r.fulfill({contentType:'text/html',body:fs.readFileSync(page)});
    return n?r.fulfill({contentType:n.endsWith('css')?'text/css':'application/javascript',body:lib(n)}):r.abort();});
  await p.goto('http://taswira.test/');await p.waitForFunction(()=>typeof anim!=='undefined');
  // hotspot zones are worked out just after the first paint
  await p.waitForFunction(()=>!/Working out/.test(document.getElementById('zones-note').textContent));
  return {p,ctx,errors};
}
const noOverflow=p=>p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
// WCAG contrast ratio between two CSS colours, read in the page
const contrast=(p,fg,bg)=>p.evaluate(([fg,bg])=>{
  const rgb=c=>{const x=document.createElement('canvas').getContext('2d');x.fillStyle=c;const h=x.fillStyle;
    return h.startsWith('#')?[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)):h.match(/[\d.]+/g).slice(0,3).map(Number);};
  const L=c=>{const [r,g,b]=rgb(c).map(v=>{v/=255;return v<=.03928?v/12.92:((v+.055)/1.055)**2.4});return .2126*r+.7152*g+.0722*b;};
  const a=L(fg),b=L(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);},[fg,bg]);
const v=(p,name)=>p.evaluate(n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim(),name);

(async()=>{const browser=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM,args:['--no-sandbox']}:{});try{
for(const theme of ['dark','light']){
  // --- contrast of the panel text in both looks
  const {p,ctx,errors}=await open(browser,{width:1440,height:900},theme);
  for(const [fg,bg] of [['--text-primary','--surface-1'],['--text-secondary','--surface-1'],['--text-secondary','--surface-2'],
                        ['--text-muted','--surface-1'],['--text-muted','--surface-2'],['--accent','--surface-1']]){
    const r=await contrast(p,await v(p,fg),await v(p,bg));
    assert.ok(r>=4.5,`${theme}: ${fg} on ${bg} is ${r.toFixed(2)}:1, below 4.5:1`);
  }
  const link=p.locator('.leaflet-control-attribution a').first();
  const [lc,lb]=await link.evaluate(a=>[getComputedStyle(a).color,getComputedStyle(a.closest('.leaflet-control-attribution')).backgroundColor]);
  assert.ok(await contrast(p,lc,lb)>=4.5,`${theme}: attribution link contrast`);
  // --- every control has a name a screen reader can say
  const unnamed=await p.evaluate(()=>[...document.querySelectorAll('button,select,input,summary')].filter(el=>
    !(el.getAttribute('aria-label')||el.textContent.trim()||el.labels?.[0]?.textContent.trim())).map(el=>el.outerHTML.slice(0,60)));
  assert.deepEqual(unnamed,[],'controls without an accessible name');
  // --- the charts in words and as a table
  assert.match(await p.locator('#years-text').textContent(),/^Deaths per year: 2020 [\d,]+, .*Highest: \d{4}\.$/);
  assert.match(await p.locator('#months-text').textContent(),/^Deaths per month: /);
  const years=await p.locator('#years button').count();
  assert.equal(await p.locator('#chart-rows tr').count(),years+12);
  assert.equal(await p.locator('#years').getAttribute('aria-describedby'),'years-text');
  // year bars: named, and pressed when picked
  const y0=p.locator('#years button').first();
  assert.match(await y0.getAttribute('aria-label'),/^\d{4}: [\d,]+ deaths/);
  await y0.click();assert.equal(await y0.getAttribute('aria-pressed'),'true');
  await p.locator('#year-all').click();assert.equal(await y0.getAttribute('aria-pressed'),'false');
  // newest Candidate release note
  if(await p.locator('#prelim-note').isVisible())
    assert.match(await p.locator('#latest-note').textContent(),/^Newest release, GED Candidate \S+: [\d,]+ preliminary events added or updated/);
  // --- keyboard: a group row is a button; Enter filters the map to that group, Enter again shows all
  const row=p.locator('#groups-rows .row-link').first();
  await row.focus();await p.keyboard.press('Enter');
  assert.notEqual(await p.locator('#group').inputValue(),'');
  assert.equal(await p.locator('#groups-rows .row-link').first().getAttribute('aria-pressed'),'true');
  await p.locator('#groups-rows .row-link').first().focus();await p.keyboard.press('Enter');
  assert.equal(await p.locator('#group').inputValue(),'');
  assert.ok(await p.locator('#zones-rows .row-link').count()>0,'zone rows have buttons');
  // --- desktop play box clear of the Hide panel button
  await p.locator('#year-play').click();await p.waitForFunction(()=>anim.on);
  const tb=await p.locator('#map-panel-toggle').boundingBox(),pb=await p.locator('.play-box').boundingBox();
  assert.ok(pb.y>=tb.y+tb.height,'play box starts below the panel button');
  await p.keyboard.press('Escape');
  assert.deepEqual(errors,[]);await ctx.close();

  // --- phone, 360 px wide
  const ph=await open(browser,{width:360,height:740},theme),q=ph.p;
  assert.ok(await noOverflow(q),'no horizontal scroll on a 360 px phone');
  // the closed drawer shows the title, theme button and all three numbers in full
  const [statsBottom,panelTop]=await q.evaluate(()=>[document.querySelector('.stats').getBoundingClientRect().bottom,document.getElementById('panel').getBoundingClientRect().top]);
  assert.ok(statsBottom<=740+1&&statsBottom>panelTop,'numbers fully on screen in the closed drawer');
  await shot(q,`phone-${theme}`);
  // keyboard: tabbing into the closed drawer opens it, Esc closes it again
  await q.locator('#theme').focus();await q.keyboard.press('Tab');
  assert.equal(await q.locator('#drawer').getAttribute('aria-expanded'),'true');
  await q.keyboard.press('Escape');
  assert.equal(await q.locator('#drawer').getAttribute('aria-expanded'),'false');
  assert.equal(await q.evaluate(()=>document.activeElement.id),'drawer');
  // finger-sized controls in the open drawer
  await q.locator('#drawer').click();await q.waitForTimeout(350);
  const small=await q.evaluate(()=>[...document.querySelectorAll('#panel button:not(.row-link):not([data-year]):not([data-month]), #panel select, #panel label, #map-panel-toggle')]
    .filter(el=>el.offsetParent&&el.getBoundingClientRect().height<44).map(el=>el.id||el.textContent.trim().slice(0,30)));
  assert.deepEqual(small,[],'controls under 44 px tall on a phone');
  assert.ok(await noOverflow(q));await shot(q,`phone-${theme}-open`);
  // playing: every play-box button is on screen and nothing covers it
  await q.locator('#year-play').click();await q.waitForFunction(()=>anim.on);
  await q.locator('input[value="points"]').evaluate(r=>{r.checked=true;r.dispatchEvent(new Event('change'));});
  const covered=await q.evaluate(()=>[...document.querySelectorAll('.play-box button')].filter(b=>!b.hidden).filter(b=>{
    const r=b.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
    return r.right>innerWidth||r.left<0||!(hit===b||b.contains(hit))||r.height<40;}).map(b=>b.className));
  assert.deepEqual(covered,[],'play-box buttons covered, off screen or too small');
  assert.ok(await noOverflow(q));await shot(q,`phone-${theme}-play`);
  assert.deepEqual(ph.errors,[]);await ph.ctx.close();
}
console.log('PASS: phone layout at 360 px (drawer, play box, touch targets), keyboard drawer and table rows, contrast in both looks, chart text and newest-release note.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

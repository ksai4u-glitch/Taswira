const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=process.argv[3];
if(!process.argv[2]||!root)throw Error('Usage: node tests/history_browser.cjs <built HTML> <local dependency directory> [screenshots directory]');
const screenshots=process.argv[4];
const html=fs.readFileSync(process.argv[2],'utf8');
(async()=>{
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const results=[];
try{
for(const viewport of [{width:1440,height:900},{width:390,height:844}]){
const page=await browser.newPage({viewport});const errors=[],tiles=[];
page.on('pageerror',e=>errors.push(e.message));
await page.route('**/*',route=>{
const url=route.request().url();let name;
if(url.includes('leaflet.css'))name='leaflet.css';else if(url.includes('leaflet.js'))name='leaflet.js';
else if(url.includes('d3-array'))name='d3-array.js';else if(url.includes('d3-geo'))name='d3-geo.js';
if(name)return route.fulfill({contentType:name.endsWith('css')?'text/css':'application/javascript',body:fs.readFileSync(path.join(root,name),'utf8')});
if(url.includes('arcgisonline.com')){tiles.push(url);return route.fulfill({status:200,contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==','base64')});}
return route.abort();
});
await page.setContent(html);await page.waitForFunction(()=>typeof DATA!=='undefined'&&state.drawn!==null);
assert.equal(await page.evaluate(()=>L.version),'1.9.4');
assert.equal(tiles.length,0,'Historical opening must not request Esri tiles');
await page.evaluate(()=>{window.tileCalls=[];const create=modernTiles.createTile;modernTiles.createTile=function(...args){window.tileCalls.push(scene().base);return create.apply(this,args);};});
const chapters=await page.evaluate(()=>DATA.chapters.map(c=>({id:c.id,scenes:c.scenes.map(s=>({id:s.id,modern:s.base==='modern'}))})));
let scenes=0;
for(const mode of ['jump','play','reduced']){
await page.emulateMedia({reducedMotion:mode==='reduced'?'reduce':'no-preference'});
for(let c=0;c<chapters.length;c++)for(let s=0;s<chapters[c].scenes.length;s++){
const info=await page.evaluate(({c,s,mode})=>{
setPlaying(false);goTo(c,s,{animate:false,live:mode!=='jump'});
if(mode==='play'){setPlaying(true);state.t=lead()+scene().duration*.5;}frame(performance.now());paint(performance.now());setPlaying(false);
return {base:scene().base,title:document.querySelector('#scene-title').textContent,states:!!scene().snapshot,note:document.querySelector('#card').textContent.includes('Modern reference map.'),esri:typeof modernTiles!=='undefined'?map.hasLayer(modernTiles):true};
},{c,s,mode});
assert.ok(info.title);if(info.base==='modern'){assert.ok(info.note);assert.ok(info.esri);}else{assert.equal(info.esri,false);}
if(info.states){assert.equal(info.base,'period');assert.ok(await page.locator('.leaflet-overlay-pane path').count());}
scenes++;
}
}
assert.deepEqual(errors,[]);assert.equal(await page.evaluate(()=>window.tileCalls.every(base=>base==='modern')),true);
await page.evaluate(()=>{const c=DATA.chapters.findIndex(c=>c.id==='states');goTo(c,0,{animate:false});});
if(screenshots){fs.mkdirSync(screenshots,{recursive:true});await page.screenshot({path:path.join(screenshots,`states-${viewport.width}.png`)});}
results.push({viewport,scenes,pageErrors:errors.length,esriRequestsOnlyInReference:true});await page.close();
}
console.log(JSON.stringify(results));
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

/* Capture the live Kano scene (hausa/kano at 34 s) from docs/history.html as mock-up map backgrounds.
 * From the repo root: python -m http.server 8765, then node design/kano-journey/capture-map.cjs
 * Writes img/map-kano-desktop.png (1000x640) and img/map-kano-phone.png (390x420) at 2x. Read-only for docs/.
 */
const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();
for (const [name,w,h,t,sc] of [['map-kano-desktop',1000,640,34,'kano'],['map-kano-phone',390,420,34,'kano']]){
 const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:2});
 await p.goto('http://127.0.0.1:8765/docs/history.html#chapter=hausa&scene='+sc,{waitUntil:'load'});
 await p.waitForTimeout(2500);
 await p.evaluate(()=>{try{localStorage.setItem('taswira-history-guide','off')}catch{}});
 await p.evaluate(([t,sc])=>{ window.taswira.seek('hausa',sc,t); },[t,sc]);
 await p.waitForTimeout(2500);
 await p.addStyleTag({content:'#ov-top,#ov-bottom,#story-guide,#video-caption,#video-caution,#video-credit,#title-card,#grain,.lb,#exit-video,#video-tools,#globe-credit,#draft,header,#controls,#card{display:none!important} #mapwrap{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important}'});
 await p.evaluate(()=>{dispatchEvent(new Event('resize'))}); await p.waitForTimeout(1500);
 await p.evaluate(([t,sc])=>{ window.taswira.seek('hausa',sc,t); },[t,sc]); await p.waitForTimeout(1500);
 await p.screenshot({path:''+require('node:path').join(__dirname,'img')+'/'+name+'.png'});
 await p.close();}
await b.close();})();

/* Offline 1080p/30fps pilot. Requires Playwright, Chromium, ffmpeg and locally cached CDN assets.
 * node capture_history.cjs <built HTML> <dependency directory> <output.mp4> [fps] [seconds per shot] [shot-plan.json]
 * Does not publish, fetch data, or overwrite existing outputs. No audio is added.
 */
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process');
const {chromium}=require('playwright');
const SHOTS=[['deep','gondwana'],['deep','south-atlantic'],['nok','terracottas'],['nok','iron']];
const timestamp=seconds=>{
  const ms=Math.round(seconds*1000),h=Math.floor(ms/3600000),m=Math.floor(ms/60000)%60,s=Math.floor(ms/1000)%60;
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}.${String(ms%1000).padStart(3,'0')}`;
};
function validateShotPlan(plan){
  if(!plan||!Array.isArray(plan.shots)||!plan.shots.length||plan.shots.length>40)throw Error('Shot plan needs 1–40 shots');
  for(const shot of plan.shots)if(!shot||!['chapter','scene'].every(k=>typeof shot[k]==='string'&&/^[a-z0-9-]+$/.test(shot[k]))||!Number.isFinite(shot.from)||!Number.isFinite(shot.to)||shot.from<0||shot.to<=shot.from||shot.to-shot.from>60)throw Error('Each shot needs chapter, scene and finite in/out times spanning at most60seconds');
  return plan.shots;
}
function creditLines(manifest){
  const lines=['Unreviewed draft · Original Taswira guide and schematic architecture.',
    'Physical geography: Natural Earth · public domain.',
    'Historical sources and reuse notes: see the companion source manifest.',
    'No recorded narration or music.'];
  if(manifest.clips.some(clip=>clip.base==='deep'))lines.splice(2,0,
    'Plate model: Merdith et al. (2021), v1.2.4 · simplified and interpolated.',
    'Model: doi.org/10.5281/zenodo.13635864',
    'CC BY 4.0: creativecommons.org/licenses/by/4.0/');
  return lines;
}
const creditSeconds=manifest=>manifest.clips.some(clip=>clip.base==='deep')?16:10;
async function renderCredits(page,title="Taswira · History video pilot",manifest={clips:[{base:'deep'}]}){
    await page.evaluate(({title,lines})=>{
      const card=document.createElement('div');card.style.cssText='position:absolute;inset:0;z-index:1900;background:#08120e;color:#f0eee2;padding:100px 120px;font:26px/1.7 system-ui';
      const heading=document.createElement('h1');heading.textContent=title;heading.style.cssText='font:48px Georgia,serif;color:#d4b57a';card.append(heading);
      for(const text of lines){
        const p=document.createElement('p');p.textContent=text;card.append(p);
      }document.getElementById('mapwrap').append(card);
    },{title,lines:creditLines(manifest)});
}
async function capture(htmlFile,deps,output,fps=30,shotSeconds=8,shotPlan=null){
  const planned=shotPlan?validateShotPlan(shotPlan):null;
  if(!Number.isInteger(fps)||fps<1||fps>60||!Number.isFinite(shotSeconds)||shotSeconds<1||shotSeconds>60)
    throw Error('fps must be an integer 1–60; seconds per shot must be 1–60');
  if(!htmlFile||!deps||!output)throw Error('Usage: node capture_history.cjs <HTML> <deps> <output.mp4> [fps] [seconds per shot]');
  if(!output.toLowerCase().endsWith('.mp4'))throw Error('Output must end in .mp4');
  const stem=output.replace(/\.mp4$/i,'');
  for(const file of [output,stem+'.vtt',stem+'.sources.json'])if(fs.existsSync(file))throw Error('Output already exists: '+file);
  for(const file of ['leaflet.js','leaflet.css','d3-array.js','d3-geo.js'])fs.accessSync(path.join(deps,file));
  const html=fs.readFileSync(htmlFile,'utf8');fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  let encoder,finished=false,stderr='',temporary,closed=false;
  const created=[];
  try{
    const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1,reducedMotion:'no-preference'});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',route=>{
      const u=route.request().url(),name=u.includes('leaflet.css')?'leaflet.css':u.includes('leaflet.js')?'leaflet.js':u.includes('d3-array')?'d3-array.js':u.includes('d3-geo')?'d3-geo.js':null;
      return name?route.fulfill({contentType:name.endsWith('css')?'text/css':'application/javascript',body:fs.readFileSync(path.join(deps,name),'utf8')}):route.abort();
    });
    await page.setContent(html);await page.waitForFunction(()=>typeof window.taswira?.seek==='function');
    await page.evaluate(()=>document.fonts.ready);
    await page.evaluate(()=>window.taswira.ready?.());
    await page.addStyleTag({content:'#exit-video,#video-tools{visibility:hidden!important}'});
    const manifest={title:shotPlan?.title||'Taswira · History video pilot',width:1920,height:1080,fps,clips:[],sources:{},status:'Unreviewed draft; rights and historian review required before publication'};
    for(const shot of planned||SHOTS.map(([chapter,scene])=>({chapter,scene}))){
      const {chapter,scene}=shot;
      const info=await page.evaluate(([c,s])=>taswira.info(c,s),[chapter,scene]);
      if(info.base==='modern')throw Error('Modern basemap capture is excluded until video rights are cleared');
      const from=planned?shot.from:scene==='gondwana'?0:info.contentStart;
      const to=planned?shot.to:Math.min(info.duration,from+shotSeconds);
      if(to>info.duration)throw Error('Shot exceeds scene duration: '+chapter+'/'+scene);
      manifest.clips.push({...info,from,to,seconds:planned?to-from:shotSeconds});
    }
    const creditsFrames=creditSeconds(manifest)*fps;
    temporary=fs.mkdtempSync(path.join(path.dirname(path.resolve(output)),'.taswira-capture-'));
    const temporaryVideo=path.join(temporary,'video.mp4');
    encoder=spawn(process.env.FFMPEG_PATH||'ffmpeg',['-n','-loglevel','error','-f','image2pipe','-vcodec','png','-r',String(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',temporaryVideo],{stdio:['pipe','ignore','pipe']});
    const done=new Promise((resolve,reject)=>{encoder.on('error',reject);encoder.on('close',code=>{closed=true;code===0?resolve():reject(Error('ffmpeg failed: '+stderr));});});
    // Keep rejection handled until awaited after all frames.
    done.catch(()=>{});encoder.stderr.on('data',chunk=>{stderr=(stderr+chunk.toString()).slice(-5000);});
    encoder.stdin.on('error',()=>{}); // write callbacks below report broken pipes without an unhandled event
    const write=buffer=>Promise.race([
      new Promise((resolve,reject)=>encoder.stdin.write(buffer,error=>error?reject(error):resolve())),
      done.then(()=>{throw Error('Encoder exited before all frames were written');})
    ]);
    const cues=[];let frame=0,lastCaption='',cueStart=0,lastImage=null;
    const recordCaption=(text,at)=>{
      if(text===lastCaption)return;
      if(lastCaption)cues.push({start:cueStart,end:at,text:lastCaption});lastCaption=text;cueStart=at;
    };
    const push=async()=>{if(errors.length)throw Error(errors.join('\n'));const png=await page.locator('#mapwrap').screenshot();await write(png);lastImage=png;frame++;};
    manifest.transition='0.45-second dissolve into each later shot';
    for(const [clipIndex,clip] of manifest.clips.entries()){
      const framesPerShot=Math.round(clip.seconds*fps);
      if(clipIndex&&lastImage)await page.evaluate(src=>{
        document.getElementById('shot-dissolve')?.remove();
        const image=document.createElement('img');image.id='shot-dissolve';image.src=src;
        image.style.cssText='position:absolute;inset:0;width:100%;height:100%;z-index:1800;pointer-events:none';
        document.getElementById('mapwrap').append(image);
      },'data:image/png;base64,'+lastImage.toString('base64'));
      for(let i=0;i<framesPerShot;i++){
        const t=clip.from+(clip.to-clip.from)*i/Math.max(1,framesPerShot-1);
        const caption=await page.evaluate(({clip,t})=>{taswira.seek(clip.chapter,clip.scene,t);return document.getElementById('video-caption').textContent;},{clip,t});
        await page.evaluate(opacity=>{const image=document.getElementById('shot-dissolve');if(image)image.style.opacity=opacity;},Math.max(0,1-i/(fps*.45)));
        recordCaption(caption,frame/fps);await push();
      }
      console.log(`Captured ${clip.chapter}/${clip.scene}: ${framesPerShot} frames`);
    }
    recordCaption('',frame/fps);
    manifest.sources=await page.evaluate(shots=>{
      const ids=new Set(['natural-earth']);
      if(shots.some(([c,s])=>DATA.chapters.find(ch=>ch.id===c).scenes.find(sc=>sc.id===s).base==='deep'))ids.add('merdith-2021');
      for(const [c,s] of shots){const ch=DATA.chapters.find(ch=>ch.id===c),sc=ch.scenes.find(sc=>sc.id===s);sc.sources.forEach(id=>ids.add(id));for(const id of sc.show||[])for(const source of ch.features[id].sources||[])ids.add(source);}
      return Object.fromEntries([...ids].map(id=>[id,DATA.sources[id]]));
    },manifest.clips.map(c=>[c.chapter,c.scene]));
    await renderCredits(page,shotPlan?.title||"Taswira · History video pilot",manifest);
    const creditImage=await page.locator('#mapwrap').screenshot();
    for(let i=0;i<creditsFrames;i++){await write(creditImage);frame++;}
    encoder.stdin.end();await done;
    fs.copyFileSync(temporaryVideo,output,fs.constants.COPYFILE_EXCL);created.push(output);
    fs.writeFileSync(stem+'.vtt','WEBVTT\n\n'+cues.map((cue,i)=>`${i+1}\n${timestamp(cue.start)} --> ${timestamp(cue.end)}\n${cue.text}\n`).join('\n'),{flag:'wx'});created.push(stem+'.vtt');
    manifest.duration=frame/fps;manifest.frames=frame;
    fs.writeFileSync(stem+'.sources.json',JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});created.push(stem+'.sources.json');finished=true;
    console.log(`Wrote ${output}: ${frame} frames, ${manifest.duration}s at ${fps}fps, 1920×1080; captions and sources alongside.`);
  }finally{
    if(encoder&&!closed)await new Promise(resolve=>{encoder.once('close',resolve);encoder.kill();});
    if(!finished)for(const file of created)fs.unlinkSync(file);
    if(temporary)fs.rmSync(temporary,{recursive:true,force:true});
    await browser.close();
  }
}
if(require.main===module)capture(process.argv[2],process.argv[3],process.argv[4],Number(process.argv[5]||30),Number(process.argv[6]||8),process.argv[7]?JSON.parse(fs.readFileSync(process.argv[7],'utf8')):null).catch(e=>{console.error(e.message);process.exitCode=1;});
module.exports={capture,timestamp,renderCredits,validateShotPlan,creditLines,creditSeconds};

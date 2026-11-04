/* Offline preview. Every canvas frame is derived from scene + progress; no wall-clock effects. */
"use strict";
const DATA = JSON.parse(document.getElementById("director-data").textContent);
const $ = id => document.getElementById(id);
const canvas = $("world"), ctx = canvas.getContext("2d");
const motion = matchMedia("(prefers-reduced-motion: reduce)");
const state = { chapter: 0, scene: 0, progress: 0, playing: false };
let width = 1, height = 1, frameId = null, lastTime = null;
const chapter = () => DATA.chapters[state.chapter];
const scene = () => chapter().scenes[state.scene];
const clamp = x => Math.max(0, Math.min(1, x));
const RAD = Math.PI / 180;
const unit = (lat, lon) => [Math.cos(lat * RAD) * Math.cos(lon * RAD), Math.cos(lat * RAD) * Math.sin(lon * RAD), Math.sin(lat * RAD)];
const dot = (a, b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
const norm = v => { const n = Math.hypot(...v); return v.map(x => x/n); };
const turn = (q, v) => {
  const [w,x,y,z] = q, [a,b,c] = v;
  const cx=y*c-z*b, cy=z*a-x*c, cz=x*b-y*a;
  return [a+2*(w*cx+y*cz-z*cy),b+2*(w*cy+z*cx-x*cz),c+2*(w*cz+x*cy-y*cx)];
};
function blend(a,b,t) {
  let d=a.reduce((s,v,i)=>s+v*b[i],0);
  if(d<0){b=b.map(x=>-x);d=-d;}
  if(d>.9995)return norm(a.map((x,i)=>x+(b[i]-x)*t));
  const theta=Math.acos(Math.min(1,d)), s=Math.sin(theta);
  return a.map((x,i)=>(x*Math.sin((1-t)*theta)+b[i]*Math.sin(t*theta))/s);
}
const rotations = {};
for(const [id,rows] of Object.entries(DATA.plates.rotations))
  rotations[id]=(typeof rows==="string"?DATA.plates.rotations[rows]:rows).map(q=>q&&q.map(x=>x/DATA.plates.scale));
const shapes=DATA.plates.shapes.map(s=>({...s, vectors:s.ring.map(([lat,lon])=>unit(lat/DATA.plates.precision,lon/DATA.plates.precision))}));
function rotation(id,ma){
  const rows=rotations[id];if(!rows)return null;
  const f=Math.max(0,Math.min(rows.length-1,ma/(DATA.plates.times[1]-DATA.plates.times[0])));
  const i=Math.min(rows.length-2,Math.floor(f)),t=f-i;
  return rows[i]&&rows[i+1]?blend(rows[i],rows[i+1],t):(t<.5?rows[i]:rows[i+1]);
}
function decode(flat){let lat=0,lon=0,out=[];for(let i=0;i<flat.length;i+=2){lat+=flat[i];lon+=flat[i+1];out.push([lat/1000,lon/1000]);}return out;}
const physical={land:DATA.background.land.map(p=>p.map(decode)), lakes:DATA.background.lakes.map(p=>p.map(decode)), rivers:DATA.background.rivers.map(([rank,f])=>[rank,decode(f)])};
const stars=Array.from({length:110},(_,i)=>({x:((i*73.73)%101)/101,y:((i*43.37)%97)/97,r:i%7===0?1:.5}));
function dateLabel(year){
  if(chapter().clock==="ago"){
    const ago=Math.max(0,2000-year);
    return ago>=1e6?`${(ago/1e6).toFixed(ago>=1e8?0:1).replace(/\.0$/,'')} million years ago`:ago<100?"Today":`${Math.round(ago).toLocaleString("en-GB")} years ago`;
  }
  const n=Math.round(year);return n<0?`${Math.abs(n).toLocaleString("en-GB")} BCE`:`${Math.max(1,n)} CE`;
}
function basis(v){const lon=Math.atan2(v[1],v[0]),lat=Math.asin(v[2]);return {right:[-Math.sin(lon),Math.cos(lon),0],up:[-Math.sin(lat)*Math.cos(lon),-Math.sin(lat)*Math.sin(lon),Math.cos(lat)],front:v};}
function clip(points,front){
  const out=[];
  for(let i=0;i<points.length;i++){
    const a=points[i],b=points[(i+1)%points.length],da=dot(a,front),db=dot(b,front);
    if(da>=0)out.push(a);
    if((da>=0)!==(db>=0)){const t=da/(da-db);out.push(norm(a.map((x,k)=>x+(b[k]-x)*t)));}
  }
  return out;
}
function strokeLine(points,project,color,lineWidth=1){
  ctx.beginPath();let open=false;
  for(const v of points){const p=project(v);if(p[2]<0){open=false;continue;}if(open)ctx.lineTo(p[0],p[1]);else ctx.moveTo(p[0],p[1]);open=true;}
  ctx.strokeStyle=color;ctx.lineWidth=lineWidth;ctx.stroke();
}
function globe(year){
  const mobile=width<600;
  const cx=mobile?width*.52:width*.71,cy=mobile?535:height*.43;
  const sc=scene(),ma=Math.max(0,(2000-year)/1e6);
  const zoom=1+Math.log2(Math.max(1,sc.camera.zoom))*.45;
  const radius=(mobile?Math.min(160,width*.42):Math.min(width*.28,height*.335))*zoom;
  const q=rotation(sc.camera.plate,ma),target=unit(...sc.camera.center);
  const camera=basis(q?turn(q,target):target);
  const project=v=>[cx+radius*dot(v,camera.right),cy-radius*dot(v,camera.up),dot(v,camera.front)];
  // Orbital guides are decoration, not plate boundaries.
  ctx.save();ctx.translate(cx,cy);ctx.rotate(-.38);ctx.strokeStyle="#8fa9a31a";ctx.lineWidth=.7;
  for(const k of [1.12,1.25]){ctx.beginPath();ctx.ellipse(0,0,radius*k,radius*.32,0,0,Math.PI*2);ctx.stroke();}ctx.restore();
  const halo=ctx.createRadialGradient(cx,cy,radius*.7,cx,cy,radius*1.17);halo.addColorStop(0,"#43887900");halo.addColorStop(.65,"#43887912");halo.addColorStop(1,"#43887900");
  ctx.fillStyle=halo;ctx.fillRect(cx-radius*1.2,cy-radius*1.2,radius*2.4,radius*2.4);
  ctx.save();ctx.beginPath();ctx.arc(cx,cy,radius,0,Math.PI*2);ctx.clip();
  const sea=ctx.createRadialGradient(cx-radius*.45,cy-radius*.6,0,cx,cy,radius*1.4);sea.addColorStop(0,"#25403e");sea.addColorStop(.6,"#122727");sea.addColorStop(1,"#080f12");ctx.fillStyle=sea;ctx.fillRect(cx-radius,cy-radius,radius*2,radius*2);
  for(let lat=-60;lat<=60;lat+=30)strokeLine(Array.from({length:181},(_,i)=>unit(lat,-180+i*2)),project,"#c2d7c315",.6);
  for(let lon=-180;lon<180;lon+=30)strokeLine(Array.from({length:91},(_,i)=>unit(-90+i*2,lon)),project,"#c2d7c315",.6);
  const light=ctx.createLinearGradient(cx-radius,cy-radius,cx+radius,cy+radius);light.addColorStop(0,"#c1ac78");light.addColorStop(.5,"#8b8763");light.addColorStop(1,"#45594b");
  const turns={};
  for(const s of shapes){
    if(ma>s.from||ma<s.to)continue;
    const r=turns[s.plate]||(turns[s.plate]=rotation(s.plate,ma));if(!r)continue;
    const pts=clip(s.vectors.map(v=>turn(r,v)),camera.front);if(pts.length<3)continue;
    ctx.beginPath();pts.forEach((v,i)=>{const p=project(v);i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]);});ctx.closePath();ctx.fillStyle=light;ctx.fill();ctx.strokeStyle="#b4ab7955";ctx.lineWidth=.7;ctx.stroke();
  }
  for(const id of sc.show||[]){
    const f=chapter().features[id];if(f.kind!=="line")continue;
    const active=ma<=f.active[0]&&ma>=f.active[1],r=rotation(f.plate,ma);
    if(r)strokeLine(f.path.map(ll=>turn(r,unit(...ll))),project,active?"#efa76f":"#594c36",active?2:1);
  }
  const shade=ctx.createLinearGradient(cx-radius,0,cx+radius,0);shade.addColorStop(0,"#00100900");shade.addColorStop(.6,"#00100900");shade.addColorStop(1,"#000b16a0");ctx.fillStyle=shade;ctx.fillRect(cx-radius,cy-radius,radius*2,radius*2);ctx.restore();
  ctx.beginPath();ctx.arc(cx,cy,radius,0,Math.PI*2);ctx.strokeStyle="#9fb9a050";ctx.lineWidth=1;ctx.stroke();
  const labels=[];
  for(const id of sc.show||[]){
    const f=chapter().features[id];if(f.kind!=="point"||f.form==="landmass")continue;
    const r=rotation(f.plate,ma),p=project(r?turn(r,unit(...f.coordinates)):unit(...f.coordinates));
    if(p[2]<0)continue;
    const offset=[0,-22,22,-44,44].find(d=>!labels.some(y=>Math.abs(y-(p[1]+d))<18))||0;labels.push(p[1]+offset);
    marker(p[0],p[1],id==="nigeria-today"?"NIGERIA'S ROCK":f.short||f.name,f.status==="disputed",0,offset);
  }
}
function marker(x,y,name,disputed,uncertainty,labelOffset=0){
  ctx.save();ctx.strokeStyle=disputed?"#e0ad78":"#d4b57a";ctx.fillStyle="#f2dfb6";
  if(uncertainty){ctx.setLineDash([3,5]);ctx.beginPath();ctx.arc(x,y,uncertainty,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);}
  ctx.beginPath();ctx.arc(x,y,11,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill();
  ctx.font="10px Arial";ctx.letterSpacing=".5px";
  const text=name+(disputed?" · DISPUTED":""),side=x+38+ctx.measureText(text).width>width-15?-1:1;
  ctx.beginPath();ctx.moveTo(x+side*12,y);ctx.lineTo(x+side*24,y+labelOffset);ctx.lineTo(x+side*31,y+labelOffset);ctx.stroke();
  ctx.textAlign=side<0?"right":"left";ctx.shadowColor="#080f11";ctx.shadowBlur=5;ctx.fillText(text,x+side*38,y+labelOffset+3);ctx.restore();
}
function region(){
  const sc=scene(),mobile=width<600;
  const cx=mobile?width*.48:width*.72,cy=mobile?520:height*.43;
  const scale=(mobile?31:Math.min(width*.027,height*.045))*Math.pow(1.25,sc.camera.zoom-6);
  const [lat,lon]=sc.camera.center;
  const project=([la,lo])=>[cx+(lo-lon)*scale*Math.cos(lat*RAD),cy-(la-lat)*scale];
  function path(rings){ctx.beginPath();rings.forEach(r=>{r.forEach((v,i)=>{const p=project(v);i?ctx.lineTo(...p):ctx.moveTo(...p);});ctx.closePath();});}
  ctx.save();
  physical.land.forEach(p=>{path(p);ctx.fillStyle="#243a32";ctx.fill("evenodd");ctx.strokeStyle="#53685866";ctx.lineWidth=.8;ctx.stroke();});
  physical.lakes.forEach(p=>{path(p);ctx.fillStyle="#0c2429";ctx.fill("evenodd");});
  physical.rivers.forEach(([rank,line])=>{ctx.beginPath();line.forEach((v,i)=>{const p=project(v);i?ctx.lineTo(...p):ctx.moveTo(...p);});ctx.lineWidth=rank<=3?1.8:.7;ctx.strokeStyle=rank<=3?"#75ada5":"#49756c77";ctx.stroke();});
  // Geographic grid, never modern political boundaries.
  ctx.strokeStyle="#c8cf9b0d";ctx.lineWidth=.6;
  for(let la=-20;la<=40;la+=2){const a=project([la,-20]),b=project([la,40]);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();}
  const features=chapter().features,labelRows=[];
  for(const id of sc.show||[]){const f=features[id];if(f.kind!=="point")continue;const [x,y]=project(f.coordinates);if(x<0||x>width||y<0||y>height)continue;
    const alpha=(sc.dim||[]).includes(id)?.45:1;ctx.globalAlpha=alpha;
    const offset=[0,-20,20,-40,40].find(d=>!labelRows.some(row=>Math.abs(row-(y+d))<17))||0;
    labelRows.push(y+offset);
    marker(x,y,f.short||f.name,f.status==="disputed",f.uncertainty_km?f.uncertainty_km*scale/111:0,offset);
  }
  ctx.restore();
  // Fade the physical map under the reading column, leaving the right-hand map clear.
  if(!mobile){const fade=ctx.createLinearGradient(0,0,width*.6,0);fade.addColorStop(0,"#080f11");fade.addColorStop(.6,"#080f11f5");fade.addColorStop(1,"#080f1100");ctx.fillStyle=fade;ctx.fillRect(0,0,width,height);}
}
function paint(){
  ctx.clearRect(0,0,width,height);
  ctx.fillStyle="#b5c6af";for(const s of stars){ctx.globalAlpha=.12;ctx.beginPath();ctx.arc(s.x*width,s.y*height,s.r,0,Math.PI*2);ctx.fill();}ctx.globalAlpha=1;
  const sc=scene(),year=sc.when.from+(sc.when.to-sc.when.from)*state.progress;
  if(sc.view==="globe")globe(year);else region();
  if(sc.view==="globe"&&width>=600){const fade=ctx.createLinearGradient(0,0,width*.52,0);fade.addColorStop(0,"#080f11");fade.addColorStop(.55,"#080f11f0");fade.addColorStop(1,"#080f1100");ctx.fillStyle=fade;ctx.fillRect(0,110,width,height-110);}
  $("year").textContent=dateLabel(year);
  const sentences=sc.text.match(/[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$/g)||[sc.text];
  $("caption").textContent=sentences[Math.min(sentences.length-1,Math.floor(state.progress*sentences.length))].trim();
  $("scrub").value=Math.round(state.progress*1000);
  $("scrub").setAttribute("aria-valuetext",`${dateLabel(year)}, ${Math.round(state.progress*100)} percent through scene`);
}
function resize(){
  const r=$("experience").getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);
  width=r.width;height=r.height;canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);paint();
}
function pause(){state.playing=false;if(frameId!==null)cancelAnimationFrame(frameId);frameId=null;lastTime=null;$("play").textContent=state.progress>=1?"↺  Replay scene":"▶︎  Continue the journey";}
function tick(now){
  if(!state.playing)return;
  if(lastTime!==null)state.progress=clamp(state.progress+Math.min((now-lastTime)/1000,.1)/scene().duration);
  lastTime=now;
  if(state.progress>=1){
    if(state.scene<chapter().scenes.length-1){select(state.chapter,state.scene+1,false);state.playing=true;}
    else if(state.chapter<DATA.chapters.length-1){select(state.chapter+1,0,false);state.playing=true;}
    else{paint();pause();return;}
  }
  paint();frameId=requestAnimationFrame(tick);
}
function play(){
  if(state.playing){pause();return;}
  if(state.progress>=1)state.progress=0;
  state.playing=true;lastTime=null;$("play").textContent="Ⅱ  Pause the journey";frameId=requestAnimationFrame(tick);
}
function select(c,s,announce=true){
  const sceneFocus=!!document.activeElement?.closest("#scenes"),chapterFocus=!!document.activeElement?.closest("#chapters");
  state.chapter=c;state.scene=s;state.progress=0;lastTime=null;
  const ch=chapter(),sc=scene(),deep=ch.id==="deep";
  $("eyebrow").textContent=`CHAPTER ${String(c+1).padStart(2,"0")} / ${deep?"DEEP TIME":"THE NOK WORLD"}`;
  $("headline").innerHTML=deep?"Before the<br>borders.<em>The land moved.</em>":"Earth. Fire.<br>Human hands.<em>The Nok world.</em>";
  $("deck").textContent=deep?"Follow the land that became Nigeria, from moving continents to the farmers, sculptors and ironworkers of Nok.":"An archaeological story of farming, clay sculpture and iron working in central Nigeria. Discover the evidence, and the questions it leaves open.";
  $("location").textContent=sc.view==="globe"?"DEEP TIME · MODEL RECONSTRUCTION":"NIGER BASIN · APPROXIMATE PHYSICAL GEOGRAPHY";
  $("scene-title").textContent=sc.title;
  $("counter").textContent=`${String(s+1).padStart(2,"0")} / ${String(ch.scenes.length).padStart(2,"0")}`;
  $("from").textContent=dateLabel(sc.when.from);$("to").textContent=dateLabel(sc.when.to);
  const disputed=!!sc.disputed||(sc.show||[]).some(id=>ch.features[id].status==="disputed");
  $("certainty").textContent=sc.view==="globe"?"MODEL RECONSTRUCTION · Modern continental outlines, not ancient coastlines.":disputed?"DISPUTED EVIDENCE · See sources and notes for the disagreement.":"APPROXIMATE GEOGRAPHY · Today's rivers and coastline; dated sites, no political borders.";
  if(sc.disputed)$("certainty").textContent="DISPUTED DATING · "+$("certainty").textContent;
  $("credit").innerHTML=sc.view==="globe"?'Continents: <a href="https://doi.org/10.5281/zenodo.13635864">Merdith et al. (2021)</a> · CC BY 4.0':'Physical geography: Natural Earth · Public domain';
  $("scenes").replaceChildren(...ch.scenes.map((v,i)=>{const b=document.createElement("button");b.type="button";b.setAttribute("aria-current",String(i===s));const n=document.createElement("span");n.className="n";n.textContent=String(i+1).padStart(2,"0");b.append(n,document.createTextNode(v.title));b.onclick=()=>{pause();select(c,i);};return b;}));
  $("chapters").replaceChildren(...DATA.chapters.map((v,i)=>{const b=document.createElement("button");b.type="button";b.textContent=i===0?"01  Deep time":"02  The Nok world";b.setAttribute("aria-current",String(i===c));b.onclick=()=>{pause();select(i,0);};return b;}));
  if(sceneFocus)$("scenes").children[s].focus({preventScroll:true});
  if(chapterFocus)$("chapters").children[c].focus({preventScroll:true});
  $("next-chapter").textContent=deep?"Explore Nok →":"Return to deep time →";
  $("previous").disabled=c===0&&s===0;$("next").disabled=c===DATA.chapters.length-1&&s===ch.scenes.length-1;
  $("play").textContent=state.playing?"Ⅱ  Pause the journey":"▶︎  Begin the journey";
  if(announce)$("announce").textContent=`${ch.title}. ${sc.when.label}. ${sc.title}`;
  if($("evidence").open)fillEvidence();
  paint();
}
function step(dir){
  let c=state.chapter,s=state.scene+dir;
  if(s<0&&c>0){c--;s=DATA.chapters[c].scenes.length-1;}else if(s>=chapter().scenes.length&&c<DATA.chapters.length-1){c++;s=0;}
  if(s<0||s>=DATA.chapters[c].scenes.length)return;
  pause();select(c,s);
}
function fillEvidence(){
  const sc=scene(),ch=chapter(),root=$("evidence-content");root.replaceChildren();
  const p=document.createElement("p");p.textContent=sc.text;root.append(p);
  if(sc.disputed){const dispute=document.createElement("p");dispute.textContent=`Disputed: ${sc.disputed}`;root.append(dispute);}
  const note=document.createElement("p");note.className="note";note.textContent=$("certainty").textContent;root.append(note);
  const ids=new Set(sc.sources);
  for(const id of sc.show||[]){const f=ch.features[id];(f.sources||[]).forEach(s=>ids.add(s));
    if(f.kind==="point"&&f.form!=="landmass"){const detail=document.createElement("p");detail.className="note";detail.textContent=`${f.name} — ${f.status}. ${f.evidence}. Location: ${f.location}`;root.append(detail);}
    if(f.disputed){const p=document.createElement("p");p.textContent=`${f.name} — disputed: ${f.disputed}`;root.append(p);}}
  if(sc.view==="globe")ids.add("merdith-2021");else ids.add("natural-earth");
  const ul=document.createElement("ul");
  for(const id of ids){const source=DATA.sources[id];if(!source)continue;const li=document.createElement("li"),a=document.createElement("a"),rights=document.createElement("div");a.href=source.url;a.textContent=source.title;rights.className="note";rights.textContent=source.rights;li.append(a,rights);ul.append(li);}root.append(ul);
}
$("play").onclick=play;$("previous").onclick=()=>step(-1);$("next").onclick=()=>step(1);
$("next-chapter").onclick=()=>{pause();select(state.chapter===0?1:0,0);};
$("scrub").addEventListener("input",()=>{pause();state.progress=Number($("scrub").value)/1000;paint();});
$("sources").onclick=()=>{pause();fillEvidence();$("evidence").showModal();};
$("close-sources").onclick=()=>$("evidence").close();
document.addEventListener("visibilitychange",()=>{if(document.hidden)pause();});
document.addEventListener("keydown",e=>{
  if($("evidence").open||e.target.closest("button,a,input,summary"))return;
  if(e.code==="Space"){e.preventDefault();play();}else if(e.key==="ArrowRight")step(1);else if(e.key==="ArrowLeft")step(-1);else if(e.key==="Escape")pause();
});
motion.addEventListener("change",()=>{pause();paint();});
// Stable rendering interface for browser capture. Seeking always pauses playback.
window.TaswiraDirector={
  seek({chapter:c=0,scene:s=0,progress:p=0}={}){
    if(!Number.isInteger(c)||!Number.isInteger(s)||!DATA.chapters[c]?.scenes[s]||!Number.isFinite(p))throw new RangeError("Invalid scene or progress");
    pause();select(c,s,false);state.progress=clamp(p);paint();return {...state};
  },
  getState:()=>({...state}),
};
new ResizeObserver(resize).observe($("experience"));
select(0,0,false);resize();

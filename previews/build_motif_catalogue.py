"""Build a self-contained review catalogue from researched motif proposals; no museum art is copied."""
from pathlib import Path
import html
import json

root=Path(__file__).resolve().parent.parent
records=json.loads((root/'history/motifs.json').read_text(encoding='utf-8'))['records']
cards=[]
for i,r in enumerate(records,1):
    sources=' · '.join('<a href="'+html.escape(s['url'],quote=True)+'">'+html.escape(s['title'])+'</a>' for s in r['sources'])
    rows=''.join('<dt>'+html.escape(label)+'</dt><dd>'+html.escape(r[key])+'</dd>' for key,label in [('role','Role'),('evidence_date','Evidence date'),('application','Proposed use'),('limit','Boundary')])
    drawing=(root/'history/art/arewa-cultural-study.svg').read_text(encoding='utf-8') if r['id']=='hausa-interlace' else ''
    cards.append('<article><span class="n">'+str(i).zfill(2)+'</span><h2>'+html.escape(r['name'])+'</h2><p class="community">'+html.escape(r['community'])+'</p>'+('<div class="motif">'+drawing+'<small>Original cultural-frame study</small></div>' if drawing else '')+'<p>'+html.escape(r['meaning'])+'</p><dl>'+rows+'</dl><p class="sources">'+sources+'</p></article>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Taswira · Culture, memory, identity</title><style>
*{box-sizing:border-box}body{max-width:1200px;margin:0 auto;padding:50px 24px;background:#08120e;color:#f0eee2;font:16px/1.65 system-ui}header{margin-bottom:38px}h1{font:400 clamp(38px,6vw,72px)/1.05 Georgia,serif;margin:12px 0;color:#d4b57a}h2{font:400 29px/1.2 Georgia,serif;margin:8px 0}.kicker{letter-spacing:.2em;text-transform:uppercase;font-size:12px;color:#b5c4b8}.intro{max-width:800px;color:#b5c4b8}main{display:grid;grid-template-columns:1fr 1fr;gap:18px}article{padding:26px;border:1px solid #304b3d;background:linear-gradient(130deg,#142d21,#0b1b13);border-radius:12px}.n{font:22px Georgia;color:#d4b57a}.community{color:#95ab9c;font-size:13px}dl{font-size:14px}dt{color:#d4b57a;margin-top:15px}dd{margin:3px 0;color:#b5c4b8}a{color:#d4b57a}.sources{font-size:12px;border-top:1px solid #304b3d;padding-top:14px}.motif{float:right;width:150px;margin:0 0 14px 18px}.motif svg{display:block;width:140px;height:140px}.motif small{font-size:10px;color:#b5c4b8}footer{margin-top:35px;color:#95ab9c;font-size:13px}:focus-visible{outline:3px solid #d4b57a;outline-offset:3px}@media(max-width:760px){main{grid-template-columns:1fr}body{padding:28px 16px}article{padding:20px}.motif{width:120px}.motif svg{width:110px;height:110px}}
</style><header><p class="kicker">Taswira · research and creative direction</p><h1>Culture, memory, identity.</h1><p class="intro">Eight researched directions for a richer visual vocabulary. Cultural motifs, dated objects, political emblems and new editorial designs have distinct roles. This catalogue records proposals and limits; it does not automatically place an emblem on a historical timeline.</p></header><main>__CARDS__</main><footer>Checked 27 October 2026. Original artwork only. Source-specific dates, passages, rights and unresolved claims are recorded in history/research/creative. Restricted museum photographs are not reproduced. The permanent mascot direction selected by Saifu is the hare; Zomo is its working name.</footer></html>'''.replace('__CARDS__',''.join(cards))
(root/'previews/motif-catalogue.html').write_text(page,encoding='utf-8')
print('Wrote motif-catalogue.html')

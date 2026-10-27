"""Package the existing map snapshot and a built history page for design review.

Usage: python previews/build_site_theme.py <map snapshot> <built history> <local CDN assets>
Writes previews/site-theme.html, never docs/. Data and citations remain in the pages.
"""
import base64
import gzip
import json
from pathlib import Path
import re
import sys


def package(map_file, history_file, deps):
    root = Path(__file__).resolve().parent.parent
    pages = {"conflict": Path(map_file).read_text(encoding="utf-8"),
             "history": Path(history_file).read_text(encoding="utf-8")}
    template = (root / "map_template.html").read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", template, re.S).group(1)
    pages["conflict"] = re.sub(r"<style>.*?</style>", lambda _: "<style>" + css + "</style>",
                                pages["conflict"], count=1, flags=re.S)
    # Reset a link to the current document, also valid when previewed inside srcdoc.
    pages["conflict"] = pages["conflict"].replace("location.pathname + location.search", 'location.href.split("#")[0]')
    for name, page in pages.items():
        page = page.replace("<head>", '<head><base href="about:srcdoc">', 1)
        for url, asset in [
            ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", "leaflet.js"),
            ("https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js", "leaflet-heat.js"),
            ("https://unpkg.com/d3-array@3.2.4/dist/d3-array.min.js", "d3-array.js"),
            ("https://unpkg.com/d3-geo@3.1.1/dist/d3-geo.min.js", "d3-geo.js"),
        ]:
            page = page.replace('<script src="' + url + '"></script>',
                                "<script>" + (Path(deps) / asset).read_text(encoding="utf-8") + "</script>")
        page = page.replace('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">',
                            "<style>" + (Path(deps) / "leaflet.css").read_text(encoding="utf-8") + "</style>")
        pages[name] = base64.b64encode(gzip.compress(page.encode(), mtime=0)).decode()
    preview = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Taswira · Green atlas preview</title>
<style>
*{box-sizing:border-box}html,body{margin:0;height:100%;background:#08120e;color:#f0eee2;font:14px system-ui}
body{display:flex;flex-direction:column}header{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:10px 20px;border-bottom:1px solid #304b3d}
h1{font:400 26px Georgia,serif;margin:0;color:#d4b57a}nav{display:flex;gap:6px}button{font:inherit;min-height:38px;padding:6px 14px;border:1px solid #304b3d;background:#12271e;color:#f0eee2;border-radius:6px;cursor:pointer}
button[aria-pressed=true]{color:#d4b57a;border-color:#d4b57a}button:focus-visible{outline:3px solid #d4b57a;outline-offset:2px}
header p{margin:0 0 0 auto;font-size:12px;color:#b5c4b8}main{flex:1;min-height:0;position:relative}iframe{border:0;width:100%;height:100%;display:block}iframe[hidden]{display:none}#status{padding:20px;color:#b5c4b8}
@media(max-width:600px){header{gap:8px;padding:8px 12px}header p{width:100%;margin:0;font-size:11px}h1{font-size:23px}}
</style><header><h1>Taswira</h1><nav aria-label="Preview pages"><button data-page="history" aria-pressed="true">History</button><button data-page="conflict" aria-pressed="false">Conflict map</button></nav><p>Design preview · existing data and draft history · map tiles need internet</p></header>
<main><p id="status" role="status">Opening the atlas…</p><iframe id="history" title="Taswira history player" hidden></iframe><iframe id="conflict" title="Taswira conflict map" hidden></iframe></main>
<script>
const packed=__PAGES__,loaded=new Set();
async function show(name){document.querySelectorAll('[data-page]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.page===name));document.querySelectorAll('iframe').forEach(f=>f.hidden=f.id!==name);
if(loaded.has(name))return;try{const bytes=Uint8Array.from(atob(packed[name]),c=>c.charCodeAt(0));const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));const source=await new Response(stream).text();const frame=document.getElementById(name);frame.onload=()=>{frame.contentDocument.addEventListener('click',event=>{const link=event.target.closest?.('a');if(link&&['./','.','index.html'].includes(link.getAttribute('href'))){event.preventDefault();show('conflict');}});};frame.srcdoc=source;loaded.add(name);document.getElementById('status').hidden=true;}catch(error){document.getElementById('status').hidden=false;document.getElementById('status').textContent='This preview needs a current browser with gzip decompression: '+error.message;}}
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>show(b.dataset.page));show('history');
</script></html>'''.replace("__PAGES__", json.dumps(pages))
    output = root / "previews" / "site-theme.html"
    licences = (root / "previews" / "dependency-licenses.txt").read_text(encoding="utf-8")
    preview = preview.replace("</html>", "<!--\n" + licences + "\n--></html>")
    output.write_text(preview, encoding="utf-8")
    print(f"Wrote {output} ({len(preview):,} characters)")


if __name__ == "__main__":
    package(*sys.argv[1:])

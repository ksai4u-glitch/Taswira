"""Bundle the rendered MP4, captions and source manifest as an offline viewing copy."""
from pathlib import Path
import base64
import html
import json
import sys


def package(video, output_name="storycraft-video.html"):
    if Path(output_name).name != output_name or not output_name.endswith(".html"):
        raise ValueError("Use an HTML filename")
    video = Path(video)
    manifest = json.loads(video.with_suffix('.sources.json').read_text(encoding='utf-8'))
    captions = video.with_suffix('.vtt').read_text(encoding='utf-8')
    root = Path(__file__).resolve().parent
    title = html.escape(manifest.get('title', 'Taswira · Beyond the monuments'))
    encoded = base64.b64encode(video.read_bytes()).decode('ascii')
    vtt = base64.b64encode(captions.encode('utf-8')).decode('ascii')
    sources = ''.join('<li><a href="' + html.escape(s['url'], quote=True) + '">' +
                      html.escape(s['title']) + '</a></li>' for s in manifest['sources'].values())
    page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Taswira · Zomo and the cities that rise</title>
<style>*{box-sizing:border-box}body{margin:0;background:#08120e;color:#f0eee2;font:16px/1.65 system-ui}main{max-width:1280px;margin:auto;padding:32px 22px}h1{font:400 clamp(32px,5vw,56px)/1.1 Georgia,serif;color:#d4b57a;margin:10px 0 20px}.kicker{font-size:12px;text-transform:uppercase;letter-spacing:.2em;color:#b5c4b8}video{display:block;width:100%;background:#050d09;border:1px solid #304b3d;border-radius:8px}p,li{color:#b5c4b8}a,summary{color:#d4b57a}details{border-top:1px solid #304b3d;padding-top:18px;margin-top:25px}summary{cursor:pointer}pre{white-space:pre-wrap;font:14px/1.6 system-ui}a:focus-visible,summary:focus-visible{outline:3px solid #d4b57a;outline-offset:3px}</style>
<main><p class="kicker">Taswira · original guide and architectural studies</p><h1>Zomo and the cities that rise.</h1>
<video controls playsinline preload="metadata" aria-label="Silent animated architectural proof with burned-in narration captions"><source src="data:video/mp4;base64,__VIDEO__" type="video/mp4"><track label="English" kind="captions" srclang="en" src="data:text/vtt;base64,__VTT__"></video>
<p>__DURATION__ seconds · 1920×1080 · __FPS__ fps · silent prototype. Press Play, then use the player's full-screen button.</p>
<p>Meroe's royal cemetery, Aksum's stelae and tombs, and Great Zimbabwe assemble in layers. Original Zomo artwork accompanies the map. Architectural arrangements and counts are schematic; this is an unreviewed draft.</p>
<p><a id="download" download="taswira-storycraft.mp4">Download the MP4</a> · <a href="https://github.com/ksai4u-glitch/Taswira/blob/agent/history-africa-tour/history/research/creative/CLAUDE-HANDOFF-2026-10-27.md">Creative handoff and next scene</a></p>
<details><summary>Captions and transcript</summary><pre>__CAPTIONS__</pre></details>
<details><summary>Sources and reuse review</summary><p>Sources support the selected sites and historical narration. Source-specific rights and uncertainty remain in the companion JSON; no museum photographs are reproduced. Review is still required before a finished film is published.</p><ul>__SOURCES__</ul></details>
</main><script>document.getElementById('download').href=document.querySelector('video source').src;</script></html>'''
    if output_name != 'storycraft-video.html':
        page = page.replace('Zomo and the cities that rise.', title).replace('Taswira · Zomo and the cities that rise', title)
        page = page.replace("Meroe's royal cemetery, Aksum's stelae and tombs, and Great Zimbabwe assemble in layers.", 'A directed Great Zimbabwe sequence: hill, enclosures, passage, domestic spaces and a pullback.')
        page = page.replace('agent/history-africa-tour', 'agent/history-directed-story')
    page = page.replace('__DURATION__', str(manifest['duration'])).replace('__FPS__', str(manifest['fps']))
    page = page.replace('__VIDEO__', encoded).replace('__VTT__', vtt)
    page = page.replace('__CAPTIONS__', html.escape(captions)).replace('__SOURCES__', sources)
    (root / output_name).write_text(page, encoding='utf-8')
    (root / Path(output_name).with_suffix('.sources.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (root / Path(output_name).with_suffix('.vtt')).write_text(captions, encoding='utf-8')
    print(f'Wrote {output_name} with the rendered MP4, source manifest and captions.')


if __name__ == '__main__':
    package(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else "storycraft-video.html")

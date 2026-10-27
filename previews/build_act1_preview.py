"""Package a built history page as an offline Act 1 preview; never writes docs/."""
from pathlib import Path
import sys
import argparse
import json
import re


def package(built, deps, output_name="act1.html", initial_scene="origins", cinema=False, chapter="africa"):
    if Path(output_name).name != output_name or not output_name.endswith(".html") or not all(re.fullmatch(r"[a-z0-9-]+", x) for x in (initial_scene, chapter)):
        raise ValueError("Use an HTML filename and chapter and scene slugs")
    page = Path(built).read_text(encoding="utf-8")
    for url, asset in [
        ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", "leaflet.js"),
        ("https://unpkg.com/d3-array@3.2.4/dist/d3-array.min.js", "d3-array.js"),
        ("https://unpkg.com/d3-geo@3.1.1/dist/d3-geo.min.js", "d3-geo.js"),
    ]:
        page = page.replace('<script src="' + url + '"></script>', '<script>' +
                            (Path(deps) / asset).read_text(encoding="utf-8") + '</script>')
    page = page.replace('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">',
                        '<style>' + (Path(deps) / 'leaflet.css').read_text(encoding="utf-8") + '</style>')
    page = page.replace('href="./"', 'href="https://ksai4u-glitch.github.io/Taswira/"')
    # Preserve deep links someone has chosen; otherwise open the new chapter directly.
    startup = 'if (!location.hash) history.replaceState(null,"",'+json.dumps('#chapter='+chapter+'&scene='+initial_scene)+');\nreadLink();\n'
    if cinema:
        startup += 'document.body.classList.add("preview-boot");window.taswira.ready().then(()=>{setTheatre(true);if(!lessMotion.matches){state.drawn=null;goTo(state.c,state.s,{live:true,animate:false});setPlaying(true);}document.body.classList.remove("preview-boot");});\n'
        page = page.replace('</head>','<style>body.preview-boot #mapwrap{opacity:0}</style></head>')
    page = page.replace('readLink();\n</script>',startup+'</script>')
    root = Path(__file__).resolve().parent
    page = page.replace('</html>', '<!--\n' + (root / 'dependency-licenses.txt').read_text(encoding="utf-8") + '\n--></html>')
    output = root / output_name
    output.write_text(page, encoding="utf-8")
    print(f'Wrote {output} ({len(page):,} characters)')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('built');parser.add_argument('deps')
    parser.add_argument('--output',default='act1.html');parser.add_argument('--scene',default='origins');parser.add_argument('--cinema',action='store_true')
    parser.add_argument('--chapter',default='africa')
    args=parser.parse_args();package(args.built,args.deps,args.output,args.scene,args.cinema,args.chapter)

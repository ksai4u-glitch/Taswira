"""Package a built history page as an offline Act 1 preview; never writes docs/."""
from pathlib import Path
import sys


def package(built, deps):
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
    page = page.replace('readLink();\n</script>',
                        'if (!location.hash) history.replaceState(null,"","#chapter=africa&scene=origins");\nreadLink();\n</script>')
    root = Path(__file__).resolve().parent
    page = page.replace('</html>', '<!--\n' + (root / 'dependency-licenses.txt').read_text(encoding="utf-8") + '\n--></html>')
    output = root / 'act1.html'
    output.write_text(page, encoding="utf-8")
    print(f'Wrote {output} ({len(page):,} characters)')


if __name__ == '__main__':
    package(*sys.argv[1:])

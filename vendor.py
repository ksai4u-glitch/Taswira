"""
Put the map libraries inside each page instead of loading them from unpkg.com.

The templates still name the libraries with their usual unpkg.com tags (so a template opened
on its own, and the older preview scripts, keep working). When a page is built, each of those
tags is swapped for the same file from vendor/, written into the page. The live site then
needs no other website to draw its maps: if unpkg.com is slow or down, nothing breaks.

The files in vendor/ are the exact published versions (see vendor/README.md for their
checksums and licences). To upgrade one, replace the file and its tag in TAGS together.
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(HERE, "vendor")

# exact tag in a template -> (file in vendor/, "script" or "style")
TAGS = {
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">': ("leaflet.css", "style"),
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>': ("leaflet.js", "script"),
    '<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>': ("leaflet-heat.js", "script"),
    '<script src="https://unpkg.com/d3-array@3.2.4/dist/d3-array.min.js"></script>': ("d3-array.min.js", "script"),
    '<script src="https://unpkg.com/d3-geo@3.1.1/dist/d3-geo.min.js"></script>': ("d3-geo.min.js", "script"),
}


def inline_vendor(page):
    """Return the page with every known unpkg.com tag replaced by the file itself.
    Stops if a page still loads anything else from unpkg.com afterwards."""
    for tag, (name, kind) in TAGS.items():
        if tag not in page:
            continue
        with open(os.path.join(VENDOR_DIR, name), encoding="utf-8") as f:
            code = f.read()
        closing = "</" + kind
        if closing in code.lower():
            raise ValueError(f"vendor/{name} contains {closing!r} and would end its tag early")
        inline = (f"<style>/* vendor/{name} */\n{code}\n</style>" if kind == "style"
                  else f"<script>/* vendor/{name} */\n{code}\n</script>")
        page = page.replace(tag, inline)
    if "unpkg.com" in page:
        raise ValueError("the page still loads something from unpkg.com that vendor/ does not hold")
    return page

"""Build the Taswira front door: a dotted globe that zooms from space to Africa to Nigeria.

Usage:
    python build_home.py                      # writes previews/home.html (a local preview)
    python build_home.py --output docs/home.html --history-url history.html

It reads only files already in the repository, so it needs no token and makes no requests:
- the published conflict map docs/index.html, for the UCDP events (totals and lights),
- history/geo/natural-earth-background.json, for land, lakes and rivers (Natural Earth),
- history/geo/nga-states-2022.topojson, for Nigeria's outline (GRID3 / geoBoundaries).

Fills home_template.html. The default output is a preview: docs/ (the live site) is not touched.
"""
import argparse
import json
import math
import os
import re
import sys
from datetime import date

from build_map import fill, to_js
from settings import CANDIDATE_VERSIONS

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "home_template.html")
MAP_PAGE = os.path.join(HERE, "docs", "index.html")
LAND_PATH = os.path.join(HERE, "history", "geo", "natural-earth-background.json")
STATES_PATH = os.path.join(HERE, "history", "geo", "nga-states-2022.topojson")
OUTPUT_PATH = os.path.join(HERE, "previews", "home.html")
LIVE_MAP_URL = "https://ksai4u-glitch.github.io/Taswira/"

# Dot layers: (spacing in degrees of latitude, box (west, south, east, north) or None for the world).
# The page shows the coarse world layer from space and swaps in the finer ones as it zooms in.
WORLD_SPACING = 1.5
REGION_SPACING = 0.5
REGION_BOX = (-26.0, -40.0, 62.0, 40.0)        # Africa and its edges
NIGERIA_SPACING = 0.16
NIGERIA_BOX = (2.5, 4.0, 15.0, 14.0)
RIVER_BOX = (-12.5, 3.5, 16.5, 18.5)           # the Niger and the Benue
EVENT_CELL = 0.5                               # degrees; events are summed per cell


# --- Geography -------------------------------------------------------------------------------

def decode_ring(ring):
    """make_background.py rings: [lat, lon, dlat, dlon, ...] in thousandths of a degree."""
    lat, lon, points = ring[0], ring[1], []
    points.append((lon / 1000, lat / 1000))
    for i in range(2, len(ring), 2):
        lat += ring[i]
        lon += ring[i + 1]
        points.append((lon / 1000, lat / 1000))
    return points


def load_background():
    with open(LAND_PATH, encoding="utf-8") as f:
        data = json.load(f)
    land = [[decode_ring(r) for r in polygon] for polygon in data["land"]]
    lakes = [[decode_ring(r) for r in polygon] for polygon in data["lakes"]]
    rivers = [(rank, decode_ring(line)) for rank, *lines in data["rivers"] for line in lines]
    return land, lakes, rivers


def load_nigeria():
    """Nigeria's 37 state polygons (lon, lat) from the TopoJSON file."""
    with open(STATES_PATH, encoding="utf-8") as f:
        topo = json.load(f)
    (sx, sy), (tx, ty) = topo["transform"]["scale"], topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        points = []
        for dx, dy in arc:
            x += dx
            y += dy
            points.append((x * sx + tx, y * sy + ty))
        arcs.append(points)

    def ring(indices):
        points = []
        for i in indices:
            part = arcs[i] if i >= 0 else arcs[~i][::-1]
            points.extend(part if not points else part[1:])
        return points

    polygons = []
    for geometry in topo["objects"]["states"]["geometries"]:
        parts = [geometry["arcs"]] if geometry["type"] == "Polygon" else geometry["arcs"]
        polygons.extend([ring(r) for r in part] for part in parts)
    return polygons


def rows(spacing, box):
    west, south, east, north = box or (-180.0, -89.0, 180.0, 89.0)
    lat = math.ceil(south / spacing) * spacing
    while lat <= north:
        yield round(lat, 4)
        lat += spacing


def row_lons(lat, spacing, box):
    """Longitudes of the dots on one row, spaced so the dots stay evenly apart on the globe."""
    west, _, east, _ = box or (-180.0, 0, 180.0, 0)
    step = spacing / max(math.cos(math.radians(lat)), 0.08)
    # Offset alternate rows by half a step for a softer, less grid-like pattern.
    offset = (step / 2) if round(lat / spacing) % 2 else 0.0
    lon = math.ceil((west - offset) / step) * step + offset
    while lon <= east:
        yield round(lon, 4)
        lon += step


def spans(polygons, lat):
    """Longitude intervals inside any polygon on one latitude (even-odd rule within a polygon)."""
    out = []
    for polygon in polygons:
        xs = []
        for ring in polygon:
            for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
                if (y1 <= lat) != (y2 <= lat):
                    xs.append(x1 + (lat - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        out.extend(zip(xs[0::2], xs[1::2]))
    return out


def inside(lon, intervals):
    return any(a <= lon <= b for a, b in intervals)


def bbox_filter(polygons, box, pad=1.0):
    if box is None:
        return polygons
    west, south, east, north = box
    kept = []
    for polygon in polygons:
        xs = [x for x, _ in polygon[0]]
        ys = [y for _, y in polygon[0]]
        if max(xs) >= west - pad and min(xs) <= east + pad and max(ys) >= south - pad and min(ys) <= north + pad:
            kept.append(polygon)
    return kept


def dot_layer(spacing, box, land, holes, keep=lambda lon, lat: True):
    """Flat [lat*100, lon*100, ...] list of the dots that fall on land (and not in a lake)."""
    land, holes = bbox_filter(land, box), bbox_filter(holes, box)
    flat = []
    for lat in rows(spacing, box):
        land_spans, hole_spans = spans(land, lat), spans(holes, lat)
        if not land_spans:
            continue
        for lon in row_lons(lat, spacing, box):
            if inside(lon, land_spans) and not inside(lon, hole_spans) and keep(lon, lat):
                flat += [round(lat * 100), round(lon * 100)]
    return flat


def is_africa(lon, lat):
    """A rough test for the African mainland and Madagascar, used only to brighten dots."""
    if lat > 37.6 or lat < -35.5 or lon < -18.5 or lon > 51.5:
        return False
    if lon > 32.5 and lat > 29.5:                       # Sinai and the Levant
        return lon < 34.3 and lat < 31.4 and lat < 29.5 + (34.3 - lon)
    if lon > 42.6 and lat > 12.6:                       # Arabia
        return False
    if lon > 36.5 and lat > 16 and lon > 36.5 + (lat - 16) * 0.6:
        return False
    return True


def river_lines(rivers, box):
    """The bigger rivers in the box, as flat [lat*100, lon*100, ...] lines."""
    west, south, east, north = box
    lines = []
    for rank, points in rivers:
        if rank > 6:
            continue
        kept = [(x, y) for x, y in points if west <= x <= east and south <= y <= north]
        if len(kept) < 4:
            continue
        flat = []
        for x, y in kept[::2] + [kept[-1]]:
            flat += [round(y * 100), round(x * 100)]
        lines.append(flat)
    return lines


# --- UCDP events from the published conflict map --------------------------------------------

def read_events(path):
    """Unpack the events the conflict map page carries (see pack() in build_map.py)."""
    with open(path, encoding="utf-8") as f:
        page = f.read()

    def block(name):
        match = re.search(r'<script type="application/json" id="' + name + r'">(.*?)</script>', page, re.S)
        if not match:
            sys.exit(f"{path} has no {name} block. Run publish.py first.")
        return json.loads(match.group(1))

    def unpack(packed):
        count, columns = packed["count"], packed["columns"]
        events = [{} for _ in range(count)]
        for field, col in columns.items():
            for i, e in enumerate(events):
                e[field] = col[i] if isinstance(col, list) else col["values"][col["index"][i]]
        return events

    return unpack(block("events-data")), unpack(block("unmapped-data"))


def summarise(mapped, unmapped):
    everything = mapped + unmapped
    deaths = lambda events: sum(e["deaths_best"] or 0 for e in events)
    nigeria = [e for e in everything if e["country"] == "Nigeria"]
    prelim = [e for e in everything if e["preliminary"]]
    versions = sorted({e["dataset_version"] for e in everything})
    stable = sorted({e["dataset_version"] for e in everything if not e["preliminary"]})
    # In the order settings.py lists them (oldest first), then any the settings no longer list.
    listed = [v for v in CANDIDATE_VERSIONS if v in versions and v not in stable]
    candidates = listed + [v for v in versions if v not in stable and v not in listed]
    dates = sorted(e["date_start"] for e in everything)
    last_end = max(e["date_end"] for e in everything)
    return {
        "events": len(everything), "deaths": deaths(everything),
        "nigeriaEvents": len(nigeria), "nigeriaDeaths": deaths(nigeria),
        "prelimEvents": len(prelim), "firstYear": dates[0][:4], "lastDate": last_end,
        "stable": ", ".join(stable), "candidates": ", ".join(candidates),
        "countries": len({e["country"] for e in everything}),
    }


def lights(mapped):
    """Events summed per cell: [lat*100, lon*100, events, deaths, preliminary events]."""
    cells = {}
    for e in mapped:
        key = (math.floor(e["latitude"] / EVENT_CELL), math.floor(e["longitude"] / EVENT_CELL))
        cell = cells.setdefault(key, [0, 0, 0, 0.0, 0.0])
        cell[0] += 1
        cell[1] += e["deaths_best"] or 0
        cell[2] += 1 if e["preliminary"] else 0
        cell[3] += e["latitude"]
        cell[4] += e["longitude"]
    out = []
    for count, dead, prelim, lat, lon in sorted(cells.values(), key=lambda c: c[1]):
        out += [round(lat / count * 100), round(lon / count * 100), count, dead, prelim]
    return out


# --- Page ------------------------------------------------------------------------------------

def long_date(text):
    day = date.fromisoformat(text[:10])
    return f"{day.day} {day:%B %Y}"


def build(history_url, conflict_url):
    land, lakes, rivers = load_background()
    nigeria = load_nigeria()

    world = dot_layer(WORLD_SPACING, None, land, lakes)
    region = dot_layer(REGION_SPACING, REGION_BOX, land, lakes)
    nigeria_dots = dot_layer(NIGERIA_SPACING, NIGERIA_BOX, nigeria, lakes)
    africa_flags = [1 if is_africa(world[i + 1] / 100, world[i] / 100) else 0 for i in range(0, len(world), 2)]
    nigeria_land = bbox_filter(nigeria, NIGERIA_BOX)
    region_flags = []
    for i in range(0, len(region), 2):
        lat, lon = region[i] / 100, region[i + 1] / 100
        in_nigeria = inside(lon, spans(nigeria_land, lat)) if NIGERIA_BOX[1] <= lat <= NIGERIA_BOX[3] else False
        # bit 1: Africa; bit 2: Nigeria (the page hides these when it shows the finer Nigeria dots)
        region_flags.append((1 if is_africa(lon, lat) else 0) + (2 if in_nigeria else 0))

    mapped, unmapped = read_events(MAP_PAGE)
    stats = summarise(mapped, unmapped)
    geo = {
        "world": world, "worldAfrica": africa_flags,
        "region": region, "regionAfrica": region_flags, "regionBox": REGION_BOX,
        "nigeria": nigeria_dots, "rivers": river_lines(rivers, RIVER_BOX),
        "lights": lights(mapped),
    }

    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        page = f.read()
    number = lambda n: f"{n:,}"
    return fill(page, {
        "__GEO_JSON__": to_js(geo),
        "__EVENTS__": number(stats["events"]),
        "__DEATHS__": number(stats["deaths"]),
        "__NGA_EVENTS__": number(stats["nigeriaEvents"]),
        "__NGA_DEATHS__": number(stats["nigeriaDeaths"]),
        "__PRELIM__": number(stats["prelimEvents"]),
        "__FIRST_YEAR__": stats["firstYear"],
        "__LAST_DATE__": long_date(stats["lastDate"]),
        "__VERSION__": stats["stable"],
        "__CANDIDATES__": stats["candidates"] or "none",
        "__COUNTRIES__": str(stats["countries"]),
        "__HISTORY_URL__": history_url,
        "__HISTORY_STATE__": "ready" if history_url else "draft",
        "__CONFLICT_URL__": conflict_url,
        "__BUILT__": date.today().isoformat(),
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", default=OUTPUT_PATH, help="where to write the page (default: a preview)")
    parser.add_argument("--history-url", default="",
                        help="link for the history map; leave empty while it is an unpublished draft")
    parser.add_argument("--conflict-url", default=LIVE_MAP_URL, help="link for the conflict map")
    args = parser.parse_args()

    page = build(args.history_url, args.conflict_url)
    leftover = re.findall(r"__[A-Z_]+__", page)
    if leftover:
        sys.exit(f"Template placeholders left unfilled: {sorted(set(leftover))}")
    if "ucdp" not in page.lower() or "preliminary" not in page.lower():
        sys.exit("The page must credit UCDP and label preliminary data.")

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"Wrote {args.output} ({os.path.getsize(args.output) / 1000:.0f} KB).")
    if os.path.abspath(args.output) != os.path.abspath(os.path.join(HERE, "docs", "home.html")):
        print("Local preview only. The live site in docs/ was not changed.")


if __name__ == "__main__":
    main()

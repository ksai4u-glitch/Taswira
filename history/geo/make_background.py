"""
Make natural-earth-background.json, the map background for scenes before 1914.

Scenes set before 1914 must not sit on today's map (borders, roads, towns), so the
history page draws its own background from Natural Earth instead: land, lakes and
rivers, nothing else. Reservoirs are left out because they were made in the
20th century (Kainji 1968, Lake Volta 1965).

This script cuts the Natural Earth layers down to the area the page can show,
simplifies the lines and writes a compact file. Only needed when the background
changes; the result is committed. See history/geo/README.md for the exact files.

    python history/geo/make_background.py <folder with the Natural Earth .geojson files>

Uses only the Python standard library.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(HERE, "natural-earth-background.json")

# What the map can show at its widest zoom on a large screen, and the closer area
# where it zooms in. Boxes are (west, south, east, north) in degrees.
WIDE = (-40.0, -40.0, 65.0, 45.0)
NEAR = (-6.0, 0.0, 20.0, 18.0)
# Allowed error when simplifying, in degrees (0.01 is about 1 km)
TOLERANCE = {"land_wide": 0.03, "land_near": 0.004, "lakes": 0.004, "rivers_near": 0.004, "rivers_wide": 0.02}
# Outside the closer area only big rivers are kept (Natural Earth scalerank: 1 is the biggest)
WIDE_RIVER_RANK = 5
PRECISION = 1000          # coordinates are stored in thousandths of a degree (about 110 m)
PAD = 0.05                # the detailed and coarse land overlap by this much, so no seam shows


def around(wide, near, pad=PAD):
    """Four boxes that cover the wide box except the near one (overlapping it by pad)."""
    w, s, e, n = wide
    nw, ns, ne_, nn = near
    return [(w, s, nw + pad, n), (ne_ - pad, s, e, n),
            (nw, s, ne_, ns + pad), (nw, nn - pad, ne_, n)]


def read(folder, name):
    with open(os.path.join(folder, name + ".geojson"), encoding="utf-8") as f:
        return json.load(f)["features"]


def polygons(geom):
    """Each polygon as a list of rings; each ring a list of (lon, lat)."""
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def lines(geom):
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    if geom["type"] == "MultiLineString":
        return geom["coordinates"]
    return []


def overlaps(points, box):
    w, s, e, n = box
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs) <= e and max(xs) >= w and min(ys) <= n and max(ys) >= s


def clip_ring(ring, box):
    """Cut a ring to the box (Sutherland-Hodgman). Where a coast leaves the box and
    comes back, the result runs along the box edge; that edge is never stroked."""
    w, s, e, n = box
    edges = [(lambda p: p[0] >= w, lambda a, b: cross_x(a, b, w)),
             (lambda p: p[0] <= e, lambda a, b: cross_x(a, b, e)),
             (lambda p: p[1] >= s, lambda a, b: cross_y(a, b, s)),
             (lambda p: p[1] <= n, lambda a, b: cross_y(a, b, n))]
    out = ring[:-1] if ring[0] == ring[-1] else ring
    for inside, cross in edges:
        pts, out = out, []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
        if not out:
            return []
    return out + [out[0]]


def cross_x(a, b, x):
    t = (x - a[0]) / (b[0] - a[0])
    return (x, a[1] + t * (b[1] - a[1]))


def cross_y(a, b, y):
    t = (y - a[1]) / (b[1] - a[1])
    return (a[0] + t * (b[0] - a[0]), y)


def clip_line(line, box):
    """Split a line into the runs that are inside the box, keeping one point either
    side so the line reaches the edge."""
    w, s, e, n = box
    inside = [w <= x <= e and s <= y <= n for x, y in line]
    runs, run = [], []
    for i, pt in enumerate(line):
        near = inside[i] or (i > 0 and inside[i - 1]) or (i + 1 < len(line) and inside[i + 1])
        if near:
            run.append(pt)
        elif run:
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    return [r for r in runs if len(r) > 1]


def simplify(points, tol):
    """Douglas-Peucker: drop points that are closer than tol to the line between their neighbours."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = points[a], points[b]
        dx, dy = x2 - x1, y2 - y1
        length = (dx * dx + dy * dy) ** 0.5
        far, far_i = -1.0, None
        for i in range(a + 1, b):
            x, y = points[i]
            if length:
                d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / length
            else:
                d = ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
            if d > far:
                far, far_i = d, i
        if far_i is not None and far > tol:
            keep[far_i] = True
            stack += [(a, far_i), (far_i, b)]
    return [p for p, k in zip(points, keep) if k]


def area(ring):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:]))) / 2


def encode(points):
    """[lat, lon, dlat, dlon, ...] in thousandths of a degree: short numbers keep the file small."""
    out, last = [], (0, 0)
    for lon, lat in points:
        cur = (round(lat * PRECISION), round(lon * PRECISION))
        if out and cur == last:
            continue
        out += [cur[0] - last[0], cur[1] - last[1]]
        last = cur
    return out


def cut_polygons(features, box, tol, min_area):
    out = []
    for f in features:
        for poly in polygons(f["geometry"]):
            if not overlaps(poly[0], box):
                continue
            rings = []
            for ring in poly:
                ring = simplify(clip_ring(ring, box), tol)
                if len(ring) >= 4 and area(ring) >= min_area:
                    rings.append(encode(ring))
                elif not rings:
                    break            # the outer ring vanished, so drop its holes too
            if rings:
                out.append(rings)
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = sys.argv[1]
    # Coarse land around the closer area, detailed land inside it
    coarse = read(folder, "ne_50m_land")
    land = [p for box in around(WIDE, NEAR) for p in cut_polygons(coarse, box, TOLERANCE["land_wide"], 0.01)]
    land += cut_polygons(read(folder, "ne_10m_land"), NEAR, TOLERANCE["land_near"], 0.0004)
    lakes = cut_polygons([f for f in read(folder, "ne_10m_lakes")
                          if f["properties"].get("featurecla") != "Reservoir"],
                         WIDE, TOLERANCE["lakes"], 0.002)
    rivers = []
    for f in read(folder, "ne_10m_rivers_lake_centerlines"):
        p = f["properties"]
        if p.get("featurecla") not in ("River", "Lake Centerline"):
            continue
        rank = int(p.get("scalerank") or 10)
        for line in lines(f["geometry"]):
            for run in clip_line(line, NEAR):
                rivers.append([rank, encode(simplify(run, TOLERANCE["rivers_near"]))])
            if rank <= WIDE_RIVER_RANK:
                # Outside the closer area: the same river, coarser. Inside it, the line above is used.
                for run in clip_line(line, WIDE):
                    for part in split_outside(run, NEAR):
                        rivers.append([rank, encode(simplify(part, TOLERANCE["rivers_wide"]))])
    rivers = [r for r in rivers if len(r[1]) >= 4]
    rivers.sort(key=lambda r: -r[0])     # small rivers first, so big ones are drawn on top

    out = {"note": "Natural Earth (public domain), cut and simplified by make_background.py. "
                   "Rings and lines are [lat, lon, dlat, dlon, ...] in thousandths of a degree.",
           "land": land, "lakes": lakes, "rivers": rivers}
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"Wrote {OUTPUT_PATH}: {len(land)} land polygons, {len(lakes)} lakes, {len(rivers)} river lines, "
          f"{os.path.getsize(OUTPUT_PATH) / 1000:.0f} KB.")


def split_outside(line, box):
    """The parts of a line that are outside the box (with one point inside, so they join up)."""
    w, s, e, n = box
    inside = [w < x < e and s < y < n for x, y in line]
    runs, run = [], []
    for i, pt in enumerate(line):
        near = (not inside[i]) or (i > 0 and not inside[i - 1]) or (i + 1 < len(line) and not inside[i + 1])
        if near:
            run.append(pt)
        elif run:
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    return [r for r in runs if len(r) > 1]


if __name__ == "__main__":
    main()

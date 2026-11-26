"""
Cut Africa out of CShapes 2.0 for the borders map: every country and colony that touched Africa
between two dates, with its borders simplified, as a small topology (shared borders stay shared).

    python borders/geo/make_scramble.py path/to/cshapes_2_gw.topojson.xz

Standard library only. See borders/geo/README.md for where the file comes from and its checksum.
"""

import argparse
import hashlib
import json
import lzma
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "scramble.json")
EXPECTED_SHA256 = "196c6d9d881cf944e176e4ce5bfc61074d21792de7152cb0a9e035e56b0297c8"
FIRST, LAST = "1886-01-01", "1960-10-01"
TOLERANCE = 0.04   # degrees (about 4 km): smallest wiggle kept on a border
SCALE = 100        # coordinates kept to a hundredth of a degree (about 1 km)


def in_africa(lon, lat):
    """True when a polygon's middle lies in Africa or its islands (not Europe, not Arabia)."""
    if not (-24 < lon < 60 and -40 < lat < 37.6):
        return False
    if lat > 34.5 and lon > 11:                      # Malta, Crete, Cyprus
        return False
    # East of the Red Sea (a line from Suez to Bab-el-Mandeb) and the Gulf of Aden is Arabia.
    if lat > 11.9 and lon > 32.5 + (30 - lat) * (10.8 / 17.4):
        return False
    return True


def simplify(points, tolerance):
    """Douglas-Peucker on one arc. Both ends stay, so neighbours still meet."""
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
        best, index = 0.0, None
        for i in range(a + 1, b):
            x, y = points[i]
            if length == 0:
                d = ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
            else:
                d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / length
            if d > best:
                best, index = d, i
        if index is not None and best > tolerance:
            keep[index] = True
            stack += [(a, index), (index, b)]
    return [p for p, k in zip(points, keep) if k]


def encode(points):
    """[[lon, lat], ...] -> flat ints, first point whole, the rest as steps."""
    out, last = [], (0, 0)
    for lon, lat in points:
        q = (round(lon * SCALE), round(lat * SCALE))
        if out and q == last:
            continue
        out += [q[0] - last[0], q[1] - last[1]]
        last = q
    return out


def build(source, first=FIRST, last=LAST):
    with open(source, "rb") as f:
        raw = f.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"{source}: SHA-256 {digest} is not the CShapes 2.0 file this script expects")
    topo = json.loads(lzma.decompress(raw) if source.endswith(".xz") else raw)
    arcs = topo["arcs"]
    used, units = {}, []

    def points(i):
        return arcs[i] if i >= 0 else arcs[~i][::-1]

    for geometry in topo["objects"]["cshapes_2_gw"]["geometries"]:
        p = geometry["properties"]
        if p["end"] < first or p["start"] > last:
            continue
        # A European country's own islands (Canaries, Madeira) are not colonies: leave them out.
        if 200 <= p["gwcode"] < 400 and p["status"] == "independent":
            continue
        polygons = geometry["arcs"] if geometry["type"] == "MultiPolygon" else [geometry["arcs"]]
        kept = []
        for polygon in polygons:
            ring = [q for a in polygon[0] for q in points(a)]
            lons, lats = [q[0] for q in ring], [q[1] for q in ring]
            if in_africa((min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2):
                kept.append([[used.setdefault(a, len(used)) if a >= 0
                              else ~used.setdefault(~a, len(used)) for a in r] for r in polygon])
        if kept:
            units.append({
                "gw": p["gwcode"], "name": p["country_name"], "start": p["start"], "end": p["end"],
                "status": p["status"], "owner": int(p["owner"]), "capital": p["capname"],
                "polygons": kept,
            })
    order = sorted(used, key=used.get)
    out_arcs = []
    for i in order:
        pts = simplify(arcs[i], TOLERANCE)
        if len(pts) < 2:
            pts = [arcs[i][0], arcs[i][-1]]
        out_arcs.append(encode(pts))
    units.sort(key=lambda u: (u["start"], u["gw"]))
    return {
        "note": ("CShapes 2.0 (Schvitz et al. 2022), Gleditsch-Ward version, cut to Africa between "
                 f"{first} and {last} and simplified by make_scramble.py. Arcs are "
                 "[lon, lat, dlon, dlat, ...] in hundredths of a degree; polygons are rings of arc "
                 "numbers as in TopoJSON (~i means arc i reversed)."),
        "source_sha256": digest,
        "first": first, "last": last,
        "arcs": out_arcs,
        "units": units,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("source", help="cshapes_2_gw.topojson.xz from the CShapes 2.0 R package")
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()
    data = build(args.source)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"Wrote {args.output}: {len(data['units'])} units, {len(data['arcs'])} arcs, "
          f"{os.path.getsize(args.output):,} bytes")

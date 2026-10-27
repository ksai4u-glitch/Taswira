"""
Make plates.json, the moving continents for the deep-time chapter.

The deep-time scenes show the continents where a published plate model puts them,
from 600 million years ago to today. The model is Merdith et al. (2021), which
covers the last 1,000 million years: present-day continent outlines, each on a
plate, and a rotation file saying how every plate moved. This script works out each
plate's position every few million years, so the page only has to turn the outlines
and never needs the whole model. Only needed when the model or the times change; the
result is committed. See history/geo/README.md for the exact file.

    python history/geo/make_plates.py <Merdith_etal_2021_ESR_v1.2.4.zip, or the folder it unzips to>

Uses only the Python standard library.
"""

import gzip
import hashlib
import json
import math
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(HERE, "plates.json")

# The two files used from the model, found by name wherever they are in the zip or folder.
# The zip has Continents/shapes_continents.gpml; the model's description calls it continents_Merdith_etal.gpml.
ROTATIONS = ("1000_0_rotfile_Merdith_etal.rot",)
CONTINENTS = ("shapes_continents.gpml", "continents_Merdith_etal.gpml")
ZIP_MD5 = "181ab32d1d235a923ee343568731e64a"     # Merdith_etal_2021_ESR_v1.2.4.zip, as listed on Zenodo
# The model shows the Benue Trough's two outlines only today, which would leave a hole in Africa in
# every past scene. Their rock was there before the rift, only narrower, so they are drawn throughout.
ALWAYS = {"Benue Trough (NW Africa Plate)", "Benue Trough (Central Africa Plate)"}

OLDEST = 600              # million years ago, the first deep-time scene
STEP = 10                 # a position every 10 million years, as often as the model gives Africa's; the page blends between them
TOLERANCE = 0.25          # allowed error when simplifying outlines, in degrees (about 28 km)
MIN_AREA = 15000          # km²: smaller pieces (islands, slivers) are left out
QUAT_SCALE = 10000        # rotations are stored as whole numbers, times 10,000 (an error of under 1 km)
PRECISION = 100           # coordinates are stored in hundredths of a degree
EARTH_RADIUS = 6371.0     # km

NS = {"gml": "http://www.opengis.net/gml", "gpml": "http://www.gplates.org/gplates"}


# --- Rotations ---------------------------------------------------------------------
# A rotation is a unit quaternion (w, x, y, z). The model gives each plate's rotation
# relative to another plate at a list of times; a plate's position at any time is
# found by blending the two nearest entries and adding up the chain to plate 0.

def quat_from_pole(lat, lon, angle):
    """The rotation of angle degrees about the pole at (lat, lon)."""
    la, lo, half = math.radians(lat), math.radians(lon), math.radians(angle) / 2
    s = math.sin(half)
    return (math.cos(half), s * math.cos(la) * math.cos(lo), s * math.cos(la) * math.sin(lo), s * math.sin(la))


def quat_mul(a, b):
    """a after b."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def slerp(a, b, u):
    """Blend two rotations, u from 0 (a) to 1 (b), the short way round."""
    dot = sum(p * q for p, q in zip(a, b))
    if dot < 0:
        b, dot = tuple(-q for q in b), -dot
    if dot > 0.9995:
        out = tuple(p + (q - p) * u for p, q in zip(a, b))
    else:
        theta = math.acos(dot)
        sa, sb = math.sin((1 - u) * theta), math.sin(u * theta)
        out = tuple((p * sa + q * sb) / math.sin(theta) for p, q in zip(a, b))
    n = math.sqrt(sum(c * c for c in out))
    return tuple(c / n for c in out)


def rotate(q, v):
    """Turn the 3D vector v by the rotation q."""
    w, x, y, z = q
    vx, vy, vz = v
    # v + 2w (q × v) + 2 q × (q × v), with q the vector part
    cx, cy, cz = y * vz - z * vy, z * vx - x * vz, x * vy - y * vx
    ex, ey, ez = y * cz - z * cy, z * cx - x * cz, x * cy - y * cx
    return (vx + 2 * (w * cx + ex), vy + 2 * (w * cy + ey), vz + 2 * (w * cz + ez))


def read_rotations(text):
    """
    Each plate's rotation sequences, in file order: {moving: [(fixed, [(time, quat), ...]), ...]}.
    A line is "moving time lat lon angle fixed !comment". Plate 999 lines are comments.
    A new sequence starts whenever the moving or fixed plate changes.
    """
    plates, last = {}, None
    for line in text.splitlines():
        parts = line.split("!")[0].split()
        if len(parts) < 6:
            continue
        try:
            moving, fixed = int(parts[0]), int(parts[5])
            time, lat, lon, angle = (float(p) for p in parts[1:5])
        except ValueError:
            continue
        if moving == 999:
            continue
        if last != (moving, fixed):
            plates.setdefault(moving, []).append((fixed, []))
            last = (moving, fixed)
        plates[moving][-1][1].append((time, quat_from_pole(lat, lon, angle)))
    return plates


def relative(sequences, time):
    """(fixed plate, rotation) at a time from the first sequence that covers it, or None."""
    for fixed, entries in sequences:
        for (t0, q0), (t1, q1) in zip(entries, entries[1:]):
            lo, hi = min(t0, t1), max(t0, t1)
            if lo <= time <= hi:
                u = 0.0 if t1 == t0 else (time - t0) / (t1 - t0)
                return fixed, slerp(q0, q1, u)
        if len(entries) == 1 and entries[0][0] == time:
            return fixed, entries[0][1]
    return None


def total(plates, plate, time, memo=None, depth=0):
    """A plate's rotation from its present position to where it was at a time, or None if unknown."""
    if plate == 0:
        return (1.0, 0.0, 0.0, 0.0)
    memo = {} if memo is None else memo
    if (plate, time) in memo:
        return memo[(plate, time)]
    found = relative(plates.get(plate, []), time) if depth < 50 else None
    result = None
    if found:
        fixed, rel = found
        base = total(plates, fixed, time, memo, depth + 1)
        if base is not None:
            result = quat_mul(base, rel)
    memo[(plate, time)] = result
    return result


# --- Outlines ----------------------------------------------------------------------

def to_xyz(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))


def to_latlon(v):
    x, y, z = v
    return math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))


def time_value(text):
    """A GPML time position in million years ago: distant past is infinity, distant future is 0."""
    text = (text or "").strip()
    if "distantPast" in text:
        return math.inf
    if "distantFuture" in text:
        return 0.0
    return float(text)


def read_shapes(xml_bytes):
    """Continent outlines: [{"plate", "name", "from", "to", "rings": [[(lat, lon), ...], ...]}]."""
    root = ET.fromstring(xml_bytes)
    shapes = []
    for member in root.iter(f"{{{NS['gml']}}}featureMember"):
        for feature in member:
            plate = feature.find(".//gpml:reconstructionPlateId//gpml:value", NS)
            if plate is None:
                continue
            begin = feature.find(".//gml:validTime//gml:begin//gml:timePosition", NS)
            end = feature.find(".//gml:validTime//gml:end//gml:timePosition", NS)
            name = feature.find("gml:name", NS)
            rings = []
            for poly in feature.iter(f"{{{NS['gml']}}}Polygon"):
                pos = poly.find("gml:exterior//gml:posList", NS)
                if pos is None or not pos.text:
                    continue
                nums = [float(n) for n in pos.text.split()]
                ring = list(zip(nums[0::2], nums[1::2]))        # GPML lists latitude, then longitude
                if len(ring) >= 4:
                    rings.append(ring)
            if rings:
                shapes.append({"plate": int(float(plate.text)), "name": (name.text or "").strip() if name is not None else "",
                               "from": time_value(begin.text if begin is not None else "distantPast"),
                               "to": time_value(end.text if end is not None else "distantFuture"),
                               "rings": rings})
    return shapes


def ring_area(ring):
    """Area of a ring on the sphere in km², whichever way round it runs."""
    pts = [to_xyz(*p) for p in ring]
    total_angle = 0.0
    # The sum of the signed triangles from the first point (spherical excess, Van Oosterom and Strackee)
    a = pts[0]
    for b, c in zip(pts[1:], pts[2:]):
        num = (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
               + a[2] * (b[0] * c[1] - b[1] * c[0]))
        den = 1 + sum(p * q for p, q in zip(a, b)) + sum(p * q for p, q in zip(b, c)) + sum(p * q for p, q in zip(c, a))
        total_angle += 2 * math.atan2(num, den)
    return abs(total_angle) * EARTH_RADIUS ** 2


def simplify(ring, tolerance):
    """Douglas-Peucker on the sphere: drop points closer than tolerance (degrees) to the great circle between kept ones."""
    pts = [to_xyz(*p) for p in ring]
    limit = math.sin(math.radians(tolerance))
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        a, b = pts[i], pts[j]
        n = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
        size = math.sqrt(sum(c * c for c in n))
        far, at = 0.0, None
        for k in range(i + 1, j):
            p = pts[k]
            d = (abs(sum(c * q for c, q in zip(n, p))) / size if size > 1e-12
                 else math.sqrt(sum((c - q) ** 2 for c, q in zip(p, a))))
            if d > far:
                far, at = d, k
        if at is not None and far > limit:
            keep[at] = True
            stack += [(i, at), (at, j)]
    return [p for p, k in zip(ring, keep) if k]


def sample_times(oldest=OLDEST, step=STEP):
    return list(range(0, oldest + 1, step))


def make(rot_text, continents_xml, oldest=OLDEST, step=STEP, tolerance=TOLERANCE, min_area=MIN_AREA):
    plates = read_rotations(rot_text)
    times = sample_times(oldest, step)
    shapes, used = [], set()
    for s in read_shapes(continents_xml):
        if s["to"] > oldest:                     # gone before the oldest scene
            continue
        for ring in s["rings"]:
            if ring_area(ring) < min_area:
                continue
            small = simplify(ring, tolerance)
            if small[0] == small[-1]:
                small = small[:-1]
            if len(small) < 3:
                continue
            begin = 10 ** 4 if s["name"] in ALWAYS else min(s["from"], 10 ** 4)
            shapes.append({"plate": s["plate"], "from": begin, "to": s["to"],
                           "ring": [[round(lat * PRECISION), round(lon * PRECISION)] for lat, lon in small]})
            used.add(s["plate"])
    memo = {}
    rotations, same = {}, {}
    for plate in sorted(used):
        row = []
        for t in times:
            q = total(plates, plate, float(t), memo)
            row.append(None if q is None else [round(c * QUAT_SCALE) for c in (q if q[0] >= 0 else [-c for c in q])])
        # Many small blocks move exactly with a bigger one; they name it instead of repeating its rotations
        key = json.dumps(row)
        if key in same:
            rotations[str(plate)] = same[key]
        else:
            same[key] = str(plate)
            rotations[str(plate)] = row
    return {"times": times, "precision": PRECISION, "scale": QUAT_SCALE, "tolerance": tolerance,
            "rotations": rotations, "shapes": shapes}


def read_model(path):
    """The rotation text and the continents' GPML from the model's zip or folder."""
    def find(names, wanted):
        ok = {w.lower() for w in wanted} | {w.lower() + "z" for w in wanted}     # .gpmlz is the zipped form
        hits = [n for n in names if os.path.basename(n.replace("\\", "/")).lower() in ok]
        if not hits:
            sys.exit(f"Could not find {' or '.join(wanted)} in {path}")
        return hits[0]

    if zipfile.is_zipfile(path):
        with open(path, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        if md5 != ZIP_MD5:
            print(f"Note: this zip's md5 is {md5}, not the {ZIP_MD5} of version 1.2.4 on Zenodo")
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            rot = z.read(find(names, ROTATIONS)).decode("utf-8", errors="replace")
            cont = z.read(find(names, CONTINENTS))
    else:
        names = [os.path.join(d, f) for d, _, fs in os.walk(path) for f in fs]
        with open(find(names, ROTATIONS), encoding="utf-8", errors="replace") as f:
            rot = f.read()
        with open(find(names, CONTINENTS), "rb") as f:
            cont = f.read()
    if cont[:2] == b"\x1f\x8b":
        cont = gzip.decompress(cont)
    return rot, cont


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    rot, cont = read_model(sys.argv[1])
    data = make(rot, cont)
    data["source"] = ("Merdith et al. (2021), Extending full-plate tectonic models into deep time, Earth-Science "
                      "Reviews 214. Model v1.2.4, CC BY 4.0, doi:10.5281/zenodo.13635864")
    text = json.dumps(data, separators=(",", ":"))
    text = re.sub(r"(?<=[\[,])-?0\.0+(?=[,\]])", "0", text)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    vertices = sum(len(s["ring"]) for s in data["shapes"])
    print(f"Wrote {OUTPUT_PATH}: {len(data['shapes'])} outlines, {vertices} points, "
          f"{len(data['rotations'])} plates, {len(data['times'])} times, {len(text) // 1024} KB")


if __name__ == "__main__":
    main()

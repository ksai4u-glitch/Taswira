"""
Build the Nigeria history page as docs/history.html.

The page plays short chapters of Nigeria's history on a map, scene by scene.
Everything it shows comes from three kinds of files in history/:

  history/chapters/<id>.json   the scenes, what is on the map in each, and the text
  history/sources.json         every source a scene or map feature cites
  history/emblems.json         flags and symbols, and which are documented
  history/drawings/*.svg       the emblems that are drawn, redrawn from written descriptions
  history/geo/*.topojson       today's state borders (simplified, see history/geo/README.md)
  history/geo/natural-earth-background.json
                               neutral land, lakes and rivers for historical scenes
  history/geo/plates.json      the continents of a plate model, for scenes in deep time

This script checks those files (dates, places, sources, how sure each thing is,
which state belonged to which at each date), fills in history/template.html and
writes docs/history.html.
It makes no API requests and is separate from publish.py, so the history page
does not change when the UCDP data does.

    python build_history.py           check, then write docs/history.html
    python build_history.py --check   only check, write nothing

Uses only the Python standard library.
"""

import base64
import copy
from pathlib import Path
import struct
import colorsys
import html
import argparse
import json
import math
import os
import re
import sys
from datetime import date
from calendar import isleap

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(HERE, "history")
TEMPLATE_PATH = os.path.join(HISTORY_DIR, "template.html")
SOURCES_PATH = os.path.join(HISTORY_DIR, "sources.json")
EMBLEMS_PATH = os.path.join(HISTORY_DIR, "emblems.json")
DRAWINGS_DIR = os.path.join(HISTORY_DIR, "drawings")
STATES_PATH = os.path.join(HISTORY_DIR, "geo", "nga-states-2022.topojson")
BACKGROUND_PATH = os.path.join(HISTORY_DIR, "geo", "natural-earth-background.json")
PLATES_PATH = os.path.join(HISTORY_DIR, "geo", "plates.json")
OUTPUT_PATH = os.path.join(HERE, "docs", "history.html")

# Chapters in the order the page plays them
CHAPTERS = ["deep", "africa", "nok", "hausa", "sokoto", "states", "key"]

# Modern reference maps are never allowed before this year. Later historical scenes also
# use the neutral background unless a modern locator is explicitly requested and explained.
PERIOD_BEFORE = 1914
# Map data credited on the map itself rather than by a scene
MAP_SOURCES = {"grid3-states", "esri-tiles", "natural-earth", "merdith-2021"}

# Rough box around the lower Niger and Lake Chad basin, out to Bilma on the Sahara salt road,
# to catch swapped or mistyped coordinates
LAT_RANGE = (2.0, 20.0)
LON_RANGE = (0.0, 18.0)
# A chapter with "area": "world" may place things anywhere (the deep-time globe)
AREAS = ("world", "africa")
AFRICA_LAT = (-40.0, 40.0)
AFRICA_LON = (-25.0, 55.0)
# A chapter with "clock": "ago" counts in years ago (million years ago, then years ago)
CLOCKS = ("ago", "label")
SLUG = re.compile(r"^[a-z0-9-]+$")
UNSAFE_SVG = re.compile(r"<script|<foreignObject|\son\w+\s*=|href", re.I)

# Moods set the decoration while a scene with places plays (see history/README.md)
MOODS = ("survey", "farming", "sculpture", "iron", "decline", "excavation", "calm", "delta", "greening")
EFFECTS = ("arc", "pulse", "shatter")
# Architectural stage sets drawn on the map, and the small glyph each becomes when far out
SETTINGS = ("royal-cemetery", "stelae-field", "stone-enclosure", "walled-city")
MONUMENT_TYPES = ("pyramid", "stele", "tower", "walled-city")
# What a dated beat's date rests on. A Chronicle date says so on screen; oral tradition has no date;
# an account is a dated written description by a named writer.
BEAT_BASES = ("archaeology", "chronicle", "differ", "oral", "account", "record")

# The map vocabulary (see history/README.md). How sure each thing on the map is:
STATUSES = ("firm", "approx", "disputed", "to-check")
# How a place's political order is drawn. No form: a plain dot, as for archaeological sites.
FORMS = ("kingdom", "city-state", "network", "caliphate", "emirate", "communities")
# Ties between two places, and movements along a path of places
LINKS = ("allegiance", "tribute", "alliance", "trade", "ritual")
MOVES = ("migration", "campaign", "trade")
# A city-state may be drawn as a small walled town (the same symbol for every town, not a plan)
ICONS = {"walled-town": "city-state"}
# Drawings a scene's note may carry
NOTE_ART = ("well",)
UNCERTAIN = ("start", "end", "whole")
# A colonial claim on a place: on paper only, occupied, or taken during the scene by a campaign it shows
CONTROL = ("claimed", "held", "taken")
# What is documented about an actor's emblem: a flag, a symbol that is not a flag, or nothing
TIERS = ("flag", "symbol", "none")
# Forms for the land rather than its rulers: a name written across a continent (on the globe),
# and a lake drawn as a soft disc of its area (its shoreline is not drawn)
NATURE = ("landmass", "lake")
# Lines drawn on the globe, with the years (million years ago) they were active
LINE_TYPES = ("rift", "river")

# Deep time: scenes with "view": "globe" show the whole Earth, with the continents where the
# plate model puts them. The plate file covers the last 600 million years.
VIEWS = ("globe",)
OLDEST_YEAR = -600_000_000
AGO_YEAR = 2000             # "years ago" count back from 2000, as on the page
GLOBE_ZOOM = (1, 6)

# Hues for the 12 states of 1967, picked so neighbours look different.
# Later states keep the hue of the state they came from.
HUES_1967 = {
    "North-Western": 8, "North-Central": 38, "Kano": 270, "North-Eastern": 84,
    "Benue-Plateau": 150, "Kwara": 190, "Lagos": 315, "Western": 230,
    "Mid-Western": 55, "East-Central": 290, "South-Eastern": 205, "Rivers": 350,
}
REGION_COLOURS = {
    "Northern Region": "#c9a35b", "Western Region": "#5fa8a0",
    "Mid-Western Region": "#b07acb", "Eastern Region": "#d07a62",
}
FCT_COLOUR = "#d9dde3"
OTHER_COLOUR = "#7d8590"     # a parent that is not on the map as a state (old Lagos territory)
# How much lighter or darker each new state is than the one it came from
CHILD_SHIFTS = [0, 0.12, -0.10, 0.20, -0.17, 0.27]


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --- Period background ------------------------------------------------------------

def load_background(path=BACKGROUND_PATH):
    """Read the period background made by history/geo/make_background.py and check its shape:
    every ring or line is a list of [lat, lon, dlat, dlon, ...] in thousandths of a degree."""
    bg = read_json(path)
    problems = []
    for key in ("land", "lakes", "rivers"):
        if not bg.get(key):
            problems.append(f"background: {key} is missing or empty")
    flats = ([ring for poly in bg.get("land", []) + bg.get("lakes", []) for ring in poly]
             + [line for _, line in bg.get("rivers", [])])
    for flat in flats:
        if len(flat) < 4 or len(flat) % 2 or not all(isinstance(v, int) for v in flat):
            problems.append("background: a ring or line is not a list of whole-number pairs")
            break
        lat, lon = flat[0] / 1000, flat[1] / 1000
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            problems.append(f"background: a line starts at an impossible place ({lat}, {lon})")
            break
    if problems:
        sys.exit("Not building the history page:\n  - " + "\n  - ".join(problems))
    return {key: bg[key] for key in ("land", "lakes", "rivers")}


def base_for(scene):
    """Historical scenes default to neutral geography; modern maps are explicit locators."""
    if scene.get("view") == "globe":
        return "deep"
    if scene.get("background") == "modern-reference" and scene["when"]["from"] >= PERIOD_BEFORE:
        return "modern"
    return "period"


# --- Plates ------------------------------------------------------------------------

def load_plates(path=PLATES_PATH):
    """The plate file made by history/geo/make_plates.py, or None if it has not been made."""
    return read_json(path) if os.path.exists(path) else None


def unit(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))


def plate_of(lat, lon, plates):
    """The plate whose present-day outline holds a point, or None. Where outlines overlap, the one
    that goes furthest back wins (some, like the Benue Trough's, exist only today).
    Each outline is drawn flat around the point (a stereographic projection from the far side
    of the Earth), where an ordinary inside-or-outside test works for outlines of any size."""
    p = unit(lat, lon)
    # Two directions at right angles to p, along the ground
    e1 = (-math.sin(math.radians(lon)), math.cos(math.radians(lon)), 0.0)
    e2 = (p[1] * e1[2] - p[2] * e1[1], p[2] * e1[0] - p[0] * e1[2], p[0] * e1[1] - p[1] * e1[0])
    dot = lambda a, b: a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
    k = plates["precision"]
    best = None
    for shape in plates["shapes"]:
        flat = []
        for la, lo in shape["ring"]:
            v = unit(la / k, lo / k)
            d = 1 + dot(v, p)
            if d > 1e-9:
                flat.append((dot(v, e1) / d, dot(v, e2) / d))
        inside = False
        for (x1, y1), (x2, y2) in zip(flat, flat[1:] + flat[:1]):
            if (y1 > 0) != (y2 > 0) and 0 < x1 + (0 - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        if inside and (best is None or shape["from"] > best["from"]):
            best = shape
    return best and best["plate"]


def turn_known(plate, ma, plates):
    """Whether the plate file says where a plate was at a time (million years ago)."""
    rows = plates["rotations"].get(str(plate))
    if isinstance(rows, str):                     # moves with another plate
        rows = plates["rotations"][rows]
    times = plates["times"]
    i = min(range(len(times)), key=lambda n: abs(times[n] - ma))
    return rows is not None and rows[i] is not None


# --- Emblems ------------------------------------------------------------------------

def load_emblems(path=EMBLEMS_PATH, drawings_dir=DRAWINGS_DIR):
    """Read the emblem list and add each drawing's SVG text (None for emblems that are not drawn)."""
    emblems = read_json(path)
    for e in emblems.values():
        drawing = os.path.join(drawings_dir, f"{e['drawing']}.svg") if e.get("drawing") else None
        if drawing and os.path.exists(drawing):
            with open(drawing, encoding="utf-8") as f:
                e["svg"] = f.read().strip()
        else:
            e["svg"] = None
    return emblems


def check_emblems(emblems, sources, cited):
    """An emblem is drawn only from a cited description. "none" says that nothing is documented."""
    problems = []

    def need(cond, msg):
        if not cond:
            problems.append(msg)

    for eid, e in emblems.items():
        where = f"emblem {eid}"
        need(SLUG.match(eid), f"{where}: id must be a-z 0-9 -")
        for field in ("actor", "description"):
            need(e.get(field), f"{where}: missing {field}")
        need(e.get("tier") in TIERS, f"{where}: tier must be one of {', '.join(TIERS)}")
        need(e.get("status") in STATUSES, f"{where}: status must be one of {', '.join(STATUSES)}")
        need((e.get("status") == "disputed") == bool(e.get("disputed")),
             f"{where}: status must be 'disputed' exactly when disputed explains the disagreement")
        if e.get("tier") in ("flag", "symbol"):
            need(e.get("sources"), f"{where}: a {e['tier']} needs a source, or it is not shown")
        else:
            need(e.get("note"), f"{where}: say what was looked for in note")
            need(not e.get("drawing"), f"{where}: nothing is documented, so nothing may be drawn")
        for sid in e.get("sources", []):
            need(sid in sources, f"{where}: unknown source {sid!r}")
            cited.add(sid)
        if e.get("drawing"):
            svg = e.get("svg") or ""
            need(svg.startswith("<svg"), f"{where}: no drawing history/drawings/{e['drawing']}.svg")
            # The drawing goes into the public page as it is, so it may hold shapes only
            need(not UNSAFE_SVG.search(svg), f"{where}: a drawing must be plain shapes, with no scripts or links")
        years = [e[k] for k in ("from", "to") if k in e]
        need(all(isinstance(y, int) for y in years) and years == sorted(years),
             f"{where}: from and to must be whole years, from <= to")
    return problems


def emblem_fits(e, when):
    """An emblem is visible throughout a scene, so its dates must cover that scene."""
    return (("from" not in e or e["from"] <= when["from"])
            and ("to" not in e or e["to"] >= when["to"]))


# --- Today's state borders -------------------------------------------------------

def load_states(path=STATES_PATH):
    """Read the TopoJSON file of today's states.

    TopoJSON stores each border line ("arc") once, shared by the two states on
    either side, so we can tell which lines separate which states. Returns
    {code: {"name", "rings"}}, the arcs as [lat, lon] lists, and for each arc
    the states that use it."""
    topo = read_json(path)
    (sx, sy), (tx, ty) = topo["transform"]["scale"], topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        points = []
        for dx, dy in arc:          # positions are stored as steps from the previous point
            x, y = x + dx, y + dy
            points.append([round(y * sy + ty, 3), round(x * sx + tx, 3)])
        arcs.append(points)

    states, users = {}, [[] for _ in arcs]
    for geom in topo["objects"]["states"]["geometries"]:
        code = geom["properties"]["shapeISO"]
        polygons = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
        rings, refs = [], []
        for polygon in polygons:
            for ring_arcs in polygon:
                refs.append(ring_arcs)
                ring = []
                for i in ring_arcs:
                    points = arcs[i] if i >= 0 else arcs[~i][::-1]   # ~i: the arc walked backwards
                    ring.extend(points if not ring else points[1:])
                    users[i if i >= 0 else ~i].append(code)
                rings.append(ring)
        name = geom["properties"]["shapeName"].replace("Abuja Federal Capital Territory", "FCT (Abuja)")
        states[code] = {"name": name, "rings": rings, "arc_refs": refs}
    return states, arcs, users


def ring_area_centroid(ring):
    """Area and centre of one ring, treating degrees as flat (fine at this scale)."""
    a = cx = cy = 0.0
    for (y1, x1), (y2, x2) in zip(ring, ring[1:] + ring[:1]):
        cross = x1 * y2 - x2 * y1
        a += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if a == 0:
        return 0.0, ring[0]
    return abs(a / 2), [cy / (3 * a), cx / (3 * a)]


def label_point(codes, states):
    """Where to write a group's name: the area-weighted centre of its states."""
    total = lat = lon = 0.0
    for code in codes:
        for ring in states[code]["rings"][:1]:
            area, (y, x) = ring_area_centroid(ring)
            total += area
            lat += y * area
            lon += x * area
    return [round(lat / total, 3), round(lon / total, 3)]


# --- Colours ---------------------------------------------------------------------

def hsl(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, max(0, min(1, l)), s)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def snapshot_colours(snapshots):
    """Give every group in every snapshot a colour.

    The 12 states of 1967 get 12 different hues. A state created later keeps
    the hue of the state it came from, a little lighter or darker, so you can
    see a state splitting into its children."""
    colours, previous = {}, None
    for key in sorted(snapshots):
        snap, these = snapshots[key], {}
        children = {}
        for g in snap["groups"]:
            children.setdefault(g.get("from"), []).append(g)
        for i, g in enumerate(snap["groups"]):
            name = g["name"]
            if g.get("not_a_state"):
                these[name] = FCT_COLOUR
            elif name in REGION_COLOURS:
                these[name] = REGION_COLOURS[name]
            elif not g.get("from") or previous is None:
                these[name] = hsl(HUES_1967.get(name, i * 47 % 360), 0.55, 0.52)
            else:
                parent = previous[g["from"]]
                siblings = sorted(children[g["from"]], key=lambda c: c["name"] != g["from"])
                shift = CHILD_SHIFTS[siblings.index(g) % len(CHILD_SHIFTS)]
                h, l, s = colorsys.rgb_to_hls(*(int(parent[j:j + 2], 16) / 255 for j in (1, 3, 5)))
                these[name] = hsl(h * 360, s, l + shift)
        colours[key] = these
        previous = these
    return colours


# --- Checks ------------------------------------------------------------------------

def check_parts(where, m, need, cite):
    """A setting built from dated parts: each part is natural ground, oral tradition (shown for a
    while and never dated), or dated by its earliest documented year, with sources."""
    parts = m.get("parts")
    need(isinstance(parts, list) and parts, f"{where}: monument parts must be a non-empty list")
    seen = set()
    for part in parts if isinstance(parts, list) else []:
        pid = part.get("id", "?") if isinstance(part, dict) else "?"
        here = f"{where} part {pid}"
        need(isinstance(part, dict) and SLUG.match(pid) and pid not in seen, f"{here}: id must be unique, a-z 0-9 -")
        seen.add(pid)
        if not isinstance(part, dict):
            continue
        at, until = part.get("at"), part.get("until")
        need(isinstance(at, (int, float)) and at >= 0, f"{here}: at must be seconds into the scene")
        need(until is None or (isinstance(until, (int, float)) and isinstance(at, (int, float)) and until > at),
             f"{here}: until must come after at")
        kinds = [k for k in ("natural", "oral") if part.get(k)] + (["year"] if "year" in part else [])
        need(len(kinds) == 1, f"{here}: a part is natural, oral, or has a year (exactly one)")
        if part.get("natural"):
            continue
        need(isinstance(part.get("label"), str) and part["label"].strip(), f"{here}: say what the part shows and what its date rests on")
        cite(here, part.get("sources"))
        if part.get("oral"):
            need(until is not None, f"{here}: oral tradition is shown for a while and then leaves (until)")
        elif "year" in part:
            need(type(part["year"]) is int and m.get("from", part["year"]) <= part["year"] <= m.get("to", part["year"]),
                 f"{here}: year must be a whole year inside the monument's from/to")


def check_notes(where, sc, features, need):
    """A scene's notes and fades. A note is a few words at a shown place for part of the scene. A note
    from oral tradition (`oral: true`) appears only during an oral-tradition beat and leaves before the
    next dated one; any other note appears only under a dated beat. A fade dims a place from a moment on."""
    end = sc.get("duration", reading_seconds(sc.get("text", "")))
    shown = [fid for fid in sc.get("show", []) if features.get(fid, {}).get("kind") == "point"]
    beats = [b for b in sc.get("beats", []) if isinstance(b, dict) and isinstance(b.get("at"), (int, float))]
    oral_at = lambda t: next((b.get("when", {}).get("basis") == "oral" for b in reversed(beats) if b["at"] <= t), None)
    notes = sc.get("notes", [])
    need(isinstance(notes, list), f"{where}: notes must be a list")
    for n in notes if isinstance(notes, list) else []:
        here = f"{where} note {n.get('text') if isinstance(n, dict) else n!r}"
        if not isinstance(n, dict):
            need(False, f"{here}: a note is an object")
            continue
        at, until, text = n.get("at"), n.get("until"), n.get("text")
        need(n.get("place") in shown, f"{here}: a note needs a place the scene shows")
        need(isinstance(text, str) and 0 < len(text.strip()) <= 40, f"{here}: a note is 1 to 40 characters")
        need(isinstance(at, (int, float)) and isinstance(until, (int, float)) and 0 <= at < until <= end,
             f"{here}: a note needs at < until, inside the scene")
        need(n.get("art") in (None,) + NOTE_ART, f"{here}: art must be one of {', '.join(NOTE_ART)}")
        need(isinstance(n.get("oral", False), bool), f"{here}: oral must be true or false")
        need(n.get("side") in (None, "above"), f"{here}: side is \"above\", or left out for below")
        if not beats or not isinstance(at, (int, float)) or not isinstance(until, (int, float)):
            continue
        if n.get("oral"):
            need(oral_at(at) is True, f"{here} is oral tradition but appears during a dated beat")
            later = [b["at"] for b in beats if b["at"] > at and b.get("when", {}).get("basis") != "oral"]
            need(not later or until <= later[0], f"{here} is oral tradition and must leave before the next dated beat")
        else:
            need(oral_at(at) is False, f"{here} appears during an oral-tradition beat but is not marked oral")
    fade = sc.get("fade", {})
    need(isinstance(fade, dict), f"{where}: fade must map places to seconds")
    for fid, at in (fade if isinstance(fade, dict) else {}).items():
        need(fid in shown and fid not in sc.get("dim", []) and isinstance(at, (int, float)) and 0 <= at < end,
             f"{where}: fade needs places the scene shows (not already dim) and times inside the scene")


def expand_bases(chapters):
    """A city can carry on from another setting in the same chapter (monument "base"). It starts
    from the base city as it stands, without the base's passing parts (oral tradition, a disputed
    line). Base parts named again in its own "parts" take their new time there; the others stand
    from the start ("standing"). Parts new to this city follow. Returns copies; the files are unchanged,
    and expanding chapters that are already expanded changes nothing."""
    out = copy.deepcopy(chapters)
    for ch in out:
        feats = [f for f in ch.get("features", []) if isinstance(f, dict)]
        by_id = {f.get("id"): f for f in feats}
        for f in feats:
            m = f.get("monument")
            if not isinstance(m, dict) or "base" not in m or not isinstance(m.get("parts"), list):
                continue
            base = by_id.get(m["base"], {}).get("monument")
            if not isinstance(base, dict) or "base" in base or not isinstance(base.get("parts"), list):
                continue  # reported by check()
            own = {p.get("id"): p for p in m["parts"] if isinstance(p, dict)}
            known = {p.get("id") for p in base["parts"] if isinstance(p, dict)}
            parts = []
            for p in base["parts"]:
                if not isinstance(p, dict) or p.get("oral") or "until" in p:
                    continue
                parts.append({**p, **own[p["id"]]} if p.get("id") in own else {**p, "at": 0, "standing": True})
            m["parts"] = parts + [p for p in m["parts"] if not (isinstance(p, dict) and p.get("id") in known)]
    return out


def check_bases(chapters, need):
    """What expand_bases needs: a base that is another dated city of the same chapter, in the same
    setting, and no return of a part that passed in the base city."""
    for ch in chapters:
        feats = {f.get("id"): f for f in ch.get("features", []) if isinstance(f, dict)}
        for fid, f in feats.items():
            m = f.get("monument")
            if not isinstance(m, dict) or "base" not in m:
                continue
            where = f"{ch.get('id', '?')}/{fid}"
            base = feats.get(m["base"], {}).get("monument") if m["base"] != fid else None
            ok = isinstance(base, dict) and "base" not in base and isinstance(base.get("parts"), list)
            need(ok and isinstance(m.get("parts"), list),
                 f"{where}: base must name another city with dated parts in this chapter, and parts must be a list")
            if not ok:
                continue
            need(m.get("setting") == base.get("setting"), f"{where}: a city carries on in its base's setting")
            passing = {p.get("id") for p in base["parts"] if isinstance(p, dict) and (p.get("oral") or "until" in p)}
            again = sorted(p.get("id") for p in m.get("parts", []) if isinstance(p, dict) and p.get("id") in passing)
            need(not again, f"{where}: {', '.join(again)} passed in the base city and cannot return")


def beat_in_force(beats, at):
    """The beat on screen at a time in the scene (beats start at zero and are in order)."""
    current = beats[0]
    for beat in beats:
        if beat["at"] <= at:
            current = beat
    return current


def check_part_times(where, fid, parts, sc, need):
    """No part of a dated setting may appear before its date: the beat on screen when it appears
    must be dated no earlier than the part. Oral tradition appears only while an oral-tradition
    beat is on screen, and has left before the next dated beat."""
    beats = sc.get("beats", [])
    duration = sc.get("duration", reading_seconds(sc.get("text", "")))
    good = (isinstance(beats, list) and beats and all(isinstance(b, dict) and isinstance(b.get("at"), (int, float))
                                                       and isinstance(b.get("when"), dict) for b in beats))
    need(good, f"{where}: {fid} has dated parts, so every beat needs a when")
    if not good:
        return
    for part in parts:
        if not isinstance(part, dict) or not isinstance(part.get("at"), (int, float)):
            continue
        here = f"{where}: {fid} part {part.get('id')}"
        need(part["at"] < duration and (part.get("until") is None or part["until"] <= duration),
             f"{here} is timed past the end of the scene")
        shown = beat_in_force(beats, part["at"])["when"]
        if part.get("natural"):
            continue
        if part.get("oral"):
            need(shown.get("basis") == "oral", f"{here} is oral tradition but appears during a dated beat")
            later = [b["at"] for b in beats if b["at"] > part["at"] and b["when"].get("basis") != "oral"]
            need(not later or (isinstance(part.get("until"), (int, float)) and part["until"] <= later[0]),
                 f"{here} is oral tradition and must leave before the next dated beat")
        elif type(part.get("year")) is int:
            need(shown.get("basis") != "oral" and isinstance(shown.get("from"), int) and shown["from"] >= part["year"],
                 f"{here} appears at {part['at']} s under \"{shown.get('label')}\", before its date ({part['year']})")


def check(chapters, sources, states, cited=None, emblems=None, plates=None):
    """Return a list of problems. An empty list means the page can be built.
    Pass a set as cited to collect the ids of the sources that are used."""
    problems = []
    cited = set() if cited is None else cited
    emblems = {} if emblems is None else emblems

    def need(cond, msg):
        if not cond:
            problems.append(msg)

    for sid, s in sources.items():
        for field in ("title", "url", "rights", "checked"):
            need(s.get(field), f"source {sid}: missing {field}")
        need(str(s.get("url", "")).startswith("https://"), f"source {sid}: url must start with https://")

    def cite(where, ids):
        need(ids, f"{where}: no sources")
        for sid in ids or []:
            need(sid in sources, f"{where}: unknown source {sid!r}")
            cited.add(sid)

    check_bases(chapters, need)
    chapters = expand_bases(chapters)
    seen_chapters = set()
    for ch in chapters:
        cid = ch.get("id", "?")
        need(SLUG.match(cid) and cid not in seen_chapters, f"chapter {cid}: id must be unique, a-z 0-9 -")
        seen_chapters.add(cid)
        for field in ("title", "period", "intro", "scenes"):
            need(ch.get(field), f"chapter {cid}: missing {field}")
        need(ch.get("area") in AREAS + (None,), f"chapter {cid}: area must be one of {', '.join(AREAS)}, or left out")
        need(ch.get("clock") in CLOCKS + (None,), f"chapter {cid}: clock must be one of {', '.join(CLOCKS)}, or left out")
        need(isinstance(ch.get("reference", False), bool), f"chapter {cid}: reference must be true or false")
        world = ch.get("area") == "world"
        lat_range, lon_range = ((-90.0, 90.0), (-180.0, 180.0)) if world else (AFRICA_LAT, AFRICA_LON) if ch.get("area") == "africa" else (LAT_RANGE, LON_RANGE)

        def placed(ll):
            return (isinstance(ll, (list, tuple)) and len(ll) == 2 and all(isinstance(v, (int, float)) for v in ll)
                    and lat_range[0] <= ll[0] <= lat_range[1] and lon_range[0] <= ll[1] <= lon_range[1])

        features = {}
        for f in ch.get("features", []):
            fid = f.get("id", "?")
            where = f"{cid}/{fid}"
            need(SLUG.match(fid) and fid not in features, f"{where}: feature id must be unique, a-z 0-9 -")
            features[fid] = f
            for field in ("name", "what", "evidence"):
                need(f.get(field), f"{where}: missing {field}")
            need("disputed" in f, f"{where}: say disputed: null or explain the disagreement")
            need(f.get("status") in STATUSES, f"{where}: status must be one of {', '.join(STATUSES)}")
            need((f.get("status") == "disputed") == bool(f.get("disputed")),
                 f"{where}: status must be 'disputed' exactly when disputed explains the disagreement")
            cite(where, f.get("sources"))
            kind = f.get("kind")
            if kind in ("point", "move", "line"):
                need(f.get("location"), f"{where}: missing location (how precise the place or route is)")
            if kind == "point":
                need(placed(f.get("coordinates")), f"{where}: coordinates [lat, lon] are outside the map area")
                if "form" in f:
                    need(f["form"] in FORMS + NATURE, f"{where}: form must be one of {', '.join(FORMS + NATURE)}")
                if "reach_km" in f or f.get("form") == "communities":
                    need(isinstance(f.get("reach_km"), (int, float)) and 5 <= f["reach_km"] <= 600
                         and f.get("reach_note"), f"{where}: a halo or field needs reach_km (5 to 600) and a "
                                                  f"reach_note saying what its size rests on")
                if f.get("form") == "landmass":
                    # A continent lights the model's plates whose numbers start with these digits
                    # (the model numbers plates by region: 7 Africa, 2 South America and so on)
                    blocks = f.get("blocks")
                    need(isinstance(blocks, list) and blocks and all(isinstance(b, str) and b.isdigit() for b in blocks),
                         f"{where}: a landmass needs blocks, the starts of its plate numbers, like [\"7\"]")
                    if plates and isinstance(blocks, list):
                        known = {str(sh["plate"]) for sh in plates["shapes"]}
                        for b in blocks:
                            need(any(k.startswith(str(b)) for k in known),
                                 f"{where}: no plate in the plate model starts with {b}")
                if "monument" in f:
                    m = f["monument"]
                    need(isinstance(m, dict), f"{where}: monument must be an object")
                    if isinstance(m, dict):
                        need(m.get("setting") in (None,) + SETTINGS, f"{where}: unsupported architectural setting")
                        need(m.get("type") in MONUMENT_TYPES and m.get("note"),
                             f"{where}: monument needs a known schematic type and note")
                        if "parts" in m:
                            check_parts(where, m, need, cite)
                        need(all(type(m.get(k)) is int for k in ("from", "to")) and m.get("from", 1) <= m.get("to", 0),
                             f"{where}: monument needs documented from/to years")
                        cite(where + " monument", m.get("sources"))
                if "icon" in f:
                    need(ICONS.get(f["icon"]) == f.get("form"),
                         f"{where}: icon must be one of {', '.join(ICONS)}, for a place of that form")
                if "emblem" in f:
                    need(f["emblem"] in emblems, f"{where}: unknown emblem {f['emblem']!r}")
                if "short" in f:
                    need(isinstance(f["short"], str) and 0 < len(f["short"]) < len(f.get("name", "")),
                         f"{where}: short must be a shorter name for the map on a phone")
            elif kind == "line":
                need(f.get("type") in LINE_TYPES, f"{where}: type must be one of {', '.join(LINE_TYPES)}")
                path = f.get("path", [])
                need(len(path) >= 2 and all(placed(ll) for ll in path),
                     f"{where}: a line needs a path of two or more [lat, lon] inside the map area")
                active = f.get("active")
                need(f.get("type") == "river" or (isinstance(active, list) and len(active) == 2 and all(isinstance(v, (int, float)) for v in active)
                     and active[0] >= active[1] >= 0),
                     f"{where}: active must be [from, to] in million years ago, older first")
            elif kind == "link":
                need(f.get("type") in LINKS, f"{where}: type must be one of {', '.join(LINKS)}")
            elif kind == "move":
                need(f.get("type") in MOVES, f"{where}: type must be one of {', '.join(MOVES)}")
                need(len(f.get("path", [])) >= 2, f"{where}: a path needs two or more places")
                need(f.get("uncertain") in UNCERTAIN + (None,),
                     f"{where}: uncertain must be null or one of {', '.join(UNCERTAIN)}")
                need(f.get("type") != "migration" or f.get("period"),
                     f"{where}: a migration needs a period, such as \"by the 15th century\"")
                need(f.get("type") != "trade" or f.get("goods"), f"{where}: trade needs goods")
                for k in f.get("dates", {}):
                    need(k in f.get("path", []), f"{where}: a date for {k!r}, which is not on the path")
                if f.get("type") == "campaign":
                    stops = f.get("stops")
                    need(isinstance(stops, dict) and set(stops) == set(f.get("path", [])),
                         f"{where}: campaign stops must date every path place, with no extra stops")
                    need("dates" not in f, f"{where}: use structured campaign stops, not free-text dates")
                    stops = stops if isinstance(stops, dict) else {}
                    parsed = []
                    for pid, stop in (stops or {}).items():
                        try:
                            parse_campaign_stop(stop)
                        except ValueError as error:
                            need(False, f"{where}: stop {pid}: {error}")
                    for pid in f.get("path", []):
                        try:
                            parsed.append(parse_campaign_stop((stops or {}).get(pid))["year"])
                        except ValueError:
                            pass
                    need(parsed == sorted(parsed), f"{where}: campaign stops must be in chronological order")
            else:
                need(False, f"{where}: unknown kind {kind!r}")
        # Links and paths join places of the same chapter
        is_point = lambda x: features.get(x, {}).get("kind") == "point"
        for fid, f in features.items():
            if f.get("kind") == "line":
                continue                  # a line's path is coordinates, not places
            ends = [f.get("from"), f.get("to")] if f.get("kind") == "link" else f.get("path", [])
            for end in ends:
                need(is_point(end), f"{cid}/{fid}: {end!r} is not a place in this chapter")
            if f.get("kind") == "link":
                need(f.get("from") != f.get("to"), f"{cid}/{fid}: a link needs two different places")
                need("bend" not in f or isinstance(f["bend"], (int, float)) and 0 < abs(f["bend"]) <= .4,
                     f"{cid}/{fid}: bend curves a tie, from -0.4 to 0.4 (sign picks the side)")

        snapshots = ch.get("snapshots", {})
        previous = None
        for key in sorted(snapshots):
            snap = snapshots[key]
            where = f"{cid}/snapshot {key}"
            names = [g["name"] for g in snap["groups"]]
            need(len(names) == len(set(names)), f"{where}: a group name is used twice")
            states_here = [g for g in snap["groups"] if not g.get("not_a_state")]
            need(len(states_here) == snap.get("count"),
                 f"{where}: {len(states_here)} states listed but count says {snap.get('count')}")
            placed = [c for g in snap["groups"] for c in g["members"]] + list(snap.get("split", {}))
            for code in states:
                n = placed.count(code)
                need(n == 1, f"{where}: {code} ({states[code]['name']}) is placed {n} times, should be once")
            for code in placed:
                need(code in states, f"{where}: unknown state code {code}")
            for g in snap["groups"]:
                if previous is not None and g.get("from"):
                    need(g["from"] in previous, f"{where}: {g['name']} comes from {g['from']!r}, "
                                                f"which is not in the previous snapshot")
            for code, sp in snap.get("split", {}).items():
                need(len(sp.get("parents", [])) >= 2, f"{where}/{code}: a split needs two or more parents")
                need(any(p in names for p in sp.get("parents", [])),
                     f"{where}/{code}: none of its parents is a group in this snapshot")
                for field in ("note", "evidence"):
                    need(sp.get(field), f"{where}/{code}: missing {field}")
                need("disputed" in sp, f"{where}/{code}: say disputed: null or explain")
            previous = set(names)

        scene_ids = set()
        for sc in ch.get("scenes", []):
            sid = sc.get("id", "?")
            where = f"{cid}/scene {sid}"
            need(SLUG.match(sid) and sid not in scene_ids, f"{where}: id must be unique, a-z 0-9 -")
            scene_ids.add(sid)
            for field in ("title", "text", "when", "camera"):
                need(sc.get(field), f"{where}: missing {field}")
            when = sc.get("when", {})
            need(isinstance(when.get("from"), int) and isinstance(when.get("to"), int)
                 and when["from"] <= when["to"] <= date.today().year,
                 f"{where}: when.from and when.to must be whole years (BCE negative), from <= to")
            need(when.get("label"), f"{where}: when.label missing")
            need(isinstance(sc.get("monuments", True), bool), f"{where}: monuments must be true or false")
            need(isinstance(sc.get("sensitive", False), bool), f"{where}: sensitive must be true or false")
            need(sc.get("background") in (None, "period", "modern-reference"),
                 f"{where}: background must be period or modern-reference, or left out")
            if sc.get("background") == "modern-reference":
                note = sc.get("background_note")
                need(isinstance(note, str) and bool(note.strip()),
                     f"{where}: modern-reference needs a background_note explaining that this is today's map")
                need(sc.get("view") != "globe" and isinstance(when.get("from"), int)
                     and when["from"] >= PERIOD_BEFORE,
                     f"{where}: modern-reference is only for map scenes from 1914 onward")
            need(sc.get("clock") in CLOCKS + (None,), f"{where}: unknown scene clock")
            need(sc.get("camera_frame") in (None, "video"),
                 f"{where}: camera_frame is \"video\" (zooms composed for the 1920x1080 frame), or left out")
            cam = sc.get("camera", {})
            shown = sc.get("show", [])
            for fid in shown + sc.get("dim", []):
                need(fid in features, f"{where}: shows unknown feature {fid!r}")
            need(sc.get("view") in VIEWS + (None,), f"{where}: view must be one of {', '.join(VIEWS)}, or left out")
            if sc.get("view") == "globe":
                # The camera follows a place on the globe, and everything shown moves with a plate
                need(placed(cam.get("center")) and GLOBE_ZOOM[0] <= cam.get("zoom", 0) <= GLOBE_ZOOM[1],
                     f"{where}: a globe camera needs a center on the map and a zoom from "
                     f"{GLOBE_ZOOM[0]} to {GLOBE_ZOOM[1]}")
                need(isinstance(when.get("from"), int) and when["from"] >= OLDEST_YEAR,
                     f"{where}: the plate file starts {-OLDEST_YEAR // 10 ** 6} million years ago")
                if plates is None:
                    need(False, f"{where}: a globe scene needs history/geo/plates.json (see history/geo/README.md)")
                else:
                    spots = [("the camera centre", cam.get("center"))]
                    for fid in shown:
                        f = features.get(fid, {})
                        need(f.get("kind") == "point" or (f.get("kind") == "line" and f.get("type") == "rift"), f"{where}: a globe shows places and rifts only")
                        lls = [f.get("coordinates")] if f.get("kind") == "point" else f.get("path", [])
                        spots += [(f"{fid} at {ll}", ll) for ll in lls]
                    ends = [(AGO_YEAR - when[k]) / 10 ** 6 for k in ("from", "to") if isinstance(when.get(k), int)]
                    for name, ll in spots:
                        if not placed(ll):
                            continue
                        plate = plate_of(*ll, plates)
                        need(plate is not None, f"{where}: {name} is not on any continent of the plate model")
                        for ma in ends if plate is not None else []:
                            need(turn_known(plate, ma, plates), f"{where}: {name} is on plate {plate}, "
                                 f"which the plate model does not place {ma:g} million years ago")
            else:
                lat, lon = cam.get("center", [0, 0])
                need(lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]
                     and (2 <= cam.get("zoom", 0) <= 11 if ch.get("area") == "africa" else 4 <= cam.get("zoom", 0) <= 11), f"{where}: camera centre or zoom out of range")
                for fid in shown:
                    f = features.get(fid, {})
                    need((f.get("kind") != "line" or f.get("type") == "river") and f.get("form") != "landmass",
                         f"{where}: {fid} can only be shown on the globe")
            previous_beat = -1
            beats = sc.get("beats", [])
            need(isinstance(beats, list), f"{where}: beats must be a list")
            for beat in beats if isinstance(beats, list) else []:
                at = beat.get("at") if isinstance(beat, dict) else None
                focus = beat.get("focus") if isinstance(beat, dict) else None
                valid = (isinstance(at, (int, float)) and previous_beat < at
                         < sc.get("duration", reading_seconds(sc.get("text", "")))
                         and isinstance(beat.get("text"), str) and bool(beat["text"].strip())
                         and beat.get("pose") in (0, 1, 3, 5, 6, 7)
                         and isinstance(focus, list) and len(focus) == 3
                         and all(isinstance(v, (int, float)) for v in focus)
                         and 0 <= focus[0] <= 440 and 0 <= focus[1] <= 300 and .6 <= focus[2] <= 2)
                need(valid, f"{where}: beats need ordered finite times, text, supported guide poses and bounded architectural focus")
                if valid:
                    previous_beat = at
            if isinstance(beats, list) and beats:
                need(isinstance(beats[0], dict) and beats[0].get("at") == 0,
                     f"{where}: beats must begin at zero")
            dated = isinstance(beats, list) and any(isinstance(b, dict) and "when" in b for b in beats)
            last_year = None
            for beat in beats if dated else []:
                bw = beat.get("when") if isinstance(beat, dict) else None
                here = f"{where} beat at {beat.get('at') if isinstance(beat, dict) else '?'}"
                if not isinstance(bw, dict):
                    need(False, f"{here}: when one beat is dated, every beat needs a when")
                    continue
                basis, label = bw.get("basis"), bw.get("label")
                need(basis in BEAT_BASES, f"{here}: when.basis must be one of {', '.join(BEAT_BASES)}")
                need(isinstance(label, str) and label.strip(), f"{here}: when.label missing")
                label = label if isinstance(label, str) else ""
                if basis == "oral":
                    # Oral tradition is labelled as such and never given a date
                    need("from" not in bw and "to" not in bw and not re.search(r"\d", label),
                         f"{here}: an oral-tradition beat has no date and no year in its label")
                    continue
                need(isinstance(bw.get("from"), int) and isinstance(bw.get("to"), int) and bw["from"] <= bw["to"]
                     and when.get("from", bw["from"]) <= bw["from"] and bw["to"] <= when.get("to", bw["to"]),
                     f"{here}: when.from and when.to must be whole years inside the scene's years")
                if basis == "chronicle":
                    need("Chronicle" in label, f"{here}: a date reckoned from a chronicle must say so in its label")
                if basis == "differ":
                    need("differ" in label.lower(), f"{here}: a disputed date must say that the sources differ")
                if basis == "account":
                    need("account" in label.lower(), f"{here}: a date from a writer's account must say so in its label")
                if isinstance(bw.get("from"), int):
                    need(last_year is None or bw["from"] >= last_year, f"{here}: dated beats must not go back in time")
                    last_year = bw["from"]
            appear = sc.get("appear", {})
            need(isinstance(appear, dict), f"{where}: appear must map places and ties to seconds")
            appear = appear if isinstance(appear, dict) else {}
            for fid, at in appear.items():
                kind = features.get(fid, {}).get("kind")
                need(fid in shown and kind in ("point", "link")
                     and isinstance(at, (int, float)) and 0 <= at < sc.get("duration", reading_seconds(sc.get("text", ""))),
                     f"{where}: appear needs places or ties the scene shows and times inside the scene")
                if kind == "link":
                    # A tie is drawn only once both its places are on the map
                    ends = [appear.get(features[fid].get(k), 0) for k in ("from", "to")]
                    need(all(isinstance(e, (int, float)) and isinstance(at, (int, float)) and e < at for e in ends),
                         f"{where}: a tie's appear time must come after both its places' appear times")
            check_notes(where, sc, features, need)
            previous_cue = -1
            for cue in sc.get("camera_path", []):
                valid = isinstance(cue, dict) and placed(cue.get("center"))
                need(valid and 2 <= cue.get("zoom", 0) <= 11 and isinstance(cue.get("at"), (int, float))
                     and previous_cue < cue["at"] < sc.get("duration", reading_seconds(sc.get("text", "")))
                     and isinstance(cue.get("dur"), (int, float)) and cue["dur"] > 0
                     and cue["at"] + cue["dur"] <= sc.get("duration", reading_seconds(sc.get("text", ""))),
                     f"{where}: camera_path needs ordered times, bounded centres/zooms and positive durations")
                if isinstance(cue, dict) and isinstance(cue.get("at"), (int, float)):
                    previous_cue = cue["at"]
            for fid in shown:
                f = features.get(fid, {})
                if f.get("type") == "campaign":
                    for pid, stop in (f["stops"] if isinstance(f.get("stops"), dict) else {}).items():
                        try:
                            y = parse_campaign_stop(stop)["year"]
                            need(when["from"] <= y < when["to"] + 1,
                                 f"{where}: campaign stop {pid} is outside the scene's years")
                        except (ValueError, KeyError, TypeError):
                            pass  # malformed stops or scene years have their own diagnostics
                ends = ([f.get("from"), f.get("to")] if f.get("kind") == "link"
                        else f.get("path", []) if f.get("kind") == "move" else [])
                missing = [e for e in ends if e not in shown]
                need(not missing, f"{where}: {fid} joins {', '.join(map(str, missing))}, which the scene does not show")
                m = f.get("monument")
                if sc.get("monuments", True) and isinstance(m, dict) and all(type(m.get(k)) is int for k in ("from", "to")):
                    need(m["from"] <= when.get("from", -10**10) <= when.get("to", 10**10) <= m["to"],
                         f"{where}: monument is outside its documented interval")
                if sc.get("monuments", True) and isinstance(m, dict) and isinstance(m.get("parts"), list):
                    check_part_times(where, fid, m["parts"], sc, need)
                e = emblems.get(f.get("emblem"))
                if e and e["tier"] != "none" and when.get("from") is not None and when.get("to") is not None:
                    need(emblem_fits(e, when), f"{where}: shows the {f['emblem']} emblem outside its documented years")
            for fid, how in sc.get("control", {}).items():
                need(fid in shown and features.get(fid, {}).get("kind") == "point",
                     f"{where}: control of {fid!r}, which is not a place the scene shows")
                need(how in CONTROL, f"{where}: control must be one of {', '.join(CONTROL)}")
                if how == "taken":
                    need(any(features.get(m, {}).get("type") == "campaign" and fid in features[m]["path"]
                             for m in shown), f"{where}: {fid} is taken, but no campaign in the scene reaches it")
            # Anything still marked to-check may only be shown if the scene says so
            unchecked = [fid for fid in shown if features.get(fid, {}).get("status") == "to-check"]
            unchecked += [features[fid]["emblem"] for fid in shown if features.get(fid, {}).get("emblem") in emblems
                          and emblems[features[fid]["emblem"]]["tier"] != "none"
                          and emblems[features[fid]["emblem"]]["status"] == "to-check"]
            need(not unchecked or sc.get("unchecked"),
                 f"{where}: shows {', '.join(unchecked)}, still marked to-check; check them, "
                 f"or say what is unchecked in the scene's unchecked note")
            if sc.get("snapshot"):
                need(sc["snapshot"] in snapshots, f"{where}: unknown snapshot {sc['snapshot']!r}")
            cite(where, sc.get("sources"))
            need("{" not in sc.get("text", ""), f"{where}: text still has a {{placeholder}}")
            for fid in sc.get("furnace", []):
                need(fid in sc.get("show", []), f"{where}: furnace glow on {fid!r}, which the scene does not show")
            if "mood" in sc:
                need(sc["mood"] in MOODS, f"{where}: mood must be one of {', '.join(MOODS)}")
            if any(features.get(fid, {}).get("type") == "campaign" for fid in shown):
                try:
                    campaign_clock(sc, features, sc.get("duration", reading_seconds(sc.get("text", ""))))
                except ValueError as error:
                    need(False, f"{where}: {error}")
                except (KeyError, TypeError):
                    pass  # feature/date diagnostics above describe invalid input
            for e in sc.get("effects", []):
                need(e.get("type") in EFFECTS and isinstance(e.get("at"), (int, float)) and 0 <= e["at"] < 1,
                     f"{where}: an effect needs type {', '.join(EFFECTS)} and at between 0 and 1 (part of the scene)")
                if e.get("type") == "shatter":
                    need(e.get("features") and all(f in sc.get("show", []) for f in e["features"]),
                         f"{where}: shatter needs features that the scene shows")
                if e.get("type") == "pulse":
                    need(e.get("state") in states and sc.get("snapshot"), f"{where}: pulse needs a state on a state map")
                if e.get("type") == "arc":
                    for end in ("from", "to"):
                        lat, lon = e.get(end, [0, 0])
                        need(LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]
                             and e.get(end + "_label"), f"{where}: arc {end} must be inside the map area and have a {end}_label")

    return problems


# --- Building the page ---------------------------------------------------------------

def reading_seconds(text):
    """Time to show a scene while playing: enough to read it at a calm pace."""
    return max(8, round(len(text.split()) * 0.33 + 4))


def parse_campaign_stop(stop):
    """Validate CE ISO dates at their stated precision; do not invent missing month/day evidence."""
    if not isinstance(stop, dict):
        raise ValueError("a stop needs a date and precision")
    precision = stop.get("precision")
    patterns = {"year": r"\d{4}", "month": r"\d{4}-\d{2}", "day": r"\d{4}-\d{2}-\d{2}"}
    raw = stop.get("date")
    if not isinstance(precision, str) or precision not in patterns or not isinstance(raw, str) or not re.fullmatch(patterns[precision], raw):
        raise ValueError("stop date must be ISO YYYY, YYYY-MM or YYYY-MM-DD matching its precision")
    if not isinstance(stop.get("approximate", False), bool):
        raise ValueError("approximate must be true or false")
    parsed = date.fromisoformat(raw + {"year": "-01-01", "month": "-01", "day": ""}[precision])
    year = parsed.year + (parsed - date(parsed.year, 1, 1)).days / (366 if isleap(parsed.year) else 365)
    label = stop.get("label", raw)
    if not isinstance(label, str) or not label.strip():
        raise ValueError("stop label must be non-empty text")
    if stop.get("approximate"):
        label = "approx. " + label
    if precision != "day":
        label += f" ({precision} only)"
    return dict(stop, year=year, label=label)


def campaign_clock(scene, features, duration):
    """One chronological clock for every campaign, its arrivals and the displayed year.

    Missing month/day components anchor an interval at its beginning for presentation only;
    labels retain the evidence's precision. Equal dates hold the year while a leg draws.
    """
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("scene duration must be a finite positive number")
    events = []
    campaigns = {}
    for fid in scene.get("show", []):
        f = features.get(fid, {})
        if f.get("type") != "campaign":
            continue
        if not isinstance(f.get("stops"), dict):
            raise ValueError("campaign needs a structured stops mapping")
        campaigns[fid] = []
        for pid in f["path"]:
            stop = dict(parse_campaign_stop(f.get("stops", {}).get(pid)), id=pid)
            campaigns[fid].append(stop)
            events.append(stop)
    if not events:
        return None
    events.sort(key=lambda stop: stop["year"])
    end_year = scene["when"]["to"]
    first, last = scene["when"]["from"], end_year + 1 - 1 / (366 if isleap(end_year) else 365)
    anchors = ([{"year": first}] if first < events[0]["year"] else []) + events
    if last > events[-1]["year"]:
        anchors.append({"year": last})
    points = sum(features.get(fid, {}).get("kind") == "point" for fid in scene.get("show", []))
    start = 1 + max(0, points - 1) * min(1.2, duration * .4 / max(1, points)) + .6
    minimum = 1.8
    spare = duration - 2 - start - minimum * (len(anchors) - 1)
    if spare < 0:
        raise ValueError("campaign needs a longer scene duration for readable dated legs")
    span = anchors[-1]["year"] - anchors[0]["year"]
    t = start
    for i, anchor in enumerate(anchors):
        if i:
            fraction = (anchor["year"] - anchors[i - 1]["year"]) / span if span else 0
            t += minimum + spare * fraction
        anchor["at"] = t
    return {"knots": [[stop["at"], stop["year"]] for stop in anchors], "campaigns": campaigns}


def guide_art():
    path = os.path.join(HISTORY_DIR, "art", "zomo-poses.png")
    with open(path, "rb") as f:
        png = f.read()
    if png[:8] != b"\x89PNG\r\n\x1a\n" or len(png) > 8_000_000:
        raise ValueError("Zomo pose atlas must be a PNG smaller than 8 MB")
    width, height = struct.unpack(">II", png[16:24])
    if width % 4 or height % 2 or not width or not height:
        raise ValueError("Zomo pose atlas must have a four-column, two-row grid")
    return {"name": "Zomo", "columns": 4, "rows": 2, "width": width, "height": height,
            "image": "data:image/png;base64," + base64.b64encode(png).decode("ascii")}


def page_data(chapters, sources, states, arcs, users, background, emblems=None, plates=None):
    globe = plates is not None and any(sc.get("view") == "globe" for ch in chapters for sc in ch["scenes"])
    out = {"chapters": [], "sources": sources, "built": date.today().isoformat(), "background": background,
           "emblems": emblems or {}, "plates": plates if globe else None, "guide": guide_art(),
           "motifs": read_json(os.path.join(HISTORY_DIR, "motifs.json"))["records"],
           "cultural_mark": "data:image/svg+xml;base64," + base64.b64encode(
               Path(HISTORY_DIR, "art", "arewa-cultural-study.svg").read_bytes()).decode("ascii"),
           # Each state as lists of arc numbers (negative: walk the arc backwards); the page rebuilds the rings
           "states": {c: {"name": s["name"], "rings": s["arc_refs"]} for c, s in states.items()},
           "arcs": arcs}
    for ch in chapters:
        snaps = ch.get("snapshots", {})
        colours = snapshot_colours(snaps)
        snap_out = {}
        for key, snap in snaps.items():
            group_of = {c: g["name"] for g in snap["groups"] for c in g["members"]}
            group_of.update({c: "split:" + c for c in snap.get("split", {})})
            thick = [i for i, u in enumerate(users)
                     if len(u) == 1 or group_of[u[0]] != group_of[u[1]]]
            snap_out[key] = {
                "label": snap["label"], "count": snap["count"], "count_note": snap.get("count_note"),
                "unit": snap.get("unit", "states"),
                "group_of": group_of, "colours": colours[key], "thick": thick,
                "labels": [{"name": g["name"], "at": label_point(g["members"], states),
                            "not_a_state": bool(g.get("not_a_state"))} for g in snap["groups"]],
                "split": {c: dict(sp, colours=[colours[key].get(p, OTHER_COLOUR) for p in sp["parents"]])
                          for c, sp in snap.get("split", {}).items()},
            }
        scenes = [dict(sc, duration=sc.get("duration", reading_seconds(sc["text"])), base=base_for(sc))
                  for sc in ch["scenes"]]
        features = {f["id"]: dict(f) for f in ch.get("features", [])}
        for f in features.values():
            if f.get("type") == "campaign":
                f["dates"] = {pid: parse_campaign_stop(stop)["label"] for pid, stop in f["stops"].items()}
        for sc in scenes:
            clock = campaign_clock(sc, features, sc["duration"])
            if clock:
                sc["campaign_clock"] = clock
        if globe and ch.get("area") == "world":
            # Which plate each place, line and camera rides on, so the page can move them. A line moves
            # with the plate under its first point, so it keeps its shape.
            for f in features.values():
                if f["kind"] == "point":
                    f["plate"] = plate_of(*f["coordinates"], plates)
                elif f["kind"] == "line":
                    f["plate"] = plate_of(*f["path"][0], plates)
            for sc in scenes:
                if sc.get("view") == "globe":
                    sc["camera"] = dict(sc["camera"], plate=plate_of(*sc["camera"]["center"], plates))
        out["chapters"].append({
            "id": ch["id"], "title": ch["title"], "period": ch["period"], "intro": ch["intro"],
            "method": ch.get("method"), "area": ch.get("area"), "clock": ch.get("clock"), "reference": ch.get("reference", False), "features": features,
            "snapshots": snap_out, "scenes": scenes,
        })
    return out


def source_links(ids, sources):
    return ", ".join(f'<a href="{html.escape(sources[s]["url"])}">{html.escape(sources[s]["title"])}</a>'
                     for s in ids)


STATUS_WORDS = {"firm": "Firm", "approx": "Approximate", "disputed": "Disputed", "to-check": "To check"}
TIER_WORDS = {"flag": "Flag", "symbol": "Symbol, not a flag", "none": "Nothing documented"}
FORM_WORDS = {"landmass": "Continent", "lake": "Lake", "kingdom": "Kingdom", "city-state": "City-state", "network": "Centre of a network",
              "caliphate": "Seat of the caliphate", "emirate": "Emirate", "communities": "Self-governing communities"}
LINK_WORDS = {"allegiance": "Allegiance", "tribute": "Tribute", "alliance": "Alliance", "trade": "Trade",
              "ritual": "Ritual authority"}
MOVE_WORDS = {"migration": "Migration", "campaign": "Military campaign", "trade": "Trade route"}
LINE_WORDS = {"rift": "Rift"}
CONTROL_WORDS = {"claimed": "claimed on paper (hatched)", "held": "held (solid)",
                 "taken": "claimed, then taken during this scene"}


def emblem_text(e, sources):
    """One emblem in words: what is documented, how sure, and where it comes from."""
    esc = html.escape
    years = (f" ({e['from'] if 'from' in e else ''} to {e['to'] if 'to' in e else 'today'})"
             if "from" in e or "to" in e else "")
    return (f"<em>{esc(TIER_WORDS[e['tier']])}{esc(years)}:</em> {esc(e['description'])}"
            + (f" {esc(e['note'])}" if e.get("note") else "")
            + (f" <em>Disputed:</em> {esc(e['disputed'])}" if e.get("disputed") else "")
            + f" <em>How sure:</em> {STATUS_WORDS[e['status']]}."
            + (f" <em>Sources:</em> {source_links(e['sources'], sources)}." if e.get("sources") else ""))


def feature_text(f, sc, features, sources, emblems):
    """One thing on the map in words, for the text version."""
    e = html.escape
    kind = f["kind"]
    if kind == "link":
        head = (f"<strong>{e(f['name'])}.</strong> {e(LINK_WORDS[f['type']])}, from "
                f"{e(features[f['from']]['name'])} to {e(features[f['to']]['name'])}. {e(f['what'])}")
    elif kind == "move":
        dates = ({pid: parse_campaign_stop(stop)["label"] for pid, stop in f["stops"].items()}
                 if f.get("type") == "campaign" else f.get("dates", {}))
        stops = " to ".join(features[p]["name"] + (f" ({dates[p]})" if p in dates else "")
                            for p in f["path"])
        extra = "".join(f" <em>{label}:</em> {e(f[k])}." for k, label in (("period", "When"), ("goods", "Goods"))
                        if f.get(k))
        head = f"<strong>{e(f['name'])}.</strong> {e(MOVE_WORDS[f['type']])}: {e(stops)}. {e(f['what'])}{extra}"
        if f.get("uncertain"):
            head += f" <em>Uncertain part of the route:</em> {e(f['uncertain'])}."
    elif kind == "line" and f.get("type") == "river":
        head = f"<strong>{e(f['name'])}.</strong> Physical river locator. {e(f['what'])}"
    elif kind == "line":
        head = (f"<strong>{e(f['name'])}.</strong> {e(LINE_WORDS[f['type']])}, active about {f['active'][0]} "
                f"to {f['active'][1]} million years ago. {e(f['what'])}")
    else:
        form = f" ({FORM_WORDS[f['form']]})" if f.get("form") else ""
        head = f"<strong>{e(f['name'])}{e(form)}.</strong> {e(f['what'])}"
        if f.get("monument") and sc.get("monuments", True):
            head += f" <em>Schematic:</em> {e(f['monument']['note'])}"
            dated = [p for p in f["monument"].get("parts", []) if not p.get("natural") and not p.get("standing")]
            if dated:
                head += " <em>What appears when:</em> " + "; ".join(e(p["label"]) for p in dated) + "."
        if f.get("reach_note"):
            head += f" <em>Halo or field:</em> {e(f['reach_note'])}"
        how = sc.get("control", {}).get(f["id"])
        if how:
            head += f" <em>Colonial claim:</em> {e(CONTROL_WORDS[how])}."
    out = (f"<li>{head} <em>Evidence:</em> {e(f['evidence'])}."
           + (f" <em>Location:</em> {e(f['location'])}" if f.get("location") else "")
           + (f" <em>Disputed:</em> {e(f['disputed'])}" if f.get("disputed") else "")
           + f" <em>How sure:</em> {STATUS_WORDS[f['status']]}."
           + f" <em>Sources:</em> {source_links(f['sources'], sources)}.")
    if f.get("emblem"):
        out += f" <em>Emblem:</em> {emblem_text(emblems[f['emblem']], sources)}"
    return out + "</li>"


def transcript(chapters, sources, states, emblems=None):
    """The whole page as plain HTML text: every scene, map feature, emblem and source.
    It works without JavaScript and is what screen readers read."""
    e = html.escape
    emblems = emblems or {}
    chapters = expand_bases(chapters)   # a city carrying on from another lists only what is new
    parts = []
    for ch in chapters:
        parts.append(f'<section class="tr-chapter" id="text-{e(ch["id"])}">')
        parts.append(f'<h3>{e(ch["title"])} <span class="tr-period">({e(ch["period"])})</span></h3>')
        parts.append(f"<p>{e(ch['intro'])}</p>")
        if ch.get("method"):
            parts.append(f'<p class="tr-method"><strong>How to read this map.</strong> {e(ch["method"])}</p>')
        features = {f["id"]: f for f in ch.get("features", [])}
        for sc in ch["scenes"]:
            if sc.get("beats") and all("when" in b for b in sc["beats"]):
                # A scene told in dated beats: each line with the date it rests on
                parts.append(f'<h4>{e(sc["when"]["label"])}: {e(sc["title"])}</h4><ol class="tr-beats">'
                             + "".join(f'<li><em>{e(b["when"]["label"])}.</em> {e(b["text"])}</li>' for b in sc["beats"])
                             + "</ol>")
            else:
                parts.append(f'<h4>{e(sc["when"]["label"])}: {e(sc["title"])}</h4><p>{e(sc["text"])}</p>')
            if sc.get("disputed"):
                parts.append(f'<p class="tr-disputed"><strong>Disputed:</strong> {e(sc["disputed"])}</p>')
            if sc.get("unchecked"):
                parts.append(f'<p class="tr-disputed"><strong>Not yet checked:</strong> {e(sc["unchecked"])}</p>')
            if sc.get("background") == "modern-reference":
                parts.append(f'<p class="tr-method"><strong>Modern reference map:</strong> {e(sc["background_note"])}</p>')
            items = [feature_text(features[fid], sc, features, sources, emblems) for fid in sc.get("show", [])]
            if sc.get("snapshot"):
                snap = ch["snapshots"][sc["snapshot"]]
                for g in snap["groups"]:
                    today = ", ".join(states[c]["name"] for c in g["members"])
                    items.append(f"<li><strong>{e(g['name'])}</strong>: today's {e(today)}.</li>")
                for code, sp in snap.get("split", {}).items():
                    items.append(f"<li><strong>{e(states[code]['name'])} (today)</strong>: split between "
                                 f"{e(' and '.join(sp['parents']))}. {e(sp['note'])}"
                                 + (f" <em>Disputed:</em> {e(sp['disputed'])}" if sp.get("disputed") else "")
                                 + "</li>")
            if items:
                parts.append('<ul class="tr-features">' + "".join(items) + "</ul>")
            parts.append(f'<p class="tr-sources">Sources: {source_links(sc["sources"], sources)}.</p>')
        parts.append("</section>")
    if emblems:
        parts.append('<section class="tr-chapter" id="text-emblems"><h3>Flags, emblems and symbols</h3>'
                     "<p>What is documented for each actor. A flag or symbol is drawn only from a cited description; "
                     "where nothing is documented, nothing is invented.</p><ul class=\"tr-features\">")
        for em in emblems.values():
            parts.append(f"<li><strong>{e(em['actor'])}.</strong> {emblem_text(em, sources)}</li>")
        parts.append("</ul></section>")
    parts.append('<section class="tr-chapter" id="text-sources"><h3>All sources</h3><ul class="tr-all-sources">')
    for sid, s in sources.items():
        parts.append(f'<li id="src-{e(sid)}"><a href="{e(s["url"])}">{e(s["title"])}</a>. {e(s.get("author", ""))}, '
                     f'{e(s.get("year", ""))}. <em>{e(s.get("kind", ""))}.</em> Use and rights: {e(s["rights"])} '
                     f'What was checked: {e(s["checked"])}</li>')
    parts.append("</ul></section>")
    return "\n".join(parts)


def build():
    sources = read_json(SOURCES_PATH)
    chapters = [read_json(os.path.join(HISTORY_DIR, "chapters", f"{c}.json")) for c in CHAPTERS]
    states, arcs, users = load_states()
    emblems = load_emblems()
    plates = load_plates()
    cited = set()
    problems = check_emblems(emblems, sources, cited) + check(chapters, sources, states, cited, emblems, plates)
    if problems:
        sys.exit("Not building the history page:\n  - " + "\n  - ".join(problems))
    for sid in sorted(set(sources) - cited - MAP_SOURCES):
        print(f"Note: source {sid} is not cited by any scene, feature or emblem.")
    chapters = expand_bases(chapters)

    data = page_data(chapters, sources, states, arcs, users, load_background(), emblems, plates)
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    for slot in ("{{DATA}}", "{{TRANSCRIPT}}", "{{BUILT}}"):
        if template.count(slot) != 1:
            sys.exit(f"{TEMPLATE_PATH} must hold {slot} exactly once, not {template.count(slot)} times")
    # "</" inside the JSON would end the <script> block early
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (template.replace("{{DATA}}", data_json)
                    .replace("{{TRANSCRIPT}}", transcript(chapters, sources, states, emblems))
                    .replace("{{BUILT}}", data["built"]))

    # The page must say it is an unreviewed draft and credit the boundary and background data
    for must in ("Unreviewed draft", "GRID3", "geoBoundaries", "CC BY 4.0", "Natural Earth"):
        if must not in page:
            sys.exit(f"Not building the history page: the page does not mention {must!r}.")
    return page, data


def main():
    parser = argparse.ArgumentParser(description="Build Taswira's sourced history page or an explicit local preview.")
    parser.add_argument("--check", action="store_true", help="validate and build in memory without writing")
    parser.add_argument("--output", default=OUTPUT_PATH, help="write a local preview here instead of docs/history.html")
    args = parser.parse_args()
    page, data = build()
    scenes = sum(len(c["scenes"]) for c in data["chapters"])
    if args.check:
        print(f"Checks passed: {len(data['chapters'])} chapters, {scenes} scenes, "
              f"{len(data['sources'])} sources. Nothing written (--check).")
        return
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(page)
    size_kb = os.path.getsize(args.output) / 1000
    print(f"Checks passed: {len(data['chapters'])} chapters, {scenes} scenes, {len(data['sources'])} sources.")
    print(f"Wrote {args.output} ({size_kb:.0f} KB). Open it in your browser to try it.")
    if os.path.abspath(args.output) != os.path.abspath(OUTPUT_PATH):
        print("Local preview only. The default live-site output was not changed.")
        return
    print("\nTo publish it later, commit and push it:")
    print("  git add docs/history.html")
    print('  git commit -m "Update history page"')
    print("  git push")


if __name__ == "__main__":
    main()


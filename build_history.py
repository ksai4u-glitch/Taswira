"""
Build the Nigeria history page as docs/history.html.

The page plays short chapters of Nigeria's history on a map, scene by scene.
Everything it shows comes from three kinds of files in history/:

  history/chapters/<id>.json   the scenes, what is on the map in each, and the text
  history/sources.json         every source a scene or map feature cites
  history/geo/*.topojson       today's state borders (simplified, see history/geo/README.md)

This script checks those files (dates, places, sources, which state belonged to
which at each date), fills in history/template.html and writes docs/history.html.
It makes no API requests and is separate from publish.py, so the history page
does not change when the UCDP data does.

    python build_history.py           check, then write docs/history.html
    python build_history.py --check   only check, write nothing

Uses only the Python standard library.
"""

import colorsys
import html
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(HERE, "history")
TEMPLATE_PATH = os.path.join(HISTORY_DIR, "template.html")
SOURCES_PATH = os.path.join(HISTORY_DIR, "sources.json")
STATES_PATH = os.path.join(HISTORY_DIR, "geo", "nga-states-2022.topojson")
OUTPUT_PATH = os.path.join(HERE, "docs", "history.html")

# Chapters in the order the page plays them
CHAPTERS = ["nok", "states"]

# Rough box around Nigeria, to catch swapped or mistyped coordinates
LAT_RANGE = (4.0, 14.0)
LON_RANGE = (2.5, 15.0)
SLUG = re.compile(r"^[a-z0-9-]+$")

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

def check(chapters, sources, states, cited=None):
    """Return a list of problems. An empty list means the page can be built.
    Pass a set as cited to collect the ids of the sources that are used."""
    problems = []
    cited = set() if cited is None else cited

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

    seen_chapters = set()
    for ch in chapters:
        cid = ch.get("id", "?")
        need(SLUG.match(cid) and cid not in seen_chapters, f"chapter {cid}: id must be unique, a-z 0-9 -")
        seen_chapters.add(cid)
        for field in ("title", "period", "intro", "scenes"):
            need(ch.get(field), f"chapter {cid}: missing {field}")

        features = {}
        for f in ch.get("features", []):
            fid = f.get("id", "?")
            where = f"{cid}/{fid}"
            need(fid not in features, f"{where}: duplicate feature id")
            features[fid] = f
            for field in ("name", "what", "evidence", "location"):
                need(f.get(field), f"{where}: missing {field}")
            need("disputed" in f, f"{where}: say disputed: null or explain the disagreement")
            cite(where, f.get("sources"))
            if f.get("kind") == "point":
                lat, lon = f.get("coordinates", [None, None])
                need(isinstance(lat, (int, float)) and LAT_RANGE[0] <= lat <= LAT_RANGE[1]
                     and isinstance(lon, (int, float)) and LON_RANGE[0] <= lon <= LON_RANGE[1],
                     f"{where}: coordinates [lat, lon] are outside Nigeria")
            else:
                need(False, f"{where}: unknown kind {f.get('kind')!r}")

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
            cam = sc.get("camera", {})
            lat, lon = cam.get("center", [0, 0])
            need(LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]
                 and 4 <= cam.get("zoom", 0) <= 11, f"{where}: camera centre or zoom out of range")
            for fid in sc.get("show", []) + sc.get("dim", []):
                need(fid in features, f"{where}: shows unknown feature {fid!r}")
            if sc.get("snapshot"):
                need(sc["snapshot"] in snapshots, f"{where}: unknown snapshot {sc['snapshot']!r}")
            cite(where, sc.get("sources"))
            need("{" not in sc.get("text", ""), f"{where}: text still has a {{placeholder}}")

    return problems


# --- Building the page ---------------------------------------------------------------

def reading_seconds(text):
    """Time to show a scene while playing: enough to read it at a calm pace."""
    return max(8, round(len(text.split()) * 0.33 + 4))


def page_data(chapters, sources, states, arcs, users):
    out = {"chapters": [], "sources": sources, "built": date.today().isoformat(),
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
                "group_of": group_of, "colours": colours[key], "thick": thick,
                "labels": [{"name": g["name"], "at": label_point(g["members"], states),
                            "not_a_state": bool(g.get("not_a_state"))} for g in snap["groups"]],
                "split": {c: dict(sp, colours=[colours[key].get(p, OTHER_COLOUR) for p in sp["parents"]])
                          for c, sp in snap.get("split", {}).items()},
            }
        scenes = [dict(sc, duration=sc.get("duration", reading_seconds(sc["text"]))) for sc in ch["scenes"]]
        out["chapters"].append({
            "id": ch["id"], "title": ch["title"], "period": ch["period"], "intro": ch["intro"],
            "method": ch.get("method"), "features": {f["id"]: f for f in ch.get("features", [])},
            "snapshots": snap_out, "scenes": scenes,
        })
    return out


def source_links(ids, sources):
    return ", ".join(f'<a href="{html.escape(sources[s]["url"])}">{html.escape(sources[s]["title"])}</a>'
                     for s in ids)


def transcript(chapters, sources, states):
    """The whole page as plain HTML text: every scene, map feature and source.
    It works without JavaScript and is what screen readers read."""
    e = html.escape
    parts = []
    for ch in chapters:
        parts.append(f'<section class="tr-chapter" id="text-{e(ch["id"])}">')
        parts.append(f'<h3>{e(ch["title"])} <span class="tr-period">({e(ch["period"])})</span></h3>')
        parts.append(f"<p>{e(ch['intro'])}</p>")
        if ch.get("method"):
            parts.append(f'<p class="tr-method"><strong>How to read this map.</strong> {e(ch["method"])}</p>')
        features = {f["id"]: f for f in ch.get("features", [])}
        for sc in ch["scenes"]:
            parts.append(f'<h4>{e(sc["when"]["label"])}: {e(sc["title"])}</h4><p>{e(sc["text"])}</p>')
            if sc.get("disputed"):
                parts.append(f'<p class="tr-disputed"><strong>Disputed:</strong> {e(sc["disputed"])}</p>')
            items = []
            for fid in sc.get("show", []):
                f = features[fid]
                items.append(
                    f"<li><strong>{e(f['name'])}.</strong> {e(f['what'])} "
                    f"<em>Evidence:</em> {e(f['evidence'])}. <em>Location:</em> {e(f['location'])}"
                    + (f" <em>Disputed:</em> {e(f['disputed'])}" if f.get("disputed") else "")
                    + f" <em>Sources:</em> {source_links(f['sources'], sources)}.</li>")
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
    cited = set()
    problems = check(chapters, sources, states, cited)
    if problems:
        sys.exit("Not building the history page:\n  - " + "\n  - ".join(problems))
    for sid in sorted(set(sources) - cited - {"grid3-states", "esri-tiles"}):   # those two are credited on the map
        print(f"Note: source {sid} is not cited by any scene or feature.")

    data = page_data(chapters, sources, states, arcs, users)
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    # "</" inside the JSON would end the <script> block early
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (template.replace("{{DATA}}", data_json)
                    .replace("{{TRANSCRIPT}}", transcript(chapters, sources, states))
                    .replace("{{BUILT}}", data["built"]))

    # The page must say it is an unreviewed draft and credit the boundary data
    for must in ("Unreviewed draft", "GRID3", "geoBoundaries", "CC BY 4.0"):
        if must not in page:
            sys.exit(f"Not building the history page: the page does not mention {must!r}.")
    return page, data


def main():
    page, data = build()
    scenes = sum(len(c["scenes"]) for c in data["chapters"])
    if "--check" in sys.argv[1:]:
        print(f"Checks passed: {len(data['chapters'])} chapters, {scenes} scenes, "
              f"{len(data['sources'])} sources. Nothing written (--check).")
        return
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(page)
    size_kb = os.path.getsize(OUTPUT_PATH) / 1000
    print(f"Checks passed: {len(data['chapters'])} chapters, {scenes} scenes, {len(data['sources'])} sources.")
    print(f"Wrote {OUTPUT_PATH} ({size_kb:.0f} KB). Open it in your browser to try it.")
    print("\nTo publish it later, commit and push it:")
    print("  git add docs/history.html")
    print('  git commit -m "Update history page"')
    print("  git push")


if __name__ == "__main__":
    main()

"""
Build the borders map ("Who drew Africa's borders?").

    python build_borders.py            # checks the files and writes a draft preview, previews/borders.html
    python build_borders.py --publish  # writes the live page, docs/borders.html
    python build_borders.py --check    # only checks

The preview carries a Draft badge and asks search engines not to list it. Only --publish writes
docs/, and the live site changes only when that change is merged.
Standard library only. The borders come from borders/geo/scramble.json (see borders/geo/README.md).
"""

import argparse
import datetime
import json
import os
import re

from vendor import inline_vendor

HERE = os.path.dirname(os.path.abspath(__file__))
BORDERS = os.path.join(HERE, "borders")
OUTPUT = os.path.join(HERE, "previews", "borders.html")
SITE_PAGE = os.path.join(HERE, "docs", "borders.html")
BACKGROUND = os.path.join(HERE, "history", "geo", "natural-earth-background.json")
DATE = re.compile(r"^\d{4}(-\d{2}-\d{2})?$")


def load(name):
    with open(name, encoding="utf-8") as f:
        return json.load(f)


def check(story, geo):
    """Return a list of problems; empty when the story and borders agree."""
    problems = []
    sources = story["sources"]
    if "cshapes-2" not in sources:
        problems.append("sources must include cshapes-2 (every border comes from it)")
    for sid, s in sources.items():
        for field in ("cite", "used_for"):
            if not s.get(field):
                problems.append(f"source {sid}: missing {field}")
    powers = story["powers"]
    for code in story["european"]:
        if code not in powers:
            problems.append(f"european power {code} has no colour")
    for owner, group in story["owner_groups"].items():
        if group not in powers:
            problems.append(f"owner {owner}: group {group} has no colour")
    first, last = geo["first"], geo["last"]
    for u in geo["units"]:
        owner = str(u["owner"])
        self_ruled = u["owner"] == u["gw"] and u["status"] == "independent"
        if owner not in powers and owner not in story["owner_groups"] and not self_ruled:
            problems.append(f"{u['name']} ({u['gw']}): owner {owner} has no power or group")
        names = story["names"].get(str(u["gw"]))
        if not names:
            problems.append(f"{u['name']} ({u['gw']}): no period name in story.json")
    for gw, names in story["names"].items():
        dates = [n[0] for n in names]
        if not all(len(n) in (2, 3) for n in names):
            problems.append(f"names for {gw}: each entry is [from, name] or [from, name, map label]")
        if not all(DATE.match(d) for d in dates) or dates != sorted(dates):
            problems.append(f"names for {gw}: dates must be YYYY or YYYY-MM-DD, in order")
    for c in story["corrections"]:
        if c.get("to") and not (DATE.match(c["to"]) and c["from"] < c["to"]):
            problems.append(f"correction for {c['gw']}: 'to' must be a date after 'from'")
        if c["owner"] not in powers or not c.get("note") or not c.get("sources"):
            problems.append(f"correction for {c['gw']}: needs a known owner, a note and sources")
        problems += [f"correction for {c['gw']}: unknown source {s}" for s in c.get("sources", []) if s not in sources]
    previous = ""
    for m in story["moments"]:
        where = f"moment {m.get('date')} {m.get('title')!r}"
        if not DATE.match(m["date"]) or len(m["date"]) != 10:
            problems.append(f"{where}: date must be YYYY-MM-DD")
        elif not first <= m["date"] <= last:
            problems.append(f"{where}: outside {first} to {last}")
        if m["date"] <= previous:
            problems.append(f"{where}: moments must be in date order")
        previous = m["date"]
        if not m.get("sources"):
            problems.append(f"{where}: no sources")
        problems += [f"{where}: unknown source {s}" for s in m.get("sources", []) if s not in sources]
        known = {u["gw"] for u in geo["units"] if u["start"] <= m["date"] <= u["end"]}
        problems += [f"{where}: highlight {gw} is not on the map that day" for gw in m.get("highlight", []) if gw not in known]
        lon, lat = m["focus"]
        if not (-30 <= lon <= 60 and -40 <= lat <= 40):
            problems.append(f"{where}: focus is not over Africa")
    if story["moments"] and story["moments"][-1]["date"] != last:
        problems.append("the last moment should be the last date of the borders")
    return problems


def build(output=OUTPUT, built=None, publish=False):
    out = os.path.abspath(output)
    in_docs = os.path.commonpath([out, os.path.join(HERE, "docs")]) == os.path.join(HERE, "docs")
    if in_docs and not publish:
        raise SystemExit("build_borders.py writes docs/ only with --publish")
    story = load(os.path.join(BORDERS, "story.json"))
    geo = load(os.path.join(BORDERS, "geo", "scramble.json"))
    problems = check(story, geo)
    if problems:
        raise SystemExit("borders/ has problems:\n  " + "\n  ".join(problems))
    bg = load(BACKGROUND)
    data = {"story": story, "geo": geo, "background": {"land": bg["land"], "lakes": bg["lakes"]}}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(os.path.join(BORDERS, "template.html"), encoding="utf-8") as f:
        page = f.read()
    if page.count("__DATA__") != 1:
        raise SystemExit("template must hold __DATA__ exactly once")
    built = built or datetime.date.today().isoformat()
    page = page.replace("__DATA__", blob).replace("__BUILT__", built)
    page = page.replace("__TITLE_DRAFT__", "" if publish else " (draft)")
    # <!--draft-->...<!--/draft--> holds what only the preview shows: the badge and the noindex tag.
    page = re.sub(r"<!--draft-->(.*?)<!--/draft-->", "" if publish else r"\1", page, flags=re.S)
    page = inline_vendor(page)
    musts = ("CShapes 2.0", "Schvitz", "Pakenham") + (() if publish else ("Draft", "noindex"))
    for must in musts:
        if must not in page:
            raise SystemExit(f"page lost its {must!r} label")
    if publish and ("noindex" in page or 'class="draft"' in page):
        raise SystemExit("the live page still carries the draft badge or the noindex tag")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    return out, len(page.encode("utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--check", action="store_true", help="only check the files")
    parser.add_argument("--output", help="where to write (default: the preview, or docs/borders.html with --publish)")
    parser.add_argument("--publish", action="store_true", help="write the live page, docs/borders.html")
    args = parser.parse_args()
    if args.check:
        problems = check(load(os.path.join(BORDERS, "story.json")), load(os.path.join(BORDERS, "geo", "scramble.json")))
        print("\n".join(problems) or "borders/ is fine")
        raise SystemExit(1 if problems else 0)
    path, size = build(args.output or (SITE_PAGE if args.publish else OUTPUT), publish=args.publish)
    print(f"Wrote {path} ({size:,} bytes)")

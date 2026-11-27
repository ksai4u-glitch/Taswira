"""
Build the elections map ("How Nigeria voted").

    python build_elections.py            # checks the files and writes a draft preview, previews/elections.html
    python build_elections.py --publish  # writes the live page, docs/elections.html
    python build_elections.py --check    # only checks

The preview carries a Draft badge and asks search engines not to list it. Only --publish writes
docs/, and the live site changes only when that change is merged.
Standard library only. The results come from elections/raw/ and elections/story.json (see elections/README.md).
"""

import argparse
import datetime
import json
import os
import re

from elections import results
from vendor import inline_vendor

HERE = os.path.dirname(os.path.abspath(__file__))
ELECTIONS = os.path.join(HERE, "elections")
OUTPUT = os.path.join(HERE, "previews", "elections.html")
SITE_PAGE = os.path.join(HERE, "docs", "elections.html")
STATES_MAP = os.path.join(HERE, "history", "geo", "nga-states-2022.topojson")
BACKGROUND = os.path.join(HERE, "history", "geo", "natural-earth-background.json")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load(name):
    with open(name, encoding="utf-8") as f:
        return json.load(f)


def check(story, topo):
    """Return a list of problems; empty when the results, the story and the state map agree."""
    problems = []
    sources = story["sources"]
    for sid, s in sources.items():
        for field in ("cite", "used_for"):
            if not s.get(field):
                problems.append(f"source {sid}: missing {field}")
    codes = {g["properties"]["shapeISO"] for g in topo["objects"]["states"]["geometries"]}
    gaps = {g["year"]: g for g in story.get("known_gaps", [])}
    parties = story["parties"]
    previous = 0
    for e in story["elections"]:
        y = e["year"]
        if y <= previous:
            problems.append(f"{y}: elections must be in date order")
        previous = y
        if not (DATE.match(e["polled"]) and DATE.match(e["declared"]) and e["polled"] < e["declared"]):
            problems.append(f"{y}: polled and declared must be dates, polled first")
        if not e.get("sources"):
            problems.append(f"{y}: no sources")
        problems += [f"{y}: unknown source {s}" for s in e.get("sources", []) if s not in sources]
        names = [c["party"] for c in e["candidates"]]
        problems += [f"{y}: party {p} has no colour" for p in names if p not in parties]
        national = e["national"]
        if set(national) != set(names) | {"valid"}:
            problems.append(f"{y}: national totals must give each candidate and the valid votes")
            continue
        if max(names, key=national.get) != e["winner"]:
            problems.append(f"{y}: the winner must have the most votes")
        states = e["states"]
        if set(states) != codes:
            problems.append(f"{y}: states {sorted(set(states) ^ codes)} do not match the state map")
        gap = gaps.get(y)
        sums = {k: sum(s[k] for s in states.values()) for k in national}
        if sums != national and not gap:
            off = {k: sums[k] - national[k] for k in national if sums[k] != national[k]}
            problems.append(f"{y}: states do not add up to the national totals {off}, and known_gaps does not say so")
        rows_off = sorted(s["name"] for s in states.values() if sum(s[p] for p in names) + s["others"] != s["valid"])
        if rows_off != sorted((gap or {}).get("rows_off", [])):
            problems.append(f"{y}: states whose votes do not add up to their total {rows_off}, known_gaps lists {(gap or {}).get('rows_off', [])}")
    for g in story.get("known_gaps", []):
        problems += [f"known gap {g['year']}: unknown source {s}" for s in g.get("sources", []) if s not in sources]
    for c in story.get("corrections", []):
        if not c.get("note") or not c.get("sources"):
            problems.append(f"correction {c['year']} {c['state']}: needs a note and sources")
        problems += [f"correction {c['year']} {c['state']}: unknown source {s}" for s in c.get("sources", []) if s not in sources]
    return problems


def load_all():
    story = results.load(load(os.path.join(ELECTIONS, "story.json")))
    return story, load(STATES_MAP)


def build(output=OUTPUT, built=None, publish=False):
    out = os.path.abspath(output)
    in_docs = os.path.commonpath([out, os.path.join(HERE, "docs")]) == os.path.join(HERE, "docs")
    if in_docs and not publish:
        raise SystemExit("build_elections.py writes docs/ only with --publish")
    story, topo = load_all()
    problems = check(story, topo)
    if problems:
        raise SystemExit("elections/ has problems:\n  " + "\n  ".join(problems))
    for e in story["elections"]:
        del e["raw"]
        for k in ("others_columns", "valid_column"):
            e.pop(k, None)
        for c in e["candidates"]:
            del c["column"]
    bg = load(BACKGROUND)
    data = {"story": story, "states": topo, "background": {"land": bg["land"], "lakes": bg["lakes"]}}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(os.path.join(ELECTIONS, "template.html"), encoding="utf-8") as f:
        page = f.read()
    if page.count("__DATA__") != 1:
        raise SystemExit("template must hold __DATA__ exactly once")
    built = built or datetime.date.today().isoformat()
    page = page.replace("__DATA__", blob).replace("__BUILT__", built)
    page = page.replace("__TITLE_DRAFT__", "" if publish else " (draft)")
    # <!--draft-->...<!--/draft--> holds what only the preview shows: the badge and the noindex tag.
    page = re.sub(r"<!--draft-->(.*?)<!--/draft-->", "" if publish else r"\1", page, flags=re.S)
    page = inline_vendor(page)
    musts = ("INEC", "GRID3", "geoBoundaries") + (() if publish else ("Draft", "noindex"))
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
    parser.add_argument("--output", help="where to write (default: the preview, or docs/elections.html with --publish)")
    parser.add_argument("--publish", action="store_true", help="write the live page, docs/elections.html")
    args = parser.parse_args()
    if args.check:
        problems = check(*load_all())
        print("\n".join(problems) or "elections/ is fine")
        raise SystemExit(1 if problems else 0)
    path, size = build(args.output or (SITE_PAGE if args.publish else OUTPUT), publish=args.publish)
    print(f"Wrote {path} ({size:,} bytes)")

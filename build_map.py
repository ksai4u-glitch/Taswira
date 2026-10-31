"""
Stage 5: build an interactive map from the clean events (Stage 4).

Reads the clean_events table (no API requests), fills in map_template.html
and writes data/<area>_<years>_map.html. Open that file in your browser.

Python does the data; the template (HTML + JavaScript with Leaflet) does the drawing.
Uses only the Python standard library.
"""

import json
import os
import re
import sqlite3
import sys
import webbrowser
from datetime import date
from pathlib import Path

from settings import API_VERSION, AREA_NAME, AREAS, BOUNDS, CANDIDATE_VERSIONS, FILE_STEM, HEAT_MAX, PERIOD

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "taswira.db")
TEMPLATE_PATH = os.path.join(HERE, "map_template.html")
OUTPUT_PATH = os.path.join(HERE, "data", f"{FILE_STEM}_map.html")

# Only the fields the map page uses, to keep the file small
MAP_FIELDS = [
    "date_start", "date_end", "country", "state", "lga", "place", "latitude", "longitude",
    "violence_label", "side_a", "side_b", "deaths_best", "deaths_low", "deaths_high",
    "dataset_version", "preliminary",
]


def load(db, map_ready):
    """Return clean events as a list of dicts, either map-ready (1) or not (0).
    clean_events already holds exactly the stable + preliminary events to show."""
    db.row_factory = sqlite3.Row
    rows = db.execute(
        f"SELECT {', '.join(MAP_FIELDS)} FROM clean_events "
        "WHERE map_ready = ? ORDER BY date_start",
        (map_ready,),
    ).fetchall()
    return [dict(row) for row in rows]


def pack(events):
    """Store the events column by column instead of as one {...} per event.

    Writing every field name 32,000 times made the page about 12 MB. Here each field
    is one list. Fields with few different values (country, violence type, dates...)
    become a short list of the values plus, for each event, the position of its value
    in that list. The page's JavaScript (unpack) turns this back into one object per event.
    """
    columns = {}
    for field in MAP_FIELDS:
        values = [e[field] for e in events]
        if field in ("latitude", "longitude"):
            values = [round(v, 4) for v in values]   # 4 decimals is about 10 metres
        distinct = sorted(set(values), key=lambda v: (v is None, str(v)))
        if len(distinct) < len(values) / 4:
            position = {v: i for i, v in enumerate(distinct)}
            columns[field] = {"values": distinct, "index": [position[v] for v in values]}
        else:
            columns[field] = values
    return {"count": len(events), "columns": columns}


def to_js(data):
    """JSON that is safe to paste inside a <script> tag.

    Every "<" becomes \\u003c (the same character to JavaScript), so no text from the
    data (a place or armed group name) can close the tag ("</script>") or open an HTML
    comment ("<!--") that would stop the browser seeing the real closing tag."""
    return (json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def fill(page, values):
    """Replace each __NAME__ placeholder in one pass. Replacing them one after another would
    also replace placeholder-like text inside values put in earlier, such as an event
    whose place name contains "__UNMAPPED_JSON__"."""
    pattern = re.compile("|".join(re.escape(k) for k in sorted(values, key=len, reverse=True)))
    return pattern.sub(lambda m: values[m.group(0)], page)


def shown_period(events):
    """The years the map actually covers, e.g. "2020-2026" once preliminary 2026 data is in.
    (PERIOD in settings.py is only the stable release's years.)"""
    years = sorted({e["date_start"][:4] for e in events})
    return years[0] if years[0] == years[-1] else f"{years[0]}-{years[-1]}"


def fill_template(mapped, unmapped):
    """Fill map_template.html with the events and settings; return the finished page as text."""
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        page = f.read()
    return fill(page, {
        "__EVENTS_JSON__": to_js(pack(mapped)),
        "__UNMAPPED_JSON__": to_js(pack(unmapped)),
        "__VERSION__": API_VERSION,
        "__CANDIDATES__": ", ".join(CANDIDATE_VERSIONS),
        "__PERIOD__": PERIOD,
        "__AREA__": AREA_NAME,
        "__BOUNDS__": json.dumps(BOUNDS),
        "__HEAT_MAX__": str(HEAT_MAX),
        # one country on screen: same heat ceiling as the Nigeria-only map
        "__COUNTRY_HEAT_MAX__": str(AREAS["nigeria"]["heat_max"]),
        "__BUILT__": date.today().isoformat(),
        "__BUILT_LONG__": f"{date.today().day} {date.today():%B %Y}",
        "__SHOWN_PERIOD__": shown_period(mapped + unmapped),
    })


def load_all():
    """Return (map-ready events, events too vague to plot) from the clean table."""
    if not os.path.exists(DB_PATH):
        sys.exit("No database yet. Run save_events.py and clean_events.py first.")

    db = sqlite3.connect(DB_PATH)
    try:
        mapped = load(db, 1)
        unmapped = load(db, 0)
    except sqlite3.OperationalError:
        sys.exit("No clean_events table yet. Run clean_events.py first.")
    finally:
        db.close()

    if not mapped:
        sys.exit("No map-ready events. Run clean_events.py first.")
    return mapped, unmapped


def main():
    mapped, unmapped = load_all()
    page = fill_template(mapped, unmapped)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"Map built: {len(mapped)} events on the map, {len(unmapped)} listed separately.")
    print(f"Saved to {OUTPUT_PATH}")

    if "--no-open" not in sys.argv:
        webbrowser.open(Path(OUTPUT_PATH).as_uri())


if __name__ == "__main__":
    main()

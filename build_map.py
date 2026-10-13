"""
Stage 5: build an interactive map from the clean events (Stage 4).

Reads the clean_events table (no API requests), fills in map_template.html
and writes data/<area>_<years>_map.html. Open that file in your browser.

Python does the data; the template (HTML + JavaScript with Leaflet) does the drawing.
Uses only the Python standard library.
"""

import json
import os
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
    """JSON that is safe to paste inside a <script> tag."""
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def shown_period(events):
    """The years the map actually covers, e.g. "2020-2026" once preliminary 2026 data is in.
    (PERIOD in settings.py is only the stable release's years.)"""
    years = sorted({e["date_start"][:4] for e in events})
    return years[0] if years[0] == years[-1] else f"{years[0]}-{years[-1]}"


def fill_template(mapped, unmapped):
    """Fill map_template.html with the events and settings; return the finished page as text."""
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        page = f.read()
    page = (page.replace("__EVENTS_JSON__", to_js(pack(mapped)))
                .replace("__UNMAPPED_JSON__", to_js(pack(unmapped)))
                .replace("__VERSION__", API_VERSION)
                .replace("__CANDIDATES__", ", ".join(CANDIDATE_VERSIONS))
                .replace("__PERIOD__", PERIOD)
                .replace("__AREA__", AREA_NAME)
                .replace("__BOUNDS__", json.dumps(BOUNDS))
                .replace("__HEAT_MAX__", str(HEAT_MAX))
                # one country on screen: same heat ceiling as the Nigeria-only map
                .replace("__COUNTRY_HEAT_MAX__", str(AREAS["nigeria"]["heat_max"]))
                .replace("__BUILT__", date.today().isoformat())
                .replace("__BUILT_LONG__", f"{date.today().day} {date.today():%B %Y}")
                .replace("__SHOWN_PERIOD__", shown_period(mapped + unmapped)))
    return page


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

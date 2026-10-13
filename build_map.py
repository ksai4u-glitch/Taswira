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

from settings import API_VERSION, AREA_NAME, BOUNDS, CANDIDATE_VERSIONS, FILE_STEM, HEAT_MAX, PERIOD

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "taswira.db")
TEMPLATE_PATH = os.path.join(HERE, "map_template.html")
OUTPUT_PATH = os.path.join(HERE, "data", f"{FILE_STEM}_map.html")

# Only the fields the map page uses, to keep the file small
MAP_FIELDS = [
    "date_start", "date_end", "country", "state", "place", "latitude", "longitude",
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


def to_js(data):
    """JSON that is safe to paste inside a <script> tag."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def fill_template(mapped, unmapped):
    """Fill map_template.html with the events and settings; return the finished page as text."""
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        page = f.read()
    page = (page.replace("__EVENTS_JSON__", to_js(mapped))
                .replace("__UNMAPPED_JSON__", to_js(unmapped))
                .replace("__VERSION__", API_VERSION)
                .replace("__CANDIDATES__", ", ".join(CANDIDATE_VERSIONS))
                .replace("__PERIOD__", PERIOD)
                .replace("__AREA__", AREA_NAME)
                .replace("__BOUNDS__", json.dumps(BOUNDS))
                .replace("__HEAT_MAX__", str(HEAT_MAX))
                .replace("__BUILT__", date.today().isoformat()))
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

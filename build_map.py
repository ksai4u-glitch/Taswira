"""
Stage 5: build an interactive map of Nigeria from the clean events (Stage 4).

Reads the clean_events table (no API requests), fills in map_template.html
and writes data/<country>_<years>_map.html. Open that file in your browser.

Python does the data; the template (HTML + JavaScript with Leaflet) does the drawing.
Uses only the Python standard library.
"""

import json
import os
import sqlite3
import sys
import webbrowser
from pathlib import Path

from settings import API_VERSION, COUNTRY_NAME, FILE_STEM, PERIOD

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "taswira.db")
TEMPLATE_PATH = os.path.join(HERE, "map_template.html")
OUTPUT_PATH = os.path.join(HERE, "data", f"{FILE_STEM}_map.html")

# Only the fields the map page uses, to keep the file small
MAP_FIELDS = [
    "date_start", "date_end", "state", "place", "latitude", "longitude",
    "violence_label", "side_a", "side_b", "deaths_best", "deaths_low", "deaths_high",
]


def load(db, map_ready):
    """Return clean events as a list of dicts, either map-ready (1) or not (0)."""
    db.row_factory = sqlite3.Row
    rows = db.execute(
        f"SELECT {', '.join(MAP_FIELDS)} FROM clean_events "
        "WHERE dataset_version = ? AND map_ready = ? ORDER BY date_start",
        (API_VERSION, map_ready),
    ).fetchall()
    return [dict(row) for row in rows]


def to_js(data):
    """JSON that is safe to paste inside a <script> tag."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def main():
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
        sys.exit(f"No map-ready GED {API_VERSION} events. Run clean_events.py first.")

    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        page = f.read()
    page = (page.replace("__EVENTS_JSON__", to_js(mapped))
                .replace("__UNMAPPED_JSON__", to_js(unmapped))
                .replace("__VERSION__", API_VERSION)
                .replace("__PERIOD__", PERIOD)
                .replace("__COUNTRY__", COUNTRY_NAME))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"Map built: {len(mapped)} events on the map, {len(unmapped)} listed separately.")
    print(f"Saved to {OUTPUT_PATH}")

    if "--no-open" not in sys.argv:
        webbrowser.open(Path(OUTPUT_PATH).as_uri())


if __name__ == "__main__":
    main()

"""
Stage 4: turn the raw UCDP events saved in Stage 3 into a clean, map-ready table.

Reads data/taswira.db (no API requests at all) and writes:
- a `clean_events` table in the same database, rebuilt on every run
- data/<area>_<years>_clean.csv, which you can open in Excel or VS Code

What "clean" means here:
- keep only the ~20 fields we need, with clear names and proper types
- dates as plain YYYY-MM-DD, violence type as a readable label
- "Borno state" -> "Borno"
- a `map_ready` flag: 1 only if the location is precise enough to plot (see below)

Uses only the Python standard library.
"""

import csv
import os
import sqlite3
import sys

from settings import API_VERSION, AREA_NAME, BOUNDS, COUNTRIES, END_DATE, FILE_STEM, PERIOD, START_DATE

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "taswira.db")
CSV_PATH = os.path.join(DATA_DIR, f"{FILE_STEM}_clean.csv")

VIOLENCE_TYPES = {1: "state-based", 2: "non-state", 3: "one-sided"}

# where_prec: how precisely UCDP knows the location.
#   1 exact place, 2 within ~25 km, 3 only the district (LGA in Nigeria), 4 only the province/state,
#   5 along a road/river/border, 6 only the country, 7 international waters/airspace.
# 4 and 6 are placed at the CENTRE of the state or country, which would create
# fake hotspots on a map, so only 1-3 count as map-ready.
MAP_READY_PRECISION = (1, 2, 3)

# BOUNDS (from settings.py) is a rough box around the area, to catch obviously wrong coordinates
(LAT_MIN, LON_MIN), (LAT_MAX, LON_MAX) = BOUNDS

CLEAN_COLUMNS = [
    "id", "dataset_version",
    "date_start", "date_end", "date_prec",
    "country", "state", "lga", "place", "latitude", "longitude", "where_prec", "map_ready",
    "violence_type", "violence_label", "side_a", "side_b", "conflict_name",
    "deaths_best", "deaths_low", "deaths_high", "deaths_civilians",
    "event_clarity",
]


def clean_state(adm_1):
    """'Borno state' -> 'Borno'. Empty or missing -> None."""
    if not adm_1:
        return None
    name = adm_1.strip()
    if name.lower().endswith(" state"):
        name = name[: -len(" state")]
    return name


def clean_event(raw):
    """Turn one raw database row (a dict) into one clean dict."""
    lat = float(raw["latitude"])
    lon = float(raw["longitude"])
    where_prec = int(raw["where_prec"])
    in_area = LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX
    violence_type = int(raw["type_of_violence"])

    return {
        "id": int(raw["id"]),
        "dataset_version": raw["dataset_version"],
        "date_start": str(raw["date_start"])[:10],      # keep only YYYY-MM-DD
        "date_end": str(raw["date_end"])[:10],
        "date_prec": int(raw["date_prec"]),
        "country": raw["country"],
        "state": clean_state(raw["adm_1"]),
        "lga": (raw["adm_2"] or "").strip() or None,
        "place": (raw["where_description"] or "").strip() or None,
        "latitude": lat,
        "longitude": lon,
        "where_prec": where_prec,
        "map_ready": int(where_prec in MAP_READY_PRECISION and in_area),
        "violence_type": violence_type,
        "violence_label": VIOLENCE_TYPES.get(violence_type, "unknown"),
        "side_a": raw["side_a"],
        "side_b": raw["side_b"],
        "conflict_name": raw["conflict_name"],
        "deaths_best": int(raw["best"]),
        "deaths_low": int(raw["low"]),
        "deaths_high": int(raw["high"]),
        "deaths_civilians": int(raw["deaths_civilians"]),
        "event_clarity": int(raw["event_clarity"]),
    }


def main():
    if not os.path.exists(DB_PATH):
        sys.exit("No database yet. Run save_events.py first.")

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row       # lets us read columns by name: row["best"]

    raw_rows = db.execute(
        # Only the area and period in settings.py. The database may also hold other downloads.
        # Like the API, filter on date_end; substr() ignores any time part after the date.
        f"SELECT * FROM events WHERE dataset_version = ? "
        f"AND substr(date_end, 1, 10) BETWEEN ? AND ? "
        f"AND country_id IN ({', '.join('?' for _ in COUNTRIES)}) ORDER BY date_start, id",
        (API_VERSION, START_DATE, END_DATE, *COUNTRIES),
    ).fetchall()
    if not raw_rows:
        sys.exit(f"No GED {API_VERSION} events for {AREA_NAME} {PERIOD} in the database. "
                 "Run save_events.py first.")

    clean = [clean_event(dict(row)) for row in raw_rows]

    # Rebuild the clean table from scratch every run: it is derived data,
    # so the raw `events` table stays the single source of truth.
    db.execute("DROP TABLE IF EXISTS clean_events")
    db.execute(f"CREATE TABLE clean_events ({', '.join(CLEAN_COLUMNS)}, "
               "PRIMARY KEY (id, dataset_version))")
    db.executemany(
        f"INSERT INTO clean_events VALUES ({', '.join('?' for _ in CLEAN_COLUMNS)})",
        [[event[c] for c in CLEAN_COLUMNS] for event in clean],
    )
    db.commit()

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CLEAN_COLUMNS)
        writer.writeheader()
        writer.writerows(clean)

    report(db, len(clean))
    db.close()
    print(f"\nWrote {len(clean)} rows to the clean_events table and {CSV_PATH}")


def report(db, total):
    """Print what cleaning found, so we can decide what to map."""
    print(f"Cleaned {total} events ({AREA_NAME} {PERIOD}, GED {API_VERSION}).\n")

    print("Location precision (where_prec):")
    for prec, count, deaths in db.execute(
        "SELECT where_prec, COUNT(*), SUM(deaths_best) FROM clean_events "
        "GROUP BY where_prec ORDER BY where_prec"
    ):
        tag = "map-ready" if prec in MAP_READY_PRECISION else "NOT map-ready"
        print(f"  {prec}: {count:6} events, {deaths:7} deaths  ({tag})")

    ready, ready_deaths = db.execute(
        "SELECT COUNT(*), SUM(deaths_best) FROM clean_events WHERE map_ready = 1"
    ).fetchone()
    all_deaths = db.execute("SELECT SUM(deaths_best) FROM clean_events").fetchone()[0]
    print(f"\nMap-ready: {ready} of {total} events ({ready / total:.0%}), "
          f"{ready_deaths or 0} of {all_deaths} deaths.")

    outside = db.execute(
        "SELECT COUNT(*) FROM clean_events WHERE where_prec IN (1, 2, 3) AND map_ready = 0"
    ).fetchone()[0]
    if outside:
        print(f"WARNING: {outside} precise events have coordinates outside the {AREA_NAME} box.")

    print("\nBy type of violence:")
    for label, count, deaths in db.execute(
        "SELECT violence_label, COUNT(*), SUM(deaths_best) FROM clean_events "
        "GROUP BY violence_label ORDER BY COUNT(*) DESC"
    ):
        print(f"  {label:12} {count:6} events, {deaths:7} deaths")

    if len(COUNTRIES) > 1:
        print("\nTop 10 countries by deaths:")
        for country, count, deaths in db.execute(
            "SELECT country, COUNT(*), SUM(deaths_best) FROM clean_events "
            "GROUP BY country ORDER BY SUM(deaths_best) DESC LIMIT 10"
        ):
            print(f"  {country:32} {count:6} events, {deaths:7} deaths")


if __name__ == "__main__":
    main()

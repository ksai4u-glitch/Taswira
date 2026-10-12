"""
Stage 3: save the events (settings.py says which) to a local SQLite database,
so later stages (cleaning, mapping) never need to call the API again.

- Fetches with fetch_all() from Stage 2, but ONLY if this exact query
  has not been saved before. Run with --refresh to fetch again anyway.
- Keeps all 49 fields of every event, exactly as UCDP sent them.
- Saving the same event twice updates it instead of duplicating it.

Database: data/taswira.db (ignored by git). Uses only the standard library.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

from fetch_all import PARAMS, fetch_all
from fetch_nigeria import load_token
from settings import API_VERSION

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "taswira.db")

# A readable label for this query, e.g. "Country=475&StartDate=2024-01-01&EndDate=2024-12-31"
QUERY = f"Country={PARAMS['Country']}&StartDate={PARAMS['StartDate']}&EndDate={PARAMS['EndDate']}"


def connect():
    """Open the database (creating the data/ folder and the log table if needed)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    # One row per successful download: which version, which filters, when, how many.
    db.execute("""
        CREATE TABLE IF NOT EXISTS fetch_log (
            dataset_version TEXT,
            query           TEXT,
            fetched_at      TEXT,
            event_count     INTEGER
        )
    """)
    return db


def already_saved(db):
    """Return the log row if this version + query was saved before, else None."""
    return db.execute(
        "SELECT fetched_at, event_count FROM fetch_log "
        "WHERE dataset_version = ? AND query = ? ORDER BY fetched_at DESC LIMIT 1",
        (API_VERSION, QUERY),
    ).fetchone()


def save(db, events):
    """Create the events table from the fields UCDP sends, then insert or update every event."""
    fields = list(events[0].keys())          # the 49 UCDP field names
    columns = ["dataset_version"] + fields
    column_list = ", ".join(f'"{c}"' for c in columns)   # quoted, e.g. "id", "best"

    # The same event id can appear in different dataset versions (e.g. 26.1 and a
    # monthly Candidate), so an event is identified by (id, dataset_version).
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS events (
            {column_list},
            PRIMARY KEY (id, dataset_version)
        )
    """)

    placeholders = ", ".join("?" for _ in columns)
    rows = []
    for event in events:
        values = [API_VERSION]
        for field in fields:
            value = event.get(field)
            # SQLite stores numbers and text; anything else (lists, dicts) is saved as JSON text
            if isinstance(value, (list, dict)):
                value = json.dumps(value)
            values.append(value)
        rows.append(values)

    # INSERT OR REPLACE: a new id is added, an existing one is overwritten, never duplicated.
    db.executemany(
        f"INSERT OR REPLACE INTO events ({column_list}) VALUES ({placeholders})",
        rows,
    )
    db.execute(
        "INSERT INTO fetch_log VALUES (?, ?, ?, ?)",
        (API_VERSION, QUERY, datetime.now(timezone.utc).isoformat(timespec="seconds"), len(events)),
    )
    db.commit()


def summary(db):
    """Prove the data is there by asking the database a couple of questions."""
    total = db.execute(
        "SELECT COUNT(*), SUM(best) FROM events WHERE dataset_version = ?", (API_VERSION,)
    ).fetchone()
    print(f"\nDatabase now holds {total[0]} events for GED {API_VERSION} "
          f"({total[1]} deaths, best estimate).")

    print("\nTop 5 countries by number of events:")
    for state, count, deaths in db.execute(
        "SELECT country, COUNT(*), SUM(best) FROM events WHERE dataset_version = ? "
        "GROUP BY country ORDER BY COUNT(*) DESC LIMIT 5",
        (API_VERSION,),
    ):
        print(f"  {state or '(unknown)'}: {count} events, {deaths} deaths")


def main():
    refresh = "--refresh" in sys.argv
    db = connect()

    previous = already_saved(db)
    if previous and not refresh:
        fetched_at, count = previous
        print(f"Already saved {count} events for GED {API_VERSION} ({QUERY}) on {fetched_at}.")
        print("No API requests made. Run with --refresh to download again.")
    else:
        events, total_count, requests_made = fetch_all(load_token())
        if len(events) != total_count:
            sys.exit(f"Not saving: collected {len(events)} events but the API said {total_count}.")
        save(db, events)
        print(f"\nSaved {len(events)} events to {DB_PATH} using {requests_made} requests.")

    summary(db)
    db.close()


if __name__ == "__main__":
    main()

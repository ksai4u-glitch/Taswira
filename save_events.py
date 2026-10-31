"""
Stage 3: save the events (settings.py says which) to a local SQLite database,
so later stages (cleaning, mapping) never need to call the API again.

- Downloads the stable release and then each preliminary Candidate release
  in settings.py, each tagged with its dataset_version.
- Fetches with fetch_all() from Stage 2, but ONLY if that version + query
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

from fetch_all import fetch_all, params_for
from fetch_nigeria import load_token
from settings import API_VERSION, CANDIDATE_VERSIONS

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "taswira.db")

VERSIONS = [API_VERSION] + CANDIDATE_VERSIONS   # stable first, then preliminary


def query_label(version):
    """A readable label for one version's query, e.g. "Country=475&StartDate=2024-01-01&EndDate=2024-12-31"."""
    return "&".join(f"{k}={v}" for k, v in params_for(version).items() if k != "pagesize")


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


def already_saved(db, version):
    """Return the log row if this version + query was saved before, else None."""
    return db.execute(
        "SELECT fetched_at, event_count FROM fetch_log "
        "WHERE dataset_version = ? AND query = ? ORDER BY fetched_at DESC LIMIT 1",
        (version, query_label(version)),
    ).fetchone()


def quote_name(name):
    """A field name as a quoted SQL identifier. The names come from the API's JSON, so a
    double quote inside one is doubled rather than allowed to end the identifier."""
    return '"' + str(name).replace('"', '""') + '"'


def incomplete(events, total_count):
    """Why a download should not be saved, or None if it is complete.

    Matching the count is not enough: if pages shifted while we were paging, one
    event can arrive twice and another not at all, and the count would still match."""
    if len(events) != total_count:
        return f"collected {len(events)} events but the API said {total_count}"
    unique = len({e.get("id") for e in events})
    if unique != total_count:
        return f"collected {total_count} events but only {unique} different ids (pages shifted while downloading?)"
    return None


def save(db, events, version):
    """Create the events table from the fields UCDP sends, then insert or update every event."""
    fields = list(events[0].keys())          # the 49 UCDP field names
    existing = [row[1] for row in db.execute("PRAGMA table_info(events)")]
    if existing:
        # The table already exists: if a release sends a field the table doesn't have, skip it
        extra = [f for f in fields if f not in existing]
        if extra:
            print(f"  Note: GED {version} has fields the table lacks, not saved: {', '.join(extra)}")
        fields = [f for f in fields if f in existing]
    columns = ["dataset_version"] + fields
    column_list = ", ".join(quote_name(c) for c in columns)   # quoted, e.g. "id", "best"

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
        values = [version]
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
    db.commit()


def log_fetch(db, version, count):
    """Remember that this version + query was downloaded, so the next run can skip it."""
    db.execute(
        "INSERT INTO fetch_log VALUES (?, ?, ?, ?)",
        (version, query_label(version), datetime.now(timezone.utc).isoformat(timespec="seconds"), count),
    )
    db.commit()


def summary(db):
    """Prove the data is there by asking the database a couple of questions."""
    print("\nDatabase now holds:")
    for version in VERSIONS:
        count, deaths = db.execute(
            "SELECT COUNT(*), SUM(best) FROM events WHERE dataset_version = ?", (version,)
        ).fetchone()
        tag = "stable" if version == API_VERSION else "Candidate, preliminary"
        print(f"  GED {version:12} {count:6} events, {deaths or 0:7} deaths  ({tag})")

    print(f"\nTop 5 countries by number of events (GED {API_VERSION}):")
    for state, count, deaths in db.execute(
        "SELECT country, COUNT(*), SUM(best) FROM events WHERE dataset_version = ? "
        "GROUP BY country ORDER BY COUNT(*) DESC LIMIT 5",
        (API_VERSION,),
    ):
        print(f"  {state or '(unknown)'}: {count} events, {deaths} deaths")


def main():
    refresh = "--refresh" in sys.argv
    db = connect()
    token = None

    for version in VERSIONS:
        previous = already_saved(db, version)
        if previous and not refresh:
            fetched_at, count = previous
            print(f"GED {version}: already saved {count} events on {fetched_at}. No API requests made.")
            continue

        token = token or load_token()
        print(f"GED {version}: downloading...")
        events, total_count, requests_made = fetch_all(token, version)
        problem = incomplete(events, total_count)
        if problem:
            sys.exit(f"Not saving: {problem}. Run it again later.")
        if events:
            save(db, events, version)
        log_fetch(db, version, len(events))
        print(f"GED {version}: saved {len(events)} events using {requests_made} requests.\n")

    if not refresh:
        print("Run with --refresh to download everything again.")

    summary(db)
    db.close()


if __name__ == "__main__":
    main()

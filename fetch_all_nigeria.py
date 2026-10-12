"""
Stage 2: fetch EVERY page of Nigeria 2024 events from the UCDP GED API,
safely and within the daily request limit.

How paging works: the API returns one page at a time. Each page includes
a NextPageUrl pointing to the next page; on the last page it is empty.
We simply follow those links until there are none left.

Uses only the Python standard library. Reuses load_token() from Stage 1.
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from fetch_nigeria import load_token

# --- Settings -------------------------------------------------------------
API_VERSION = "26.1"
BASE_URL = f"https://ucdpapi.pcr.uu.se/api/gedevents/{API_VERSION}"

PARAMS = {
    "Country": 475,            # Nigeria
    "StartDate": "2024-01-01",
    "EndDate": "2024-12-31",
    "pagesize": 100,           # bigger pages = fewer requests (502 events -> 6 requests)
}

# Safety limits
MAX_REQUESTS = 20       # hard cap for one run; far below the 5,000/day limit
PAUSE_SECONDS = 1       # wait between requests, to be polite to the server


def get_json(url, token):
    """Send one GET request and return the parsed JSON. Stops the script on any error."""
    request = urllib.request.Request(url, headers={"x-ucdp-access-token": token})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP error {e.code}: {e.reason} (url: {url})")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach the API: {e.reason}")


def fetch_all(token):
    """Follow NextPageUrl from page to page and return every event in one list."""
    url = BASE_URL + "?" + urllib.parse.urlencode(PARAMS)
    events = []
    requests_made = 0
    total_count = None

    while url:
        if requests_made >= MAX_REQUESTS:
            sys.exit(f"Stopped: reached MAX_REQUESTS ({MAX_REQUESTS}) before the last page. "
                     "Raise it only if you expected this many pages.")

        if requests_made > 0:
            time.sleep(PAUSE_SECONDS)

        data = get_json(url, token)
        requests_made += 1

        if total_count is None:
            total_count = data["TotalCount"]
            print(f"API reports {total_count} events across {data['TotalPages']} pages.")

        page_events = data.get("Result", [])
        events.extend(page_events)
        print(f"  request {requests_made}: got {len(page_events)} events "
              f"(running total {len(events)})")

        url = data.get("NextPageUrl") or None   # empty on the last page -> loop stops

    return events, total_count, requests_made


def main():
    token = load_token()
    events, total_count, requests_made = fetch_all(token)

    print(f"\nDone in {requests_made} requests.")
    print(f"Collected {len(events)} events; API said {total_count}.")
    if len(events) == total_count:
        print("Counts match.")
    else:
        print("WARNING: counts do not match. Something was missed or duplicated.")

    if not events:
        return

    # Quick sanity checks on what we collected
    ids = [e["id"] for e in events]
    print(f"Unique event ids: {len(set(ids))}")

    dates = sorted(e["date_start"] for e in events)
    print(f"Date range: {dates[0]} to {dates[-1]}")

    total_deaths = sum(e["best"] for e in events)
    print(f"Total deaths (best estimate): {total_deaths}")


if __name__ == "__main__":
    main()

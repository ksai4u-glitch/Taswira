"""
Stage 2: fetch EVERY page of events from the UCDP GED API (area and dates in settings.py),
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
from settings import API_VERSION, COUNTRIES, END_DATE, MAX_REQUESTS, PAGE_SIZE, START_DATE

# --- Settings (the values themselves live in settings.py) -------------------
BASE_URL = f"https://ucdpapi.pcr.uu.se/api/gedevents/{API_VERSION}"

PARAMS = {
    "Country": ",".join(str(c) for c in COUNTRIES),   # all codes, used as the saved-query label
    "StartDate": START_DATE,
    "EndDate": END_DATE,
    "pagesize": PAGE_SIZE,
}

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
    """Fetch every page for every country in settings.py and return all events in one list.

    The API seems to ignore all but the first few codes in a comma-separated
    Country list (an all-Africa query only returned the first 7 codes), so we ask
    for one country at a time and follow NextPageUrl within each country.
    """
    events = []
    requests_made = 0
    total_count = 0

    for position, country in enumerate(COUNTRIES):
        params = dict(PARAMS, Country=country)
        url = BASE_URL + "?" + urllib.parse.urlencode(params)
        first_page = True

        while url:
            if requests_made >= MAX_REQUESTS:
                sys.exit(f"Stopped: reached MAX_REQUESTS ({MAX_REQUESTS}) before the last page. "
                         "Raise it only if you expected this many pages.")

            if requests_made > 0:
                time.sleep(PAUSE_SECONDS)

            data = get_json(url, token)
            requests_made += 1
            page_events = data.get("Result", [])
            events.extend(page_events)

            if first_page:
                first_page = False
                total_count += data["TotalCount"]
                print(f"  country {country}: {data['TotalCount']} events, {data['TotalPages']} pages")
                # Stop early, rather than halfway through a download that can't finish:
                # this country's remaining pages + at least 1 request per country still to go
                countries_left = len(COUNTRIES) - position - 1
                needed = requests_made + max(data["TotalPages"] - 1, 0) + countries_left
                if needed > MAX_REQUESTS:
                    sys.exit(f"Stopped: this needs at least {needed} requests but MAX_REQUESTS is "
                             f"{MAX_REQUESTS}. Raise it in settings.py if that's OK.")
            else:
                print(f"    request {requests_made}: got {len(page_events)} more")

            url = data.get("NextPageUrl") or None   # empty on the last page -> next country

    print(f"API reports {total_count} events in total across {len(COUNTRIES)} countries.")
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

"""
Stage 2: fetch EVERY page of events from the UCDP GED API (area and dates in settings.py),
safely and within the daily request limit.

How paging works: the API returns one page at a time. Each page includes
a NextPageUrl pointing to the next page; on the last page it is empty.
We simply follow those links until there are none left.

Requests go through ucdp_api.py, which retries timeouts and HTTP 429/5xx a
couple of times and checks that every page still has the expected shape.

Uses only the Python standard library. Reuses load_token() from Stage 1.
"""

import sys
import time
import urllib.parse

import ucdp_api
from fetch_nigeria import is_ucdp_url, load_token
from settings import API_VERSION, COUNTRIES, END_DATE, MAX_REQUESTS, PAGE_SIZE, START_DATE

# --- Settings (the values themselves live in settings.py) -------------------
API_URL = ucdp_api.API_URL   # + version, e.g. "26.1"


def params_for(version):
    """The filters for one dataset version.

    The stable release is filtered to START_DATE-END_DATE. A Candidate release only
    holds recent months anyway, so it gets no date filter.
    """
    params = {"Country": ",".join(str(c) for c in COUNTRIES)}   # all codes, used as the saved-query label
    if version == API_VERSION:
        params.update(StartDate=START_DATE, EndDate=END_DATE)
    params["pagesize"] = PAGE_SIZE
    return params


PAUSE_SECONDS = 1       # wait between requests, to be polite to the server


def get_json(url, token):
    """Fetch one checked page (with retries, see ucdp_api.py). Stops the script on any error."""
    try:
        return ucdp_api.get_page(url, token)
    except ucdp_api.HTTPStatusError as e:
        hint = " Is that dataset version in settings.py published yet?" if e.code == 404 else ""
        sys.exit(f"{e}.{hint}")
    except ucdp_api.UCDPError as e:
        sys.exit(f"Download stopped: {e}")


def fetch_all(token, version=API_VERSION):
    """Fetch every page for every country in settings.py from one dataset version
    and return all events in one list.

    The API seems to ignore all but the first few codes in a comma-separated
    Country list (an all-Africa query only returned the first 7 codes), so we ask
    for one country at a time and follow NextPageUrl within each country.
    """
    events = []
    requests_made = 0          # attempts for this version, retries included
    total_count = 0

    for position, country in enumerate(COUNTRIES):
        params = dict(params_for(version), Country=country)
        url = API_URL + version + "?" + urllib.parse.urlencode(params)
        first_page = True

        while url:
            if requests_made >= MAX_REQUESTS:
                sys.exit(f"Stopped: reached MAX_REQUESTS ({MAX_REQUESTS}) before the last page. "
                         "Raise it only if you expected this many pages.")

            if requests_made > 0:
                time.sleep(PAUSE_SECONDS)

            before = ucdp_api.requests_made
            data = get_json(url, token)
            requests_made += ucdp_api.requests_made - before   # 1, or more after retries
            page_events = data["Result"]
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
            if url and not is_ucdp_url(url):
                # The token goes with every request, so only ever follow links back to the API
                sys.exit(f"Stopped: NextPageUrl does not point to the UCDP API over https ({url}).")

    print(f"GED {version}: API reports {total_count} events in total across {len(COUNTRIES)} countries.")
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

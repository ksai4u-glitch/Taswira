"""
Stage 1: make ONE authenticated request to the UCDP GED API
for Nigeria in 2024 and print a quick look at what comes back.

Uses only the Python standard library, so there is nothing to install.
Each run costs exactly 1 of your 5,000 daily requests.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# --- Settings -------------------------------------------------------------
API_VERSION = "26.1"  # stable yearly GED release
BASE_URL = f"https://ucdpapi.pcr.uu.se/api/gedevents/{API_VERSION}"

PARAMS = {
    "Country": 475,            # Nigeria (Gleditsch-Ward code)
    "StartDate": "2024-01-01",
    "EndDate": "2024-12-31",
    "pagesize": 5,             # small page: we only want a peek at the data
}

FIELDS_TO_SHOW = ["date_start", "latitude", "longitude", "best", "type_of_violence"]

# UCDP's three violence types, so the output is readable
VIOLENCE_TYPES = {1: "state-based", 2: "non-state", 3: "one-sided"}


def load_token():
    """Read UCDP_TOKEN from the environment, falling back to a local .env file."""
    token = os.environ.get("UCDP_TOKEN")
    if token:
        return token.strip()

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("UCDP_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")

    sys.exit("No token found. Set UCDP_TOKEN or create a .env file (see .env.example).")


def fetch(token):
    """Send one GET request and return the parsed JSON."""
    url = BASE_URL + "?" + urllib.parse.urlencode(PARAMS)
    print(f"Requesting: {url}\n")

    request = urllib.request.Request(url, headers={"x-ucdp-access-token": token})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        # 401/403 usually means a bad or missing token
        sys.exit(f"HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach the API: {e.reason}")


def main():
    token = load_token()
    data = fetch(token)

    print(f"TotalCount: {data.get('TotalCount')}  (events matching the filters)")
    print(f"TotalPages: {data.get('TotalPages')}  (at pagesize={PARAMS['pagesize']})")
    print(f"Top-level keys: {list(data.keys())}\n")

    events = data.get("Result", [])
    print(f"Sample of {len(events)} events:")
    for event in events:
        row = {field: event.get(field) for field in FIELDS_TO_SHOW}
        row["type_of_violence"] = VIOLENCE_TYPES.get(row["type_of_violence"], row["type_of_violence"])
        print("  ", row)

    if events:
        print(f"\nEvery field available on an event ({len(events[0])}):")
        print("  ", ", ".join(events[0].keys()))


if __name__ == "__main__":
    main()

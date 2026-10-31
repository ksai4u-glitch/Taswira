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


# The token may only ever be sent to the UCDP API over HTTPS.
UCDP_HOST = "ucdpapi.pcr.uu.se"


def is_ucdp_url(url):
    """True only for https://ucdpapi.pcr.uu.se/... (the one place the token may go)."""
    try:
        parts = urllib.parse.urlsplit(url or "")
        port = parts.port
    except ValueError:
        return False
    return parts.scheme == "https" and parts.hostname == UCDP_HOST and port in (None, 443) \
        and not parts.username and not parts.password


class _StayOnUcdp(urllib.request.HTTPRedirectHandler):
    """urllib copies every header, the token included, to wherever a redirect points.
    Refuse any redirect that leaves the UCDP API, so the token cannot follow it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_ucdp_url(newurl):
            raise urllib.error.HTTPError(
                req.full_url, code, f"refused a redirect away from {UCDP_HOST} (the token is not sent there)",
                headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_StayOnUcdp)


def open_ucdp(url, token, timeout=30):
    """Open a UCDP API URL with the token header. Refuses any other address."""
    if not is_ucdp_url(url):
        raise ValueError(f"not a UCDP API address, so the token is not sent: {url}")
    request = urllib.request.Request(url, headers={"x-ucdp-access-token": token})
    return _OPENER.open(request, timeout=timeout)


def fetch(token):
    """Send one GET request and return the parsed JSON."""
    url = BASE_URL + "?" + urllib.parse.urlencode(PARAMS)
    print(f"Requesting: {url}\n")

    try:
        with open_ucdp(url, token) as response:
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

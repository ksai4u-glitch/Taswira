"""
Shared code for talking to the UCDP GED API, used by fetch_all.py and
update_candidates.py.

- get_page() sends one GET, retries timeouts, dropped connections and
  HTTP 429/5xx a few times with a growing pause, and checks that the reply
  still looks like a GED page (Result, TotalCount, TotalPages).
- Every attempt, including failed ones and retries, counts towards
  MAX_REQUESTS_PER_RUN in settings.py, because UCDP counts them all against
  the 5,000 requests a day.
- Problems are raised as UCDPError with a readable message. The token is sent
  only in the request header and never appears in a message.

Uses only the Python standard library.
"""

import http.client
import json
import time
import urllib.error

from fetch_nigeria import is_ucdp_url, open_ucdp
from settings import MAX_REQUESTS_PER_RUN

API_URL = "https://ucdpapi.pcr.uu.se/api/gedevents/"   # + version, e.g. "26.1"

TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 3                 # 1 try + 2 retries
BACKOFF_SECONDS = (5, 20)        # pause before the 1st and 2nd retry
MAX_RETRY_AFTER = 120            # a longer Retry-After means "come back tomorrow": give up
RETRY_STATUSES = {429, 500, 502, 503, 504}

requests_made = 0                # attempts made by this process so far


class UCDPError(Exception):
    """The API could not be used; the message says why."""


class AuthError(UCDPError):
    """The token was refused (HTTP 401/403)."""


class HTTPStatusError(UCDPError):
    """The API answered with an HTTP error that is not worth retrying (e.g. 404)."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _retry_after(error):
    """Seconds asked for by a Retry-After header, or None if missing or not a number."""
    value = error.headers.get("Retry-After") if error.headers else None
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def get_json(url, token):
    """GET url with the token header and return the parsed JSON, retrying transient failures."""
    global requests_made
    if not is_ucdp_url(url):
        # never send the token anywhere but the UCDP API over https
        raise UCDPError(f"not a UCDP API address, so the token is not sent: {url}")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if requests_made >= MAX_REQUESTS_PER_RUN:
            raise UCDPError(f"stopped at MAX_REQUESTS_PER_RUN ({MAX_REQUESTS_PER_RUN}) requests in this run, "
                            "to stay well inside UCDP's 5,000 a day")
        requests_made += 1
        wait = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS)) - 1]

        try:
            # open_ucdp also refuses redirects that leave the UCDP API
            with open_ucdp(url, token, timeout=TIMEOUT_SECONDS) as response:
                body = response.read()
            return json.loads(body)
        except urllib.error.HTTPError as e:
            e.close()
            if e.code in (401, 403):
                raise AuthError(f"HTTP {e.code}: the token was refused. Check UCDP_TOKEN.") from None
            if e.code not in RETRY_STATUSES:
                raise HTTPStatusError(e.code, f"HTTP {e.code} {e.reason} (url: {url})") from None
            asked = _retry_after(e)
            if asked is not None:
                if asked > MAX_RETRY_AFTER:
                    raise UCDPError(f"HTTP {e.code}: UCDP asks to wait {asked} seconds; the daily "
                                    "request limit may be used up. Try again after midnight UTC.") from None
                wait = asked
            problem = f"HTTP {e.code} {e.reason}"
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
            problem = f"no usable answer ({getattr(e, 'reason', None) or e.__class__.__name__})"
        except (ValueError, UnicodeDecodeError):     # json.JSONDecodeError is a ValueError
            problem = "the answer was not valid JSON (cut off, or an error page)"

        if attempt == MAX_ATTEMPTS:
            raise UCDPError(f"{problem} after {MAX_ATTEMPTS} attempts (url: {url})")
        print(f"  {problem}; retrying in {wait} s (attempt {attempt + 1} of {MAX_ATTEMPTS})")
        time.sleep(wait)


def check_page(data, url):
    """Raise UCDPError unless data has the shape of a GED events page."""
    def bad(why):
        return UCDPError(f"unexpected answer from UCDP ({why}); has the API changed? (url: {url})")

    if not isinstance(data, dict):
        raise bad(f"expected a JSON object, got {type(data).__name__}")
    missing = [k for k in ("Result", "TotalCount", "TotalPages") if k not in data]
    if missing:
        raise bad("missing " + ", ".join(missing))
    for key in ("TotalCount", "TotalPages"):
        value = data[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise bad(f"{key} is {value!r}")
    if not isinstance(data["Result"], list):
        raise bad("Result is not a list")
    if not all(isinstance(e, dict) and "id" in e for e in data["Result"]):
        raise bad("an event without an id")
    next_url = data.get("NextPageUrl")
    if next_url and not (isinstance(next_url, str) and is_ucdp_url(next_url)):
        # never send the token anywhere but the UCDP API
        raise bad("NextPageUrl does not point at the UCDP API")
    return data


def get_page(url, token):
    """One checked page of GED events."""
    return check_page(get_json(url, token), url)

"""
Check whether UCDP has published a newer monthly GED Candidate release than
the last one in settings.py, and if so add it to CANDIDATE_VERSIONS.

Monthly versions count up: 26.0.8 -> 26.0.9 -> ... -> 26.0.12 -> 27.0.1.
Each check costs 1 API request (pagesize=1), plus 1 more per new version found.

Run by the weekly GitHub Actions workflow (.github/workflows/update.yml),
but you can also run it by hand. Uses only the Python standard library.
"""

import os
import re
import sys
import urllib.error
import urllib.request

from fetch_nigeria import load_token, open_ucdp
from settings import API_VERSION, CANDIDATE_VERSIONS
from switch_stable import stable_notice

API_URL = "https://ucdpapi.pcr.uu.se/api/gedevents/"
SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.py")
MAX_NEW = 3     # never add more than this many versions in one run


def next_version(version):
    """The monthly release after this one: "26.0.8" -> "26.0.9", "26.0.12" -> "27.0.1"."""
    year, zero, month = version.split(".")
    if int(month) < 12:
        return f"{year}.0.{int(month) + 1}"
    return f"{int(year) + 1}.0.1"


def last_monthly(versions):
    """The newest monthly version (YY.0.M) in the list; quarterly ones look different."""
    monthly = [v for v in versions if re.fullmatch(r"\d+\.0\.\d+", v)]
    if not monthly:
        sys.exit("No monthly Candidate version (like 26.0.8) in CANDIDATE_VERSIONS to count up from.")
    return max(monthly, key=lambda v: tuple(int(p) for p in v.split(".")))


def is_published(version, token):
    """Ask the API for one event from this version. True if it exists, False if not yet."""
    url = f"{API_URL}{version}?pagesize=1&Country=475"
    try:
        with open_ucdp(url, token):
            return True
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            sys.exit(f"HTTP {e.code}: the token was refused. Check the UCDP_TOKEN secret.")
        if 400 <= e.code < 500:
            return False        # 404 or 400: this version isn't published (yet)
        sys.exit(f"HTTP error {e.code} from UCDP; try again later.")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach the API: {e.reason}")


def add_to_settings(new_versions):
    """Rewrite the CANDIDATE_VERSIONS line in settings.py with the new versions appended."""
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        text = f.read()
    updated = CANDIDATE_VERSIONS + new_versions
    line = "CANDIDATE_VERSIONS = [" + ", ".join(f'"{v}"' for v in updated) + "]"
    text, count = re.subn(r"^CANDIDATE_VERSIONS = \[.*?\]", line, text, count=1, flags=re.M | re.S)
    if count != 1:
        sys.exit("Could not find the CANDIDATE_VERSIONS line in settings.py.")
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    token = load_token()
    candidate = next_version(last_monthly(CANDIDATE_VERSIONS))
    new_versions = []
    while len(new_versions) < MAX_NEW and is_published(candidate, token):
        new_versions.append(candidate)
        candidate = next_version(candidate)

    if new_versions:
        add_to_settings(new_versions)
        print(f"New Candidate release(s): {', '.join(new_versions)}. Added to settings.py.")
    else:
        print(f"No new Candidate release yet ({candidate} is not published).")

    notice = stable_notice(API_VERSION, token)  # at most 1 request, only from May of the expected year
    if notice:
        print(("::notice::" if os.environ.get("GITHUB_ACTIONS") else "Notice: ") + notice)

    # Tell the GitHub Actions workflow what happened, so it knows whether to rebuild
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"new_versions={' '.join(new_versions)}\n")


if __name__ == "__main__":
    main()

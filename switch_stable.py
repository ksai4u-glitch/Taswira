"""
Switch settings.py to a new stable yearly UCDP GED release, e.g. 26.1 -> 27.1.

    python switch_stable.py 27.1             # check it exists (1 request), then update settings.py
    python switch_stable.py 27.1 --dry-run   # show the changes, write nothing
    python switch_stable.py 27.1 --no-check  # skip the API check (no token needed)

A stable release "YY.1" covers events up to the end of the year before, so 27.1
covers everything up to 2026-12-31. The script:

- sets API_VERSION to the new version,
- sets END_DATE to the last day of the newly covered year (START_DATE stays),
- drops the Candidate versions in CANDIDATE_VERSIONS whose months the stable
  release now covers (e.g. 26.01.26.06 and 26.0.7 ... 26.0.12 for 27.1),
- prints the commands to run next.

It never downloads events itself; save_events.py does that. Uses only the
Python standard library.
"""

import argparse
import ast
import difflib
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date

API_URL = "https://ucdpapi.pcr.uu.se/api/gedevents/"
SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.py")
NEXT_STABLE_FROM_MONTH = 5   # UCDP publishes the stable release around June; look from May on


# --- Versions ------------------------------------------------------------------

def parse_stable(version):
    """Return the 2-digit release year of a stable version: "27.1" -> 27. Exits if it is not one."""
    match = re.fullmatch(r"(\d{2})\.1", version.strip())
    if not match:
        sys.exit(f"{version!r} does not look like a stable GED release (YY.1, e.g. 27.1).")
    return int(match.group(1))


def covered_year(version):
    """The last year a stable release covers: "27.1" -> 2026."""
    return 2000 + parse_stable(version) - 1


def candidate_year(version):
    """The (last) year of data in a Candidate version, or None if the format is unknown.

    Monthly "26.0.7" -> 2026 (July 2026); quarterly "26.01.26.06" -> 2026 (Jan-June 2026).
    """
    monthly = re.fullmatch(r"(\d{2})\.0\.(\d{1,2})", version)
    if monthly:
        return 2000 + int(monthly.group(1))
    quarterly = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})", version)
    if quarterly:
        return 2000 + int(quarterly.group(3))
    return None


def split_candidates(candidates, new_version):
    """Split CANDIDATE_VERSIONS into (dropped, kept, unknown) for the new stable release.

    Unknown formats are kept (and reported), never dropped silently.
    """
    last = covered_year(new_version)
    dropped, kept, unknown = [], [], []
    for v in candidates:
        year = candidate_year(v)
        if year is None:
            unknown.append(v)
            kept.append(v)
        elif year <= last:
            dropped.append(v)
        else:
            kept.append(v)
    return dropped, kept, unknown


# --- settings.py ---------------------------------------------------------------

def read_value(text, name):
    """The Python value assigned to NAME in settings.py text, e.g. "26.1" or a list."""
    match = re.search(rf"^{name} = (\[.*?\]|\"[^\"]*\")", text, flags=re.M | re.S)
    if not match:
        sys.exit(f"Could not find {name} in settings.py.")
    return ast.literal_eval(match.group(1))


def replace_line(text, pattern, replacement):
    """Replace exactly one match of PATTERN (multiline) or stop with an error."""
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.M | re.S)
    if count != 1:
        sys.exit(f"Could not update settings.py (pattern not found: {pattern}).")
    return text


def switch_text(text, new_version):
    """Return (new settings.py text, dropped versions, kept versions, unknown versions)."""
    old_version = read_value(text, "API_VERSION")
    if parse_stable(new_version) <= parse_stable(old_version):
        sys.exit(f"GED {new_version} is not newer than the current API_VERSION {old_version}.")
    year = covered_year(new_version)
    dropped, kept, unknown = split_candidates(read_value(text, "CANDIDATE_VERSIONS"), new_version)

    text = replace_line(text, r'^API_VERSION = "[^"]*"(.*)$',
                        lambda m: f'API_VERSION = "{new_version}"'
                                  + re.sub(r"end of \d{4}", f"end of {year}", m.group(1)))
    text = replace_line(text, r'^END_DATE = "[^"]*"', f'END_DATE = "{year}-12-31"')
    line = "CANDIDATE_VERSIONS = [" + ", ".join(f'"{v}"' for v in kept) + "]"
    text = replace_line(text, r"^CANDIDATE_VERSIONS = \[.*?\]", line)
    return text, dropped, kept, unknown


def show_diff(old, new):
    """Print a unified diff of settings.py."""
    diff = difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                "settings.py", "settings.py (new)")
    sys.stdout.writelines(diff)


# --- API -----------------------------------------------------------------------

def version_exists(version, token):
    """Ask the API for one event from this version (1 request). True, False, or None if unsure."""
    url = f"{API_URL}{version}?pagesize=1&Country=475"
    request = urllib.request.Request(url, headers={"x-ucdp-access-token": token})
    try:
        with urllib.request.urlopen(request, timeout=30):
            return True
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return None     # token refused: we can't tell
        if 400 <= e.code < 500:
            return False    # 404 or 400: not published (yet)
        return None
    except (urllib.error.URLError, OSError):
        return None


def next_stable(version):
    """The stable release after this one: "26.1" -> "27.1"."""
    return f"{parse_stable(version) + 1}.1"


def stable_notice(current, token, today=None):
    """A one-line notice if a newer stable release than CURRENT is out, else None.

    Costs 1 request, and only from May of the year the next release is expected
    (27.1 from May 2027 on); before that it costs nothing. Never stops the caller.
    """
    try:
        upcoming = next_stable(current)
        today = today or date.today()
        expected = date(2000 + parse_stable(upcoming), NEXT_STABLE_FROM_MONTH, 1)
        if today < expected or not version_exists(upcoming, token):
            return None
    except (SystemExit, Exception):     # a notice must never break the weekly update
        return None
    return (f"UCDP has published the stable GED {upcoming}. Switch to it with "
            f"`python switch_stable.py {upcoming}` (see README, 'Yearly stable release').")


# --- Main ----------------------------------------------------------------------

NEXT_STEPS = """
Next steps:
  python save_events.py     # downloads GED {version} (the old releases stay in the database)
  python clean_events.py
  python build_map.py       # optional: look at the map locally first
  python publish.py
Then commit settings.py and docs/index.html on a branch and open a pull request."""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Switch settings.py to a new stable GED release.")
    parser.add_argument("version", help="the new stable release, e.g. 27.1")
    parser.add_argument("--dry-run", action="store_true", help="show the changes, write nothing")
    parser.add_argument("--no-check", action="store_true",
                        help="don't ask the API whether the version exists (no token needed)")
    args = parser.parse_args(argv)
    version = args.version.strip()
    parse_stable(version)

    with open(SETTINGS_PATH, encoding="utf-8") as f:
        old = f.read()
    new, dropped, kept, unknown = switch_text(old, version)

    if not args.no_check:
        from fetch_nigeria import load_token
        exists = version_exists(version, load_token())
        if exists is False:
            sys.exit(f"GED {version} is not published yet (the API said no). Nothing changed.")
        if exists is None:
            sys.exit("Could not check with the API (token refused or server/network error). "
                     "Try again later, or use --no-check. Nothing changed.")
        print(f"GED {version} is published (1 API request).")

    show_diff(old, new)
    print(f"\nGED {version} covers events up to {covered_year(version)}-12-31.")
    print(f"Dropped Candidate versions (now covered): {', '.join(dropped) or 'none'}")
    print(f"Kept Candidate versions: {', '.join(kept) or 'none'}")
    if unknown:
        print(f"Warning: unknown version format, kept as is, check by hand: {', '.join(unknown)}")
    if not any(re.fullmatch(r"\d{2}\.0\.\d{1,2}", v) for v in kept):
        print("Warning: no monthly Candidate version (like 27.0.6) is left, so update_candidates.py "
              "has nothing to count up from. Add the latest monthly release to CANDIDATE_VERSIONS.")

    if args.dry_run:
        print("\nDry run: settings.py was not changed.")
        return
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        f.write(new)
    print("\nsettings.py updated.")
    print(NEXT_STEPS.format(version=version))


if __name__ == "__main__":
    main()

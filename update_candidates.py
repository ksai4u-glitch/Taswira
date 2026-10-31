"""
Check whether UCDP has published a newer monthly GED Candidate release than
the last one in settings.py, and if so add it to CANDIDATE_VERSIONS.

Monthly versions count up: 26.0.8 -> 26.0.9 -> ... -> 26.0.12 -> 27.0.1.
Each check costs 1 API request (pagesize=1), plus 1 more per new version found,
plus up to 2 retries if UCDP times out or answers 429/5xx (see ucdp_api.py).

If anything goes wrong it stops with a message and a non-zero exit code, and
settings.py is left exactly as it was (it is only ever replaced in one step).

Run by the weekly GitHub Actions workflow (.github/workflows/update.yml),
but you can also run it by hand. Uses only the Python standard library.
"""

import ast
import os
import re
import sys

import ucdp_api
from fetch_nigeria import load_token
from safe_files import write_text

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.py")
MAX_NEW = 3     # never add more than this many versions in one run
MONTHLY = re.compile(r"(\d+)\.0\.(\d+)")
LIST_LINE = re.compile(r"^CANDIDATE_VERSIONS = \[.*?\]", re.M | re.S)


def parse_monthly(version):
    """(year, month) of a monthly version like "26.0.9"; ValueError for anything else."""
    match = MONTHLY.fullmatch(version)
    if not match or not 1 <= int(match.group(2)) <= 12:
        raise ValueError(f"{version!r} is not a monthly Candidate version like 26.0.9")
    return int(match.group(1)), int(match.group(2))


def next_version(version):
    """The monthly release after this one: "26.0.9" -> "26.0.10", "26.0.12" -> "27.0.1"."""
    year, month = parse_monthly(version)
    if month < 12:
        return f"{year}.0.{month + 1}"
    return f"{year + 1}.0.1"


def last_monthly(versions):
    """The newest monthly version (YY.0.M) in the list; quarterly ones look different."""
    monthly = [v for v in versions if MONTHLY.fullmatch(v)]
    if not monthly:
        sys.exit("No monthly Candidate version (like 26.0.8) in CANDIDATE_VERSIONS to count up from.")
    return max(monthly, key=parse_monthly)


def is_published(version, token):
    """Ask the API for one Nigeria event from this version.

    True if the release exists and has events, False if it is not published yet
    (HTTP 400/404) or is still empty. Raises ucdp_api.UCDPError for anything
    else (token refused, UCDP down after retries, an answer of a new shape).
    """
    url = f"{ucdp_api.API_URL}{version}?pagesize=1&Country=475"
    try:
        data = ucdp_api.get_page(url, token)
    except ucdp_api.HTTPStatusError as e:
        if 400 <= e.code < 500:
            return False        # 404 or 400: this version isn't published (yet)
        raise
    if data["TotalCount"] == 0:
        print(f"GED {version} answers but has no Nigeria events yet; not adding it. "
              "The next run will check again.")
        return False
    return True


def read_candidates(text):
    """The CANDIDATE_VERSIONS list as written in the text of settings.py."""
    for node in ast.parse(text).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", None) == "CANDIDATE_VERSIONS"):
            value = ast.literal_eval(node.value)
            if isinstance(value, list) and all(isinstance(v, str) for v in value):
                return value
    raise ValueError("CANDIDATE_VERSIONS is not a plain list of strings in settings.py")


def with_versions_added(text, new_versions):
    """The text of settings.py with new_versions appended to CANDIDATE_VERSIONS.

    Checks the result before returning it: the new list must read back as expected.
    """
    current = read_candidates(text)
    duplicates = [v for v in new_versions if v in current]
    if duplicates:
        raise ValueError(f"already in CANDIDATE_VERSIONS: {', '.join(duplicates)}")
    updated = current + list(new_versions)
    line = "CANDIDATE_VERSIONS = [" + ", ".join(f'"{v}"' for v in updated) + "]"
    new_text, count = LIST_LINE.subn(lambda _: line, text, count=1)
    if count != 1:
        raise ValueError("could not find the CANDIDATE_VERSIONS line in settings.py")
    if read_candidates(new_text) != updated:
        raise ValueError("the rewritten CANDIDATE_VERSIONS line does not read back correctly")
    return new_text


def add_to_settings(new_versions, path=SETTINGS_PATH):
    """Append the new versions to CANDIDATE_VERSIONS in settings.py, in one atomic write."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        new_text = with_versions_added(text, new_versions)
    except (ValueError, SyntaxError) as e:
        sys.exit(f"Not changing settings.py: {e}.")
    write_text(path, new_text)


def find_new_versions(candidates, token):
    """The published monthly versions after the newest one in candidates (at most MAX_NEW)."""
    candidate = next_version(last_monthly(candidates))
    new_versions = []
    while len(new_versions) < MAX_NEW and is_published(candidate, token):
        new_versions.append(candidate)
        candidate = next_version(candidate)
    return new_versions, candidate


def main(settings_path=SETTINGS_PATH):
    with open(settings_path, encoding="utf-8") as f:
        try:
            candidates = read_candidates(f.read())
        except (ValueError, SyntaxError) as e:
            sys.exit(f"Could not read settings.py: {e}.")

    token = load_token()
    try:
        new_versions, unpublished = find_new_versions(candidates, token)
    except ucdp_api.UCDPError as e:
        sys.exit(f"Update check failed, nothing changed: {e}")

    if new_versions:
        add_to_settings(new_versions, settings_path)
        print(f"New Candidate release(s): {', '.join(new_versions)}. Added to settings.py.")
    else:
        print(f"No new Candidate release yet ({unpublished} is not published).")

    # Tell the GitHub Actions workflow what happened, so it knows whether to rebuild
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"new_versions={' '.join(new_versions)}\n")


if __name__ == "__main__":
    main()

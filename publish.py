"""
Stage 7: build the public version of the map as docs/index.html.

GitHub Pages can serve the docs/ folder of the repository as a website, so
committing docs/index.html and pushing it is what publishes the map.

Reads the clean_events table (no API requests), builds the same page as
build_map.py, runs a few safety checks, then writes docs/index.html.
Uses only the Python standard library.
"""

import os
import sys

from build_map import fill_template, load_all
from fetch_nigeria import load_token
from settings import API_VERSION, CANDIDATE_VERSIONS

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(HERE, "docs", "index.html")


def check(page, mapped, unmapped):
    """Stop before writing anything public if a basic rule is broken."""
    problems = []

    # 1. The token must never end up on a public page.
    try:
        token = load_token()
    except SystemExit:          # no token on this computer: nothing that could leak
        token = None
    if token and token in page:
        problems.append("the page contains your UCDP token")

    # 2. UCDP must be credited, with the dataset version.
    if "Uppsala Conflict Data Program" not in page or f"version {API_VERSION}" not in page:
        problems.append("the UCDP credit or dataset version is missing")

    # 3. Preliminary data must be labelled as such.
    if any(e["preliminary"] for e in mapped + unmapped):
        if "preliminary" not in page or not all(v in page for v in CANDIDATE_VERSIONS):
            problems.append("preliminary Candidate events are not labelled")

    if problems:
        sys.exit("Not publishing: " + "; ".join(problems) + ".")


def main():
    mapped, unmapped = load_all()
    page = fill_template(mapped, unmapped)
    check(page, mapped, unmapped)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(page)

    prelim = sum(e["preliminary"] for e in mapped + unmapped)
    size_mb = os.path.getsize(OUTPUT_PATH) / 1_000_000
    print(f"Checks passed: no token, UCDP credited (GED {API_VERSION}), "
          f"{prelim} preliminary events labelled.")
    print(f"Wrote {OUTPUT_PATH} ({size_mb:.1f} MB, {len(mapped)} events on the map).")
    print("\nTo publish, commit and push it:")
    print("  git add docs/index.html")
    print('  git commit -m "Update public map"')
    print("  git push")


if __name__ == "__main__":
    main()

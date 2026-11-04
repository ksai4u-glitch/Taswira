"""Build an offline cinematic preview from Taswira's validated history data.

    python build_director.py --check
    python build_director.py --output /tmp/taswira-director.html

Output is explicit: this command never publishes or rebuilds the live history page.
"""
import argparse
import json
from pathlib import Path

import build_history as history

ROOT = Path(__file__).resolve().parent


def build():
    _, data = history.build()
    data["chapters"] = [c for c in data["chapters"] if c["id"] in ("deep", "nok")]
    cited = {"natural-earth", "merdith-2021"}
    for chapter in data["chapters"]:
        for item in [*chapter["features"].values(), *chapter["scenes"]]:
            cited.update(item.get("sources", []))
    data["sources"] = {key: value for key, value in data["sources"].items() if key in cited}
    data["emblems"] = {}
    data["states"] = {}
    data["arcs"] = []
    chapters = [history.read_json(str(ROOT / "history" / "chapters" / (c["id"] + ".json")))
                for c in data["chapters"]]
    template = (ROOT / "history" / "director" / "template.html").read_text()
    runtime = (ROOT / "history" / "director" / "director.js").read_text()
    transcript = history.transcript(chapters, data["sources"], data["states"], data["emblems"])
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    for slot in ("{{DATA}}", "{{RUNTIME}}", "{{TRANSCRIPT}}"):
        if template.count(slot) != 1:
            raise ValueError(f"Expected one {slot} slot")
    page = template.replace("{{DATA}}", payload).replace("{{RUNTIME}}", runtime).replace("{{TRANSCRIPT}}", transcript)
    return page, sum(len(c["scenes"]) for c in chapters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--output", type=Path)
    args = parser.parse_args()
    page, count = build()
    if args.check:
        print(f"Director preview checked: {count} scenes. Nothing written.")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(page)
        print(f"Director preview: {count} scenes, {len(page.encode()):,} bytes. Wrote {args.output}")


if __name__ == "__main__":
    main()

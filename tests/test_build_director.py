"""Build the offline director preview without publishing to docs/."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DirectorBuildTests(unittest.TestCase):
    def test_check_validates_without_writing_a_live_page(self):
        result = subprocess.run([sys.executable, str(ROOT / "build_director.py"), "--check"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("13 scenes", result.stdout)
        self.assertFalse((ROOT / "docs" / "director.html").exists())

    def test_export_contains_sourced_scenes_and_no_network_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "preview.html"
            result = subprocess.run([sys.executable, str(ROOT / "build_director.py"), "--output", str(target)],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = target.read_text()
        data = json.loads(re.search(r'<script id="director-data" type="application/json">(.*?)</script>',
                                    page, re.S).group(1))
        self.assertEqual([c["id"] for c in data["chapters"]], ["deep", "nok"])
        self.assertEqual(sum(len(c["scenes"]) for c in data["chapters"]), 13)
        self.assertTrue(data["plates"]["shapes"])
        self.assertEqual(data["emblems"], {}, "This preview has no political-emblem scenes")
        self.assertNotIn("grid3-states", data["sources"], "No administrative-boundary scenes are exported")
        for chapter in data["chapters"]:
            for scene in chapter["scenes"]:
                for source in scene["sources"]:
                    self.assertIn(source, data["sources"])
        self.assertNotRegex(page, r'<(?:script|link)[^>]+(?:src|href)="https?://')
        self.assertNotIn("{{", page)
        self.assertIn("Unreviewed draft", page)
        self.assertIn("CC BY 4.0", page)
        self.assertIn("Text version", page)


if __name__ == "__main__":
    unittest.main()

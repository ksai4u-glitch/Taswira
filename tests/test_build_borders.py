"""Checks for the draft borders map (build_borders.py). Run: python -m unittest tests.test_build_borders"""
import copy
import json
import os
import tempfile
import unittest

import build_borders as bb
from borders.geo import make_scramble as ms


class BordersMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = bb.load(os.path.join(bb.BORDERS, "story.json"))
        cls.geo = bb.load(os.path.join(bb.BORDERS, "geo", "scramble.json"))
        cls.tmp = tempfile.TemporaryDirectory()
        out, _ = bb.build(os.path.join(cls.tmp.name, "borders.html"), built="2026-11-26")
        with open(out, encoding="utf-8") as f:
            cls.page = f.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_story_and_borders_agree(self):
        self.assertEqual(bb.check(self.story, self.geo), [])

    def test_page_credits_cshapes_is_labelled_draft_and_needs_no_other_site(self):
        self.assertIn("CShapes 2.0", self.page)
        self.assertIn("Schvitz", self.page)
        self.assertIn("Draft", self.page)
        self.assertIn('name="robots" content="noindex"', self.page)
        self.assertNotIn("unpkg.com", self.page)
        self.assertNotIn("__DATA__", self.page)
        self.assertNotIn("__BUILT__", self.page)

    def test_writes_docs_only_when_publishing(self):
        with self.assertRaises(SystemExit):
            bb.build(os.path.join(os.path.dirname(bb.__file__), "docs", "borders.html"))

    def test_published_page_drops_the_draft_badge_and_noindex_but_keeps_credits(self):
        out, _ = bb.build(os.path.join(self.tmp.name, "live.html"), built="2026-11-27", publish=True)
        with open(out, encoding="utf-8") as f:
            live = f.read()
        self.assertNotIn("noindex", live)
        self.assertNotIn('class="draft"', live)
        self.assertNotIn("(draft)", live)
        for credit in ("CShapes 2.0", "Schvitz", "Pakenham", "Not yet reviewed by a historian"):
            self.assertIn(credit, live)
        self.assertIn('og:image" content="https://ksai4u-glitch.github.io/Taswira/borders-preview.png"', live)

    def test_every_unit_needs_a_period_name(self):
        story = copy.deepcopy(self.story)
        del story["names"]["475"]
        self.assertTrue(any("(475)" in p for p in bb.check(story, self.geo)))

    def test_moments_need_known_sources_and_order(self):
        story = copy.deepcopy(self.story)
        story["moments"][1]["sources"] = ["made-up"]
        story["moments"][2]["date"] = "1880-01-01"
        problems = bb.check(story, self.geo)
        self.assertTrue(any("unknown source made-up" in p for p in problems))
        self.assertTrue(any("outside" in p for p in problems))
        self.assertTrue(any("date order" in p for p in problems))

    def test_borders_cover_1886_to_1960_with_one_nigeria_then_independence(self):
        self.assertEqual((self.geo["first"], self.geo["last"]), ("1886-01-01", "1960-10-01"))
        def on(date):
            return {(u["gw"], u["owner"]) for u in self.geo["units"] if u["start"] <= date <= u["end"]}
        self.assertIn((475, 200), on("1914-01-01"))
        self.assertFalse({4783, 4784} & {gw for gw, _ in on("1914-01-01")})
        self.assertIn((475, 475), on("1960-10-01"))
        dates = [m["date"] for m in self.story["moments"]]
        self.assertIn("1914-01-01", dates)
        self.assertEqual(dates[-1], "1960-10-01")

    def test_highlight_must_be_on_the_map_that_day(self):
        story = copy.deepcopy(self.story)
        story["moments"][0]["highlight"] = [475]   # Nigeria did not exist in 1886
        self.assertTrue(any("highlight 475" in p for p in bb.check(story, self.geo)))

    def test_correction_needs_an_end_after_its_start(self):
        story = copy.deepcopy(self.story)
        story["corrections"][-1]["to"] = "1930-01-01"
        self.assertTrue(any("'to' must be a date after 'from'" in p for p in bb.check(story, self.geo)))

    def test_africa_filter_keeps_africa_and_drops_arabia_and_europe(self):
        self.assertTrue(ms.in_africa(8, 9))        # Nigeria
        self.assertTrue(ms.in_africa(39.8, 15.5))  # Eritrea
        self.assertTrue(ms.in_africa(46.7, -19))   # Madagascar
        self.assertFalse(ms.in_africa(43, 14))     # Kamaran island, Yemen
        self.assertFalse(ms.in_africa(39, 23))     # Hejaz
        self.assertFalse(ms.in_africa(14.4, 35.9)) # Malta

    def test_simplify_keeps_arc_ends(self):
        line = [[0, 0], [1, 0.001], [2, 0], [3, 1], [4, 0]]
        out = ms.simplify(line, 0.04)
        self.assertEqual((out[0], out[-1]), ([0, 0], [4, 0]))
        self.assertIn([3, 1], out)
        self.assertNotIn([1, 0.001], out)

    def test_encode_round_trips_to_a_hundredth_of_a_degree(self):
        pts = [[10.123, -4.5], [10.2, -4.49], [11, 3]]
        flat, x, y, back = ms.encode(pts), 0, 0, []
        for i in range(0, len(flat), 2):
            x += flat[i]; y += flat[i + 1]; back.append([x / 100, y / 100])
        self.assertEqual(back, [[10.12, -4.5], [10.2, -4.49], [11.0, 3.0]])


if __name__ == "__main__":
    unittest.main()

"""Checks for the draft elections map (build_elections.py). Run: python -m unittest tests.test_build_elections"""
import copy
import os
import tempfile
import unittest

import build_elections as be


class ElectionsMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story, cls.topo = be.load_all()
        cls.tmp = tempfile.TemporaryDirectory()
        out, _ = be.build(os.path.join(cls.tmp.name, "elections.html"), built="2026-11-27")
        with open(out, encoding="utf-8") as f:
            cls.page = f.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def election(self, year):
        return next(e for e in self.story["elections"] if e["year"] == year)

    def test_results_agree_with_the_story_and_the_map(self):
        self.assertEqual(be.check(self.story, self.topo), [])

    def test_2015_and_2019_states_add_up_to_inec_totals(self):
        for year in (2015, 2019):
            e = self.election(year)
            for key, total in e["national"].items():
                self.assertEqual(sum(s[key] for s in e["states"].values()), total, (year, key))

    def test_known_state_results(self):
        e = self.election(2023)
        self.assertEqual(e["states"]["NG-KN"]["NNPP"], 997279)   # Kwankwaso won Kano
        self.assertEqual(e["states"]["NG-LA"]["LP"], 582454)     # Obi won Lagos
        self.assertEqual(e["states"]["NG-LA"]["APC"], 572606)
        self.assertEqual(e["states"]["NG-YO"]["PDP"], 198567)    # corrected
        self.assertEqual(self.election(2015)["states"]["NG-RI"]["PDP"], 1487075)

    def test_a_gap_must_be_admitted(self):
        story = copy.deepcopy(self.story)
        story["known_gaps"] = []
        problems = be.check(story, self.topo)
        self.assertTrue(any("2023: states do not add up" in p for p in problems))
        self.assertTrue(any("Kwara" in p for p in problems))

    def test_a_missing_state_is_caught(self):
        story = copy.deepcopy(self.story)
        del next(e for e in story["elections"] if e["year"] == 2019)["states"]["NG-ZA"]
        self.assertTrue(any("2019: states" in p for p in be.check(story, self.topo)))

    def test_winner_must_have_most_votes(self):
        story = copy.deepcopy(self.story)
        story["elections"][0]["winner"] = "PDP"
        self.assertTrue(any("winner" in p for p in be.check(story, self.topo)))

    def test_page_credits_inec_and_grid3_and_is_a_draft(self):
        for must in ("INEC", "GRID3", "geoBoundaries", "Draft", "Form EC8D", "section 134(2)"):
            self.assertIn(must, self.page)
        self.assertIn('name="robots" content="noindex"', self.page)
        self.assertNotIn("unpkg.com", self.page)
        self.assertNotIn("__DATA__", self.page)

    def test_writes_docs_only_when_publishing(self):
        with self.assertRaises(SystemExit):
            be.build(os.path.join(os.path.dirname(be.__file__), "docs", "elections.html"))

    def test_published_page_drops_draft_but_keeps_credits(self):
        out, _ = be.build(os.path.join(self.tmp.name, "live.html"), built="2026-11-27", publish=True)
        with open(out, encoding="utf-8") as f:
            live = f.read()
        self.assertNotIn("noindex", live)
        self.assertNotIn('class="draft"', live)
        for credit in ("INEC", "GRID3", "geoBoundaries"):
            self.assertIn(credit, live)


if __name__ == "__main__":
    unittest.main()

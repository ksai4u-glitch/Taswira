"""Tests for the civil-war chapter: independence, the 1966 crisis, the war of 1967 to 1970, the
blockade and its human cost, and the aftermath. They check the rules for war and violence in
history/README.md. Run from the repository folder:

    python -m unittest discover -s tests
"""

import copy
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_history as bh  # noqa: E402


class CivilWarChapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states, _, _ = bh.load_states()
        cls.sources = bh.read_json(bh.SOURCES_PATH)
        cls.emblems = bh.read_json(os.path.join(bh.HISTORY_DIR, "emblems.json"))
        cls.ch = bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", "civil-war.json"))
        cls.scenes = {s["id"]: s for s in cls.ch["scenes"]}

    def test_chapter_sits_between_colonial_rule_and_the_states_and_passes(self):
        self.assertEqual(bh.CHAPTERS.index("civil-war"), bh.CHAPTERS.index("colonial") + 1)
        self.assertEqual(bh.CHAPTERS.index("states"), bh.CHAPTERS.index("civil-war") + 1)
        self.assertEqual(bh.check([copy.deepcopy(self.ch)], self.sources, self.states, set(), self.emblems), [])
        self.assertEqual(self.ch["title"].split(":")[0], "The Civil War", "a short chapter button")

    def test_scenes_follow_the_war_rules_sequence(self):
        # context, then the war, then its human cost in its own scene, then the aftermath
        self.assertEqual(list(self.scenes), ["republic", "crisis", "war", "blockade", "end"])
        for sid in ("crisis", "war", "blockade", "end"):
            sc = self.scenes[sid]
            self.assertTrue(sc["sensitive"], sid)
            self.assertEqual(sc["mood"], "calm", sid)
            self.assertNotIn("erupt", sc)
            self.assertNotIn("warships", sc)
            self.assertNotIn("effects", sc, f"{sid}: no beacons or comets over killing or hunger")
            self.assertTrue(all(b["pose"] == 7 for b in sc["beats"]), f"{sid}: Zomo stays still")

    def test_beats_are_dated_in_order_and_match_the_text(self):
        for sc in self.ch["scenes"]:
            years = [b["when"]["from"] for b in sc["beats"]]
            self.assertEqual(years, sorted(years), sc["id"])
            self.assertEqual(sc["text"], " ".join(b["text"] for b in sc["beats"]), sc["id"])
            self.assertFalse(re.search(r"\d\.\d", sc["text"]), "a decimal point would split a caption")
        self.assertEqual(self.scenes["end"]["beats"][1]["when"]["label"], "15 January 1970")

    def test_numbers_of_the_dead_are_ranges_with_their_sources(self):
        text = " ".join(s["text"] for s in self.ch["scenes"])
        for rng in ("8,000 to 30,000", "500 to 800", "500,000 to 3 million", "500,000 to one million",
                    "45,000 and 100,000", "two and four and a half million"):
            self.assertIn(rng, text)
        # incompatible famine estimates are given separately, under a "differ" basis
        famine = self.scenes["blockade"]["beats"][2]
        self.assertEqual(famine["when"]["basis"], "differ")
        self.assertIn("not known", famine["text"])
        self.assertIn("never as counters", self.ch["method"])

    def test_human_consequences_have_their_own_beats(self):
        war = self.scenes["war"]["beats"]
        asaba = next(b for b in war if "Asaba" in b["text"])
        self.assertNotIn("Enugu", asaba["text"], "the killings at Asaba are not folded into a military beat")
        crisis = self.scenes["crisis"]["beats"]
        self.assertTrue(any("massacred" in b["text"] for b in crisis))

    def test_no_fronts_or_filled_areas(self):
        for f in self.ch["features"]:
            self.assertEqual(f["kind"], "point", f["id"])
            self.assertNotIn("reach_km", f)
        for sc in self.ch["scenes"]:
            self.assertNotIn("control", sc, "captured towns are dated points, not filled territory")

    def test_every_source_was_opened(self):
        cited = {s for f in self.ch["features"] for s in f["sources"]} | {s for sc in self.ch["scenes"] for s in sc["sources"]}
        for sid in cited:
            self.assertNotIn("Not opened", self.sources[sid]["checked"], sid)
        self.assertIn("deliberate policy", self.sources["wiki-nigerian-civil-war"]["checked"])


if __name__ == "__main__":
    unittest.main()

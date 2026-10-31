"""Tests for the Kanem-Bornu chapter: order, places, sources and honest dates.
Run from the repository folder:

    python -m unittest discover -s tests
"""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_history as bh  # noqa: E402


class KanemChapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states, _, _ = bh.load_states()
        cls.sources = bh.read_json(bh.SOURCES_PATH)
        cls.emblems = bh.read_json(bh.EMBLEMS_PATH)
        cls.kanem = bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", "kanem.json"))

    def problems(self, ch):
        return bh.check([ch], self.sources, self.states, set(), self.emblems)

    def chapter(self):
        ch = copy.deepcopy(self.kanem)
        return ch, {f["id"]: f for f in ch["features"]}, {s["id"]: s for s in ch["scenes"]}

    def test_chapter_checks_and_sits_in_time_order(self):
        self.assertEqual(self.problems(copy.deepcopy(self.kanem)), [])
        # Kanem (from about 700) comes after Nok and before the Hausa cities (from about 1000)
        self.assertEqual(bh.CHAPTERS.index("kanem"), bh.CHAPTERS.index("nok") + 1)
        self.assertLess(bh.CHAPTERS.index("kanem"), bh.CHAPTERS.index("hausa"))

    def test_scenes_run_forward_from_kanem_to_1846(self):
        scenes = self.kanem["scenes"]
        starts = [s["when"]["from"] for s in scenes]
        self.assertEqual(starts, sorted(starts))
        self.assertEqual(scenes[-1]["when"]["to"], 1846)
        self.assertEqual([s["id"] for s in scenes],
                         ["kanem-east", "sayfawa", "bornu", "idris-alooma", "sayfawa-end"])

    def test_every_source_is_recorded_with_what_was_checked(self):
        cited = set()
        for f in self.kanem["features"]:
            cited.update(f["sources"])
        for s in self.kanem["scenes"]:
            cited.update(s["sources"])
        for sid in cited:
            self.assertIn(sid, self.sources, sid)
            for field in ("title", "url", "rights", "checked"):
                self.assertTrue(self.sources[sid].get(field), f"{sid}: {field}")
        # Sources seen only through search excerpts say so
        for sid in ("lc-chad-kanem", "wiki-idris-alooma", "wiki-ibrahim-iv", "armitage-2015"):
            self.assertIn("web-search excerpts", self.sources[sid]["checked"], sid)

    def test_njimi_is_not_given_a_made_up_position(self):
        _, features, _ = self.chapter()
        self.assertFalse([f for f in features if "njimi" in f or "tie" == f])
        kanem = features["kanem"]
        self.assertIn("not a capital", kanem["location"])
        self.assertGreaterEqual(kanem["uncertainty_km"], 100)

    def test_lake_chad_has_no_invented_shoreline(self):
        _, features, _ = self.chapter()
        lake = features["lake-chad"]
        self.assertEqual(lake["form"], "lake")
        self.assertNotIn("reach_km", lake)          # no disc pretending to be the old lake
        self.assertIn("not the shoreline", lake["location"])

    def test_disputed_dates_are_labelled(self):
        _, features, scenes = self.chapter()
        self.assertEqual(features["kanem"]["status"], "disputed")
        self.assertEqual(features["ngazargamu"]["status"], "disputed")
        for sid in ("kanem-east", "sayfawa", "bornu", "idris-alooma", "sayfawa-end"):
            self.assertTrue(scenes[sid].get("disputed"), sid)
        for sid in ("sayfawa", "bornu", "idris-alooma"):
            self.assertIn("differ", scenes[sid]["when"]["label"], sid)

    def test_scenes_about_war_and_death_are_sensitive(self):
        _, _, scenes = self.chapter()
        for sid in ("bornu", "idris-alooma", "sayfawa-end"):
            self.assertIs(scenes[sid].get("sensitive"), True, sid)

    def test_no_flag_is_drawn(self):
        for f in self.kanem["features"]:
            if "emblem" in f:
                self.assertEqual(self.emblems[f["emblem"]]["tier"], "none", f["id"])

    def test_the_move_west_is_drawn_as_uncertain(self):
        _, features, _ = self.chapter()
        move = features["move-west"]
        self.assertEqual(move["type"], "migration")
        self.assertEqual(move["uncertain"], "whole")
        self.assertIn("not drawn", move["location"])

    def test_a_place_outside_the_map_is_caught(self):
        ch, features, _ = self.chapter()
        features["bilma"]["coordinates"] = [25.9, 14.4]     # the Fezzan is told, not placed
        self.assertTrue(any("bilma: coordinates" in p for p in self.problems(ch)))

    def test_an_unknown_source_is_caught(self):
        ch, _, scenes = self.chapter()
        scenes["idris-alooma"]["sources"].append("ibn-furtu-full-text")
        self.assertTrue(any("ibn-furtu-full-text" in p for p in self.problems(ch)))

    def test_text_version_lists_the_chapter(self):
        text = bh.transcript([self.kanem], self.sources, self.states, self.emblems)
        self.assertIn("Kanem-Bornu: kings on both sides of Lake Chad", text)
        self.assertIn("Ngazargamu", text)
        self.assertIn("Idris Alooma", text)


if __name__ == "__main__":
    unittest.main()

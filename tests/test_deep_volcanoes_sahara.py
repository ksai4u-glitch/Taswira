"""Tests for the deep-time additions: Africa's volcanoes, the birth of the Sahara, rivers drawn
downstream, and the faster pacing. Run from the repository folder:

    python -m unittest discover -s tests
"""

import copy
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_history as bh  # noqa: E402


def encode(points):
    """[[lat, lon], ...] in degrees as the background stores a line: thousandths, as differences."""
    out, plat, plon = [], 0, 0
    for lat, lon in points:
        a, b = round(lat * 1000), round(lon * 1000)
        out += [a - plat, b - plon]
        plat, plon = a, b
    return out


def ends(flat):
    a, b = bh._ends(flat)
    return (a[0] / 1000, a[1] / 1000), (b[0] / 1000, b[1] / 1000)


class RiverDirectionTests(unittest.TestCase):
    def test_a_backwards_segment_is_turned_round(self):
        # a -> b -> c -> d is one river, but b..c is stored from c to b. Then two segments start
        # at c and none ends there (a river "splitting at its source"), and two end at b and none
        # starts there (a river "vanishing inland"), as with the Nile in Nubia.
        a, b, c, d = (0, 0), (1, 1), (2, 2), (3, 3)
        rivers = [[3, encode([a, (0.5, 0.5), b])], [3, encode([c, (1.5, 1.5), b])], [3, encode([c, (2.5, 2.5), d])]]
        fixed = bh.orient_rivers(rivers)
        self.assertEqual(ends(fixed[1][1]), ((1.0, 1.0), (2.0, 2.0)))
        self.assertEqual(fixed[0], rivers[0])
        self.assertEqual(fixed[2], rivers[2])

    def test_a_delta_split_is_left_alone(self):
        # a river that splits into two mouths: one end, two starts at the split, both kept
        up, split = (5, 6), (4.9, 6.2)
        rivers = [[3, encode([up, split])], [3, encode([split, (4.5, 6.1)])], [3, encode([split, (4.6, 6.5)])]]
        self.assertEqual(bh.orient_rivers(rivers), rivers)

    def test_reversing_keeps_every_point(self):
        pts = [(9.0, 4.6), (8.0, 5.0), (6.5, 5.6), (5.1, 5.5)]
        back = bh._reverse(encode(pts))
        self.assertEqual(ends(back), ((5.1, 5.5), (9.0, 4.6)))
        self.assertEqual(bh._reverse(back), encode(pts))

    def test_the_nile_in_nubia_runs_north(self):
        # Natural Earth stores the Nile between 21.6 N and 24.0 N from its mouth end
        bg = bh.load_background()
        seg = [ends(f) for _, f in bg["rivers"] if {p[0] for p in ends(f)} == {21.609, 23.988}]
        self.assertEqual(seg, [((21.609, 31.091), (23.988, 32.879))])


class DeepTimeAdditionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states, _, _ = bh.load_states()
        cls.sources = bh.read_json(bh.SOURCES_PATH)
        cls.emblems = bh.read_json(os.path.join(bh.HISTORY_DIR, "emblems.json"))
        cls.deep = bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", "deep.json"))
        cls.plates = bh.load_plates()

    def problems(self, ch):
        return bh.check([ch], self.sources, self.states, set(), self.emblems, self.plates)

    def copy(self, scene):
        ch = copy.deepcopy(self.deep)
        return ch, {f["id"]: f for f in ch["features"]}, next(s for s in ch["scenes"] if s["id"] == scene)

    def test_chapter_passes_and_scenes_run_in_time_order(self):
        self.assertEqual(self.problems(copy.deepcopy(self.deep)), [])
        ids = [s["id"] for s in self.deep["scenes"]]
        self.assertEqual(ids[ids.index("coal"):], ["coal", "fire-below", "delta", "sahara-born", "green-sahara"])
        starts = [s["when"]["from"] for s in self.deep["scenes"]]
        self.assertEqual(starts, sorted(starts))

    def test_volcanoes_are_volcano_points_with_sources(self):
        _, feats, sc = self.copy("fire-below")
        for fid in sc["show"]:
            self.assertEqual(feats[fid]["form"], "volcano", fid)
            self.assertTrue(feats[fid]["sources"], fid)
        self.assertEqual(sc["mood"], "volcanic")
        self.assertTrue(set(sc["erupt"]) <= set(sc["show"]))

    def test_volcano_beats_are_dated_in_order(self):
        _, _, sc = self.copy("fire-below")
        years = [b["when"]["from"] for b in sc["beats"]]
        self.assertEqual(years, sorted(years))
        self.assertEqual({b["when"]["basis"] for b in sc["beats"]}, {"geology", "differ", "record"})
        # a decimal point inside a sentence would be cut by the sentence splitter
        self.assertFalse(re.search(r"\d\.\d", sc["text"]))

    def test_no_eruption_effects_over_the_deaths_at_goma(self):
        _, _, sc = self.copy("fire-below")
        self.assertNotIn("nyiragongo", sc["erupt"])
        self.assertEqual(sc["beats"][-1]["pose"], 7, "the beat about deaths uses Zomo's still pose")

    def test_erupt_is_checked(self):
        ch, feats, sc = self.copy("fire-below")
        sc["erupt"] = ["kilimanjaro", "niger-delta"]
        self.assertTrue(any("erupt needs volcanoes" in p for p in self.problems(ch)))
        ch, feats, sc = self.copy("fire-below")
        sc["sensitive"] = True
        self.assertTrue(any("not marked sensitive" in p for p in self.problems(ch)))
        ch, feats, sc = self.copy("fire-below")
        sc["mood"] = "calm"
        self.assertTrue(any("only in a volcanic scene" in p for p in self.problems(ch)))

    def test_the_sahara_scene_shows_the_dunes_and_the_dispute(self):
        _, feats, sc = self.copy("sahara-born")
        self.assertEqual(sc["mood"], "desert-born")
        self.assertIn("chad-dunes", sc["show"])
        self.assertTrue(feats["chad-dunes"]["uncertainty_km"])
        self.assertTrue(sc["disputed"])

    def test_sources_seen_only_through_search_ask_for_a_recheck(self):
        new = ["hofmann-1997", "wiki-cameroon-line", "wiki-biu-plateau", "wiki-mount-cameroon", "nonnotte-2008",
               "wiki-nyiragongo", "usgs-nyiragongo", "schuster-2006", "nature-news-sahara-2014", "wiki-places-volcanoes"]
        for sid in new:
            self.assertIn("Re-check", self.sources[sid]["checked"], sid)
            self.assertIn("Not opened", self.sources[sid]["checked"], sid)


class PacingTests(unittest.TestCase):
    def test_reading_time_is_shorter_but_never_under_eight_seconds(self):
        self.assertEqual(bh.reading_seconds("one two"), 8)
        self.assertEqual(bh.reading_seconds(" ".join(["w"] * 100)), 33)

    def test_hand_timed_scenes_keep_an_explicit_duration(self):
        for cid in bh.CHAPTERS:
            ch = bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", cid + ".json"))
            for sc in ch["scenes"]:
                if any(k in sc for k in ("beats", "appear", "camera_path", "fade")):
                    self.assertIn("duration", sc, f"{cid}/{sc['id']}")

    def test_the_template_reveals_narration_over_three_quarters_of_a_scene(self):
        with open(os.path.join(bh.HISTORY_DIR, "template.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertIn("const NARRATE = 0.75;", page)
        self.assertNotIn("* .55 /", page)
        self.assertNotIn("*.55/", page)


if __name__ == "__main__":
    unittest.main()

"""Tests for build_history.py. Run from the repository folder:

    python -m unittest discover -s tests
"""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_history as bh  # noqa: E402


def load():
    sources = bh.read_json(bh.SOURCES_PATH)
    chapters = [bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", f"{c}.json")) for c in bh.CHAPTERS]
    return chapters, sources


class HistoryDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states, cls.arcs, cls.users = bh.load_states()
        cls.chapters, cls.sources = load()

    def chapter(self, cid):
        return copy.deepcopy(next(c for c in self.chapters if c["id"] == cid))

    def problems_with(self, chapters):
        return bh.check(chapters, self.sources, self.states)

    def test_real_data_passes(self):
        self.assertEqual(self.problems_with(self.chapters), [])

    def test_borders_have_37_areas(self):
        self.assertEqual(len(self.states), 37)          # 36 states and the FCT
        for users in self.users:
            self.assertIn(len(users), (1, 2))           # a border line has one state (coast/frontier) or two

    def test_unknown_source_is_caught(self):
        nok = self.chapter("nok")
        nok["scenes"][0]["sources"] = ["no-such-source"]
        self.assertTrue(any("unknown source" in p for p in self.problems_with([nok])))

    def test_point_outside_nigeria_is_caught(self):
        nok = self.chapter("nok")
        nok["features"][1]["coordinates"] = [51.5, -0.1]     # London
        self.assertTrue(any("outside Nigeria" in p for p in self.problems_with([nok])))

    def test_state_placed_twice_is_caught(self):
        states = self.chapter("states")
        states["snapshots"]["1967"]["groups"][0]["members"].append("NG-KN")
        found = self.problems_with([states])
        self.assertTrue(any("NG-KN" in p and "2 times" in p for p in found))

    def test_wrong_count_is_caught(self):
        states = self.chapter("states")
        states["snapshots"]["1991"]["count"] = 31
        self.assertTrue(any("count says 31" in p for p in self.problems_with([states])))

    def test_parent_must_exist_in_previous_snapshot(self):
        states = self.chapter("states")
        states["snapshots"]["1976"]["groups"][0]["from"] = "Atlantis"
        self.assertTrue(any("Atlantis" in p for p in self.problems_with([states])))

    def test_disputed_must_be_stated(self):
        nok = self.chapter("nok")
        del nok["features"][0]["disputed"]
        self.assertTrue(any("disputed" in p for p in self.problems_with([nok])))

    def test_bce_years_and_order(self):
        nok = self.chapter("nok")
        nok["scenes"][1]["when"] = {"from": -900, "to": -1500, "label": "backwards"}
        self.assertTrue(any("from <= to" in p for p in self.problems_with([nok])))

    def test_effects_are_checked(self):
        states = self.chapter("states")
        scene = next(s for s in states["scenes"] if s["id"] == "1991")
        scene["effects"] = [{"type": "arc", "from": [6.4, 3.4], "to": [51.5, -0.1], "from_label": "Lagos",
                             "to_label": "London", "at": 0.5}]
        self.assertTrue(any("arc to" in p for p in self.problems_with([states])))
        scene["effects"] = [{"type": "pulse", "state": "NG-FC", "at": 1.5}]
        self.assertTrue(any("between 0 and 1" in p for p in self.problems_with([states])))

    def test_mood_and_shatter_are_checked(self):
        nok = self.chapter("nok")
        scene = next(s for s in nok["scenes"] if s["id"] == "terracottas")
        scene["mood"] = "party"
        scene["effects"] = [{"type": "shatter", "features": ["taruga"], "at": 0.2}]   # Taruga is not shown here
        found = self.problems_with([nok])
        self.assertTrue(any("mood must be one of" in p for p in found))
        self.assertTrue(any("shatter needs features" in p for p in found))

    def test_outlines_follow_the_snapshot(self):
        data = bh.page_data(self.chapters, self.sources, self.states, self.arcs, self.users)
        snaps = next(c for c in data["chapters"] if c["id"] == "states")["snapshots"]
        between = [i for i, u in enumerate(self.users) if sorted(u) == ["NG-KN", "NG-KT"]]
        self.assertTrue(between)
        # Kano and Katsina were both in the Northern Region, but separate states by 1987
        self.assertFalse(set(between) & set(snaps["1963"]["thick"]))
        self.assertTrue(set(between) <= set(snaps["1987"]["thick"]))
        # In 1996 every border between two states is a border between states at that date
        self.assertEqual(len(snaps["1996"]["thick"]), len(self.arcs))

    def test_children_keep_their_parents_hue(self):
        states = self.chapter("states")
        colours = bh.snapshot_colours(states["snapshots"])
        self.assertEqual(colours["1976"]["Kano"], colours["1967"]["Kano"])
        self.assertNotEqual(colours["1991"]["Jigawa"], colours["1991"]["Kano"])

    def test_page_is_built_with_credits_and_text_version(self):
        page, data = bh.build()
        for must in ("Unreviewed draft", "GRID3", "geoBoundaries", "CC BY 4.0", "Text version"):
            self.assertIn(must, page)
        for ch in data["chapters"]:
            for sc in ch["scenes"]:
                self.assertIn(sc["title"].replace("'", "&#x27;"), page)
        self.assertNotIn("{{", page)


if __name__ == "__main__":
    unittest.main()

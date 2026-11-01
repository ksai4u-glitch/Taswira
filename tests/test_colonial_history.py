"""Tests for the colonial chapter: Lagos and the protectorates, conquest and resistance, the
railways and ports, amalgamation and independence (1861 to 1960). Run from the repository folder:

    python -m unittest discover -s tests
"""

import copy
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_history as bh  # noqa: E402


class ColonialChapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states, _, _ = bh.load_states()
        cls.sources = bh.read_json(bh.SOURCES_PATH)
        cls.emblems = bh.read_json(os.path.join(bh.HISTORY_DIR, "emblems.json"))
        cls.ch = bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", "colonial.json"))

    def problems(self, ch):
        return bh.check([ch], self.sources, self.states, set(), self.emblems)

    def copy(self, scene=None):
        ch = copy.deepcopy(self.ch)
        feats = {f["id"]: f for f in ch["features"]}
        sc = next(s for s in ch["scenes"] if s["id"] == scene) if scene else None
        return ch, feats, sc

    def test_chapter_sits_between_sokoto_and_the_states_and_passes(self):
        self.assertEqual(bh.CHAPTERS.index("colonial"), bh.CHAPTERS.index("sokoto") + 1)
        self.assertEqual(bh.CHAPTERS.index("states"), bh.CHAPTERS.index("colonial") + 1)
        self.assertEqual(self.problems(copy.deepcopy(self.ch)), [])

    def test_scenes_and_beats_run_forward_in_time(self):
        ids = [s["id"] for s in self.ch["scenes"]]
        self.assertEqual(ids, ["lagos-1861", "resistance", "rail-north", "coal-port", "one-colony", "network"])
        for sc in self.ch["scenes"]:
            years = [b["when"]["from"] for b in sc["beats"]]
            self.assertEqual(years, sorted(years), sc["id"])
            self.assertEqual(sc["text"], " ".join(b["text"] for b in sc["beats"]), sc["id"])
            self.assertFalse(re.search(r"\d\.\d", sc["text"]), "a decimal point would split a caption")
        self.assertEqual(self.ch["scenes"][-1]["beats"][-1]["when"]["label"], "1 October 1960")

    def test_railways_carry_their_opening_dates(self):
        rails = [f for f in self.ch["features"] if f.get("type") == "railway"]
        self.assertEqual(len(rails), 7)
        for f in rails:
            self.assertLessEqual(f["opened"]["from"], f["opened"]["to"])
            self.assertIn("schematic", f["location"])
        feats = {f["id"]: f for f in rails}
        self.assertEqual(feats["rail-lagos-ibadan"]["opened"]["from"], 1896)
        self.assertEqual(feats["rail-eastern"]["opened"], {"from": 1913, "to": 1916, "label": "built 1913 to 1916"})
        self.assertEqual(feats["rail-ibadan-minna"]["status"], "disputed", "Jebba is dated 1911 or 1916")

    def test_the_jebba_crossing_is_marked_as_differing(self):
        _, _, sc = self.copy("rail-north")
        last = sc["beats"][-1]["when"]
        self.assertEqual(last["basis"], "differ")
        self.assertIn("differ", last["label"])

    def test_conquest_is_told_calmly(self):
        _, _, sc = self.copy("resistance")
        self.assertTrue(sc["sensitive"])
        self.assertEqual(sc["mood"], "calm")
        self.assertTrue(all(b["pose"] == 7 for b in sc["beats"]))
        self.assertNotIn("erupt", sc)

    def test_ports_point_out_to_sea(self):
        ports = [f for f in self.ch["features"] if f.get("form") == "port"]
        self.assertEqual({f["id"] for f in ports}, {"lagos", "calabar", "baro", "port-harcourt"})
        for f in ports:
            if "seaward" in f:
                self.assertLess(f["seaward"][0], f["coordinates"][0], f"{f['id']}: the sea lies to the south")

    def test_new_checks_refuse_bad_railways_and_ports(self):
        ch, feats, _ = self.copy()
        del feats["rail-nguru"]["opened"]
        self.assertTrue(any("a railway needs opened" in p for p in self.problems(ch)))
        ch, feats, _ = self.copy()
        feats["kano"]["seaward"] = [4.0, 7.0]
        self.assertTrue(any("seaward" in p for p in self.problems(ch)))
        ch, feats, sc = self.copy("coal-port")
        sc["appear"]["rail-eastern"] = 99
        self.assertTrue(any("appear needs" in p for p in self.problems(ch)))

    def test_the_british_warship_comes_only_where_a_source_says_so(self):
        _, _, sc = self.copy("lagos-1861")
        self.assertEqual(sc["warships"], ["lagos"])
        self.assertIn("British naval force entered Lagos", sc["beats"][0]["text"])
        others = [s["id"] for s in self.ch["scenes"] if s.get("warships") and s["id"] != "lagos-1861"]
        self.assertEqual(others, [])
        ch, feats, sc = self.copy("lagos-1861")
        sc["warships"] = ["lokoja"]
        self.assertTrue(any("warships sail into shown ports" in p for p in self.problems(ch)))
        ch, feats, sc = self.copy("resistance")
        sc["warships"] = ["benin-city"]
        self.assertTrue(any("warships sail into shown ports" in p for p in self.problems(ch)))

    def test_every_source_was_opened(self):
        cited = {s for f in self.ch["features"] for s in f["sources"]} | {s for sc in self.ch["scenes"] for s in sc["sources"]}
        new = [s for s in cited if self.sources[s]["checked"].startswith("Opened 1 Nov 2026")]
        self.assertGreaterEqual(len(new), 20)
        for sid in cited:
            self.assertNotIn("Not opened", self.sources[sid]["checked"], sid)

    def test_the_coal_ties_back_to_deep_time(self):
        deep = bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", "deep.json"))
        coal = next(f for f in deep["features"] if f["id"] == "enugu-coal")
        self.assertIn("Udi", coal["what"])
        _, feats, sc = self.copy("coal-port")
        self.assertIn("70 million years", sc["beats"][0]["text"])
        self.assertIn("Udi", sc["beats"][0]["text"])


if __name__ == "__main__":
    unittest.main()

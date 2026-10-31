"""Tests for the Sokoto Caliphate chapter: the jihad, the emirates and the conquest of 1903.
Run from the repository folder:

    python -m unittest discover -s tests
"""

import copy
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_history as bh  # noqa: E402


class SokotoChapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states, _, _ = bh.load_states()
        cls.sources = bh.read_json(bh.SOURCES_PATH)
        cls.emblems = bh.read_json(os.path.join(bh.HISTORY_DIR, "emblems.json"))
        cls.sokoto = bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", "sokoto.json"))

    def problems(self, ch):
        return bh.check([ch], self.sources, self.states, set(), self.emblems)

    def copy(self, scene=None):
        ch = copy.deepcopy(self.sokoto)
        feats = {f["id"]: f for f in ch["features"]}
        sc = next(s for s in ch["scenes"] if s["id"] == scene) if scene else None
        return ch, feats, sc

    def test_chapter_follows_hausa_and_passes_the_checks(self):
        self.assertEqual(bh.CHAPTERS.index("sokoto"), bh.CHAPTERS.index("hausa") + 1)
        self.assertEqual(bh.CHAPTERS.index("states"), bh.CHAPTERS.index("sokoto") + 1)
        self.assertEqual(self.problems(copy.deepcopy(self.sokoto)), [])
        self.assertFalse(self.sokoto.get("reference", False), "the chapter is part of the film, not reference")

    def test_scenes_run_in_order_from_the_jihad_to_the_conquest(self):
        scenes = self.sokoto["scenes"]
        self.assertEqual([s["id"] for s in scenes], ["jihad", "emirates", "conquest"])
        years = [(s["when"]["from"], s["when"]["to"]) for s in scenes]
        self.assertEqual(years, sorted(years))
        self.assertEqual(scenes[-1]["when"]["to"], 1903)

    def test_every_feature_and_scene_cites_known_sources(self):
        for item in self.sokoto["features"] + self.sokoto["scenes"]:
            self.assertTrue(item["sources"], item["id"])
            for sid in item["sources"]:
                self.assertIn(sid, self.sources, f"{item['id']}: {sid}")
                self.assertTrue(self.sources[sid]["checked"], sid)

    def test_new_sources_say_how_they_were_seen(self):
        # Pages that could only be seen through search results say so, and ask for a re-check
        for sid, s in self.sources.items():
            if "2026-10-31" in s.get("year", "") and "search" in s["checked"]:
                self.assertRegex(s["checked"], r"(Re-check|Check|check)", sid)

    def test_violence_and_slavery_are_solemn(self):
        for sc in self.sokoto["scenes"]:
            self.assertTrue(sc["sensitive"], sc["id"])
            for beat in sc.get("beats", []):
                if re.search(r"\b(war|army|fell|killed|captured|enslaved|rose against|defeated)\b", beat["text"]):
                    self.assertEqual(beat["pose"], 7, beat["text"])

    def test_dated_beats_say_where_their_dates_come_from(self):
        for sid in ("jihad", "emirates"):
            sc = next(s for s in self.sokoto["scenes"] if s["id"] == sid)
            for beat in sc["beats"]:
                self.assertIn(beat["when"]["basis"], ("record", "differ"), beat["text"])
                self.assertRegex(beat["when"]["label"], r"\d{4}")

    def test_record_basis_is_known_and_others_still_checked(self):
        self.assertIn("record", bh.BEAT_BASES)
        ch, _, sc = self.copy("jihad")
        sc["beats"][1]["when"]["basis"] = "rumour"
        self.assertTrue(any("when.basis must be one of" in p for p in self.problems(ch)))
        ch, _, sc = self.copy("emirates")
        ilorin = next(b for b in sc["beats"] if "Ilorin" in b["text"])
        ilorin["when"]["label"] = "1823–1824"
        self.assertTrue(any("sources differ" in p for p in self.problems(ch)))

    def test_beats_do_not_go_back_in_time(self):
        ch, _, sc = self.copy("emirates")
        sc["beats"][-1]["when"].update({"from": 1813, "to": 1813})
        self.assertTrue(any("must not go back in time" in p for p in self.problems(ch)))

    def test_places_wait_for_their_dates(self):
        # Each emirate and the caliph's seat appear under the beat that dates them, never before
        ch, _, sc = self.copy("jihad")
        for fid, year in (("zaria", 1805), ("kano", 1807), ("sokoto", 1809)):
            shown = bh.beat_in_force(sc["beats"], sc["appear"][fid])["when"]
            self.assertGreaterEqual(shown["from"], year, fid)
        shown = bh.beat_in_force(sc["beats"], sc["fade"]["alkalawa"])["when"]
        self.assertEqual(shown["from"], 1808, "Alkalawa fades only after it falls")
        sc = next(s for s in ch["scenes"] if s["id"] == "emirates")
        self.assertGreaterEqual(bh.beat_in_force(sc["beats"], sc["appear"]["yola"])["when"]["from"], 1841)
        self.assertGreaterEqual(bh.beat_in_force(sc["beats"], sc["appear"]["ilorin"])["when"]["from"], 1823)

    def test_caliphate_drawn_as_seats_and_ties_not_a_border(self):
        feats = {f["id"]: f for f in self.sokoto["features"]}
        self.assertEqual({fid for fid, f in feats.items() if f.get("form") == "caliphate"}, {"sokoto", "gwandu"})
        for fid, f in feats.items():
            self.assertNotEqual(f.get("form"), "kingdom", fid)
            self.assertNotIn("reach_km", f, f"{fid}: no halo claims how far an emir ruled")
            if f["kind"] == "link":
                self.assertEqual(f["type"], "allegiance", fid)
                self.assertIn(f["to"], ("sokoto", "gwandu"), fid)
        self.assertFalse(self.sokoto.get("snapshots"), "no state snapshot or border for the caliphate")
        self.assertEqual(feats["ilorin-gwandu"]["to"], "gwandu", "Ilorin answered through Gwandu")

    def test_no_flag_is_invented(self):
        emblem = self.emblems["sokoto-caliphate"]
        self.assertEqual(emblem["tier"], "none")
        self.assertIsNone(emblem["drawing"])
        for f in self.sokoto["features"]:
            self.assertIn(f.get("emblem"), (None, "sokoto-caliphate"), f["id"])

    def test_uncertain_places_say_so(self):
        feats = {f["id"]: f for f in self.sokoto["features"]}
        self.assertEqual(feats["degel"]["status"], "approx")
        self.assertGreaterEqual(feats["degel"]["uncertainty_km"], 10)
        for fid in ("bauchi", "ilorin", "bida", "rnc-1897", "conquest-1903"):
            self.assertEqual(feats[fid]["status"], "disputed", fid)
            self.assertTrue(feats[fid]["disputed"], fid)
        # Places with no checked position are told, not drawn
        for missing in ("gudu", "burmi", "kwatto", "tabkin-kwatto"):
            self.assertNotIn(missing, feats)

    def test_conquest_marks_each_town_on_its_date(self):
        ch, feats, sc = self.copy("conquest")
        self.assertEqual(set(sc["control"].values()), {"taken"})
        reached = {pid for m in ("rnc-1897", "conquest-1903") for pid in feats[m]["path"]}
        self.assertEqual(set(sc["control"]), reached)
        self.assertEqual(feats["conquest-1903"]["stops"]["kano"]["date"], "1903-02-03")
        self.assertEqual(feats["conquest-1903"]["stops"]["sokoto"]["date"], "1903-03-15")
        clock = bh.campaign_clock(sc, feats, sc["duration"])
        self.assertEqual([round(k[1]) for k in clock["knots"]][0], 1897)
        # A town taken with no campaign reaching it stops the build
        sc["control"]["gwandu"] = "taken"
        sc["show"].append("gwandu")
        self.assertTrue(any("no campaign in the scene reaches it" in p for p in self.problems(ch)))

    def test_disputed_dates_are_named(self):
        conquest = next(s for s in self.sokoto["scenes"] if s["id"] == "conquest")
        for words in ("13 March", "27 July", "25 or 29 January", "Burmi itself is not placed"):
            self.assertIn(words, conquest["disputed"])
        jihad = next(s for s in self.sokoto["scenes"] if s["id"] == "jihad")
        self.assertIn("no place is drawn", jihad["text"])

    def test_notes_are_dated_and_short(self):
        for sc in self.sokoto["scenes"]:
            for n in sc.get("notes", []):
                self.assertLessEqual(len(n["text"]), 40)
                self.assertFalse(n.get("oral"), "this chapter has no oral-tradition beats")

    def test_text_version(self):
        text = bh.transcript([self.sokoto], self.sources, self.states, self.emblems)
        self.assertIn("<em>3 October 1808.</em>", text)
        self.assertIn("<em>1823–1824 · sources differ.</em>", text)
        self.assertIn("Alkalawa", text)
        self.assertIn("Burmi", text)


if __name__ == "__main__":
    unittest.main()

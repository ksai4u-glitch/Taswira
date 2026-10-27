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
        cls.background = bh.load_background()
        cls.chapters, cls.sources = load()
        cls.emblems = bh.load_emblems()

    def chapter(self, cid):
        return copy.deepcopy(next(c for c in self.chapters if c["id"] == cid))

    def problems_with(self, chapters, emblems=None):
        return bh.check(chapters, self.sources, self.states, set(), emblems or self.emblems)

    def emblem_problems(self, emblems):
        return bh.check_emblems(emblems, self.sources, set())

    def test_real_data_passes(self):
        self.assertEqual(self.problems_with(self.chapters), [])
        self.assertEqual(self.emblem_problems(self.emblems), [])

    def test_borders_have_37_areas(self):
        self.assertEqual(len(self.states), 37)          # 36 states and the FCT
        for users in self.users:
            self.assertIn(len(users), (1, 2))           # a border line has one state (coast/frontier) or two

    def test_unknown_source_is_caught(self):
        nok = self.chapter("nok")
        nok["scenes"][0]["sources"] = ["no-such-source"]
        self.assertTrue(any("unknown source" in p for p in self.problems_with([nok])))

    def test_point_outside_the_map_is_caught(self):
        nok = self.chapter("nok")
        nok["features"][1]["coordinates"] = [51.5, -0.1]     # London
        self.assertTrue(any("outside the map area" in p for p in self.problems_with([nok])))

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

    # --- The map vocabulary: status, emblems, links, moves and control ---------------

    def test_every_feature_has_a_status(self):
        nok = self.chapter("nok")
        del nok["features"][0]["status"]
        self.assertTrue(any("status must be one of" in p for p in self.problems_with([nok])))

    def test_status_is_disputed_exactly_when_disputed_is_explained(self):
        key = self.chapter("key")
        daura = next(f for f in key["features"] if f["id"] == "daura")
        daura["status"] = "disputed"                       # but disputed is still null
        self.assertTrue(any("key/daura: status must be 'disputed'" in p for p in self.problems_with([key])))
        emblems = copy.deepcopy(self.emblems)
        emblems["biafra"]["disputed"] = "Someone disagrees."   # but status is still firm
        self.assertTrue(any("emblem biafra: status" in p for p in self.emblem_problems(emblems)))

    def test_a_flag_or_symbol_needs_a_source(self):
        emblems = copy.deepcopy(self.emblems)
        emblems["benin-leopard"]["sources"] = []
        self.assertTrue(any("emblem benin-leopard: a symbol needs a source" in p
                            for p in self.emblem_problems(emblems)))

    def test_nothing_is_drawn_when_nothing_is_documented(self):
        emblems = copy.deepcopy(self.emblems)
        emblems["sokoto-caliphate"]["drawing"] = "leopard"
        self.assertTrue(any("nothing may be drawn" in p for p in self.emblem_problems(emblems)))
        emblems = copy.deepcopy(self.emblems)
        emblems["aro"]["note"] = None
        self.assertTrue(any("emblem aro: say what was looked for" in p for p in self.emblem_problems(emblems)))

    def test_drawings_are_plain_shapes(self):
        self.assertTrue(self.emblems["benin-leopard"]["svg"].startswith("<svg"))
        emblems = copy.deepcopy(self.emblems)
        emblems["benin-leopard"]["svg"] = '<svg onload="alert(1)"><path d="M0 0"/></svg>'
        self.assertTrue(any("plain shapes" in p for p in self.emblem_problems(emblems)))
        emblems["benin-leopard"]["svg"] = None             # the drawing file is missing
        self.assertTrue(any("no drawing" in p for p in self.emblem_problems(emblems)))

    def test_unknown_emblem_is_caught(self):
        key = self.chapter("key")
        next(f for f in key["features"] if f["id"] == "edo")["emblem"] = "no-such-emblem"
        self.assertTrue(any("unknown emblem" in p for p in self.problems_with([key])))

    def test_emblem_must_fit_the_scene_years(self):
        key = self.chapter("key")
        # The Royal Niger Company's flag (1887 to 1899) on Kano in the 15th-century scene
        next(f for f in key["features"] if f["id"] == "kano")["emblem"] = "royal-niger-company"
        self.assertTrue(any("scene hausa: shows the royal-niger-company emblem outside its documented years" in p
                            for p in self.problems_with([key])))

    def test_unchecked_items_need_the_scene_to_say_so(self):
        key = self.chapter("key")
        next(f for f in key["features"] if f["id"] == "daura")["status"] = "to-check"
        self.assertTrue(any("scene hausa: shows daura, still marked to-check" in p
                            for p in self.problems_with([key])))
        next(s for s in key["scenes"] if s["id"] == "hausa")["unchecked"] = "Daura's place is not yet checked."
        self.assertEqual(self.problems_with([key]), [])

    def test_unchecked_emblem_needs_the_scene_to_say_so(self):
        emblems = copy.deepcopy(self.emblems)
        emblems["benin-leopard"]["status"] = "to-check"
        found = self.problems_with([self.chapter("key")], emblems)
        self.assertTrue(any("scene benin: shows benin-leopard, still marked to-check" in p for p in found))

    def test_a_link_shows_both_its_places(self):
        key = self.chapter("key")
        next(s for s in key["scenes"] if s["id"] == "hausa")["show"].remove("ngazargamu")
        self.assertTrue(any("kano-tribute joins ngazargamu, which the scene does not show" in p
                            for p in self.problems_with([key])))

    def test_links_and_moves_join_places_in_the_chapter(self):
        key = self.chapter("key")
        next(f for f in key["features"] if f["id"] == "kano-tribute")["to"] = "timbuktu"
        next(f for f in key["features"] if f["id"] == "conquest-1903")["dates"]["lokoja"] = "1900"
        found = self.problems_with([key])
        self.assertTrue(any("'timbuktu' is not a place in this chapter" in p for p in found))
        self.assertTrue(any("a date for 'lokoja', which is not on the path" in p for p in found))

    def test_taken_needs_a_campaign_that_reaches_the_place(self):
        key = self.chapter("key")
        next(s for s in key["scenes"] if s["id"] == "taken")["show"].remove("conquest-1903")
        self.assertTrue(any("sokoto is taken, but no campaign in the scene reaches it" in p
                            for p in self.problems_with([key])))

    def test_vocabulary_values_are_checked(self):
        key = self.chapter("key")
        next(f for f in key["features"] if f["id"] == "edo")["form"] = "empire"
        next(f for f in key["features"] if f["id"] == "kano-tribute")["type"] = "friendship"
        next(f for f in key["features"] if f["id"] == "fulani-east")["period"] = None
        next(s for s in key["scenes"] if s["id"] == "claimed")["control"]["sokoto"] = "owned"
        found = self.problems_with([key])
        for message in ("form must be one of", "type must be one of", "a migration needs a period",
                        "control must be one of"):
            self.assertTrue(any(message in p for p in found), message)

    def test_a_halo_says_what_its_size_rests_on(self):
        key = self.chapter("key")
        next(f for f in key["features"] if f["id"] == "edo")["reach_note"] = None
        self.assertTrue(any("key/edo: a halo or field needs reach_km" in p for p in self.problems_with([key])))

    def test_short_name_is_shorter(self):
        nok = self.chapter("nok")
        nok["features"][0]["short"] = nok["features"][0]["name"] + " and more"
        self.assertTrue(any("short must be a shorter name" in p for p in self.problems_with([nok])))

    def test_emblem_years_overlap(self):
        e = self.emblems["royal-niger-company"]           # 1887 to 1899
        self.assertTrue(bh.emblem_fits(e, {"from": 1899, "to": 1903}))
        self.assertFalse(bh.emblem_fits(e, {"from": 1900, "to": 1903}))
        self.assertTrue(bh.emblem_fits(self.emblems["nigeria-1960"], {"from": 1996, "to": 1996}))   # no end year

    def test_outlines_follow_the_snapshot(self):
        data = bh.page_data(self.chapters, self.sources, self.states, self.arcs, self.users, self.background)
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

    def test_scenes_before_1914_get_the_period_background(self):
        data = bh.page_data(self.chapters, self.sources, self.states, self.arcs, self.users, self.background)
        bases = {sc["id"]: sc["base"] for ch in data["chapters"] for sc in ch["scenes"]}
        for ancient in ("where", "farmers", "terracottas", "iron", "decline"):
            self.assertEqual(bases[ancient], "period")   # Nok before 1 CE: never on today's map
        self.assertEqual(bases["rediscovery"], "modern")  # the digs of 1928 to 2021 happened in today's Nigeria
        self.assertEqual(bases["1963"], "modern")
        self.assertEqual(bh.base_for({"when": {"from": 1913}}), "period")
        self.assertEqual(bh.base_for({"when": {"from": 1914}}), "modern")

    def test_background_is_land_lakes_and_rivers_only(self):
        self.assertEqual(set(self.background), {"land", "lakes", "rivers"})
        # Lagos lagoon sits at about 6.5 N, 3.4 E: the first point of some land ring is near Nigeria
        firsts = [(r[0][0] / 1000, r[0][1] / 1000) for r in self.background["land"]]
        self.assertTrue(any(-5 < lat < 25 and -20 < lon < 30 for lat, lon in firsts))
        # Kainji Reservoir (1968) must not be drawn as a lake
        for poly in self.background["lakes"]:
            lat, lon = poly[0][0] / 1000, poly[0][1] / 1000
            self.assertFalse(9.8 < lat < 10.6 and 4.3 < lon < 4.8, "Kainji Reservoir is in the background")

    def test_page_has_no_modern_place_name_layer(self):
        with open(bh.TEMPLATE_PATH, encoding="utf-8") as f:
            self.assertNotIn("World_Dark_Gray_Reference", f.read())

    def test_page_is_built_with_credits_and_text_version(self):
        page, data = bh.build()
        for must in ("Unreviewed draft", "GRID3", "geoBoundaries", "CC BY 4.0", "Natural Earth", "Text version",
                     "Flags, emblems and symbols", "Nothing documented"):
            self.assertIn(must, page)
        self.assertEqual(set(data["emblems"]), set(self.emblems))
        for ch in data["chapters"]:
            for sc in ch["scenes"]:
                self.assertIn(sc["title"].replace("'", "&#x27;"), page)
        self.assertNotIn("{{", page)


if __name__ == "__main__":
    unittest.main()

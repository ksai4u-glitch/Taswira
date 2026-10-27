"""Tests for the Hausa cities chapter: dated city parts, dated beats and oral tradition.
Run from the repository folder:

    python -m unittest discover -s tests
"""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_history as bh  # noqa: E402


class HausaChapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states, _, _ = bh.load_states()
        cls.sources = bh.read_json(bh.SOURCES_PATH)
        cls.hausa = bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", "hausa.json"))

    def problems(self, ch):
        return bh.check([ch], self.sources, self.states, set())

    def kano(self):
        ch = copy.deepcopy(self.hausa)
        sc = next(s for s in ch["scenes"] if s["id"] == "kano")
        city = next(f for f in ch["features"] if f["id"] == "kano-city")
        return ch, sc, {p["id"]: p for p in city["monument"]["parts"]}

    def test_chapter_follows_nok(self):
        self.assertEqual(bh.CHAPTERS.index("hausa"), bh.CHAPTERS.index("nok") + 1)
        self.assertEqual(self.problems(copy.deepcopy(self.hausa)), [])

    def test_every_dated_part_waits_for_its_date(self):
        ch, sc, parts = self.kano()
        for part in parts.values():
            if "year" in part:
                shown = bh.beat_in_force(sc["beats"], part["at"])["when"]
                self.assertGreaterEqual(shown["from"], part["year"], part["id"])

    def test_part_before_its_date_is_caught(self):
        ch, sc, parts = self.kano()
        parts["palace"]["at"] = 17          # Rumfa's palace during the 12th/14th-century wall beat
        self.assertTrue(any("palace appears at 17 s" in p and "before its date (1463)" in p for p in self.problems(ch)))

    def test_chronicle_date_must_say_so(self):
        ch, sc, _ = self.kano()
        sc["beats"][2]["when"]["label"] = "1095–1134"
        self.assertTrue(any("must say so in its label" in p for p in self.problems(ch)))

    def test_disputed_date_must_say_sources_differ(self):
        ch, sc, _ = self.kano()
        sc["beats"][3]["when"]["label"] = "About 1136"
        self.assertTrue(any("sources differ" in p for p in self.problems(ch)))

    def test_oral_tradition_has_no_date(self):
        ch, sc, _ = self.kano()
        sc["beats"][1]["when"]["label"] = "Oral tradition · about 900"
        self.assertTrue(any("no date" in p for p in self.problems(ch)))
        ch, sc, _ = self.kano()
        sc["beats"][1]["when"]["from"] = 900
        self.assertTrue(any("no date" in p for p in self.problems(ch)))

    def test_oral_tradition_leaves_before_the_next_dated_beat(self):
        ch, sc, parts = self.kano()
        parts["tradition"]["until"] = 12
        self.assertTrue(any("must leave before the next dated beat" in p for p in self.problems(ch)))
        ch, sc, parts = self.kano()
        parts["tradition"]["at"] = 11
        self.assertTrue(any("appears during a dated beat" in p for p in self.problems(ch)))

    def test_dated_part_never_appears_in_an_oral_beat(self):
        ch, sc, parts = self.kano()
        parts["first-wall"]["at"] = 6
        self.assertTrue(any("first-wall appears at 6 s" in p for p in self.problems(ch)))

    def test_part_needs_exactly_one_kind_of_date(self):
        ch, sc, parts = self.kano()
        parts["first-wall"]["oral"] = True
        self.assertTrue(any("exactly one" in p for p in self.problems(ch)))
        ch, sc, parts = self.kano()
        del parts["kurmi"]["year"]
        self.assertTrue(any("exactly one" in p for p in self.problems(ch)))

    def test_dated_beats_do_not_go_back_in_time(self):
        ch, sc, _ = self.kano()
        sc["beats"][4]["when"] = dict(sc["beats"][4]["when"], **{"from": 1100, "to": 1110})
        self.assertTrue(any("must not go back in time" in p for p in self.problems(ch)))

    def test_every_beat_is_dated_when_one_is(self):
        ch, sc, _ = self.kano()
        del sc["beats"][5]["when"]
        self.assertTrue(any("every beat needs a when" in p for p in self.problems(ch)))

    def test_appear_needs_a_shown_place(self):
        ch, sc, _ = self.kano()
        sc["appear"] = {"zazzau": 40}
        self.assertTrue(any("appear needs places the scene shows" in p for p in self.problems(ch)))

    def test_nothing_later_is_drawn(self):
        # No mosque, minaret, emblem or bridge, and no part dated after Rumfa's reign
        ch, sc, parts = self.kano()
        city = next(f for f in ch["features"] if f["id"] == "kano-city")
        self.assertNotIn("emblem", city)
        self.assertFalse([p for p in parts if any(w in p for w in ("mosque", "minaret", "bridge", "flag"))])
        self.assertLessEqual(max(p.get("year", 0) for p in parts.values()), 1499)

    def test_text_version_dates_each_beat_and_part(self):
        text = bh.transcript([self.hausa], self.sources, self.states)
        self.assertIn("<em>Oral tradition · no date.</em>", text)
        self.assertIn("<em>1095–1134 · Kano Chronicle reckoning.</em>", text)
        self.assertIn("What appears when:", text)
        self.assertIn("position schematic", text)


class KanoPeopleTests(unittest.TestCase):
    """The second Kano scene carries on from the first city (monument "base")."""

    @classmethod
    def setUpClass(cls):
        cls.states, _, _ = bh.load_states()
        cls.sources = bh.read_json(bh.SOURCES_PATH)
        cls.hausa = bh.read_json(os.path.join(bh.HISTORY_DIR, "chapters", "hausa.json"))

    def problems(self, ch):
        return bh.check([ch], self.sources, self.states, set())

    def life(self):
        ch = copy.deepcopy(self.hausa)
        sc = next(s for s in ch["scenes"] if s["id"] == "kano-people")
        city = next(f for f in ch["features"] if f["id"] == "kano-life")
        return ch, sc, city["monument"], {p["id"]: p for p in city["monument"]["parts"]}

    def expanded(self, ch):
        city = next(f for f in bh.expand_bases([ch])[0]["features"] if f["id"] == "kano-life")
        return {p["id"]: p for p in city["monument"]["parts"]}

    def test_starts_from_the_city_as_it_stood(self):
        ch, _, _, _ = self.life()
        parts = self.expanded(ch)
        # The first wall stands from the start; the passing parts of the first scene are gone
        for pid in ("ground", "dala", "dala-iron", "first-wall", "gate-adama", "first-wall-finished"):
            self.assertTrue(parts[pid]["standing"], pid)
            self.assertEqual(parts[pid]["at"], 0, pid)
        self.assertNotIn("tradition", parts)
        self.assertNotIn("first-wall-differs", parts)
        # Rumfa's parts rise again at their own date, keeping their labels and sources
        palace = parts["palace"]
        self.assertNotIn("standing", palace)
        self.assertEqual(palace["year"], 1463)
        self.assertIn("Dakin Rimfa", palace["label"])
        self.assertIn("camels", parts)
        self.assertEqual(self.problems(ch), [])

    def test_files_are_not_changed_by_expanding(self):
        ch, _, _, _ = self.life()
        before = copy.deepcopy(ch)
        once = bh.expand_bases([ch])
        self.assertEqual(ch, before)
        self.assertEqual(bh.expand_bases(once), once)   # the build and the text version may both expand

    def test_later_part_left_standing_is_caught(self):
        ch, _, m, _ = self.life()
        m["parts"] = [p for p in m["parts"] if p["id"] != "palace"]
        self.assertTrue(any("palace appears at 0 s" in p and "before its date (1463)" in p for p in self.problems(ch)))

    def test_passing_part_cannot_return(self):
        ch, _, m, _ = self.life()
        m["parts"].append({"id": "tradition", "at": 2, "until": 3, "oral": True, "label": "x", "sources": ["wiki-dalla-hill"]})
        self.assertTrue(any("tradition passed in the base city and cannot return" in p for p in self.problems(ch)))

    def test_base_must_be_another_city_in_the_same_setting(self):
        for base in ("nowhere", "kano-life", "katsina"):
            ch, _, m, _ = self.life()
            m["base"] = base
            self.assertTrue(any("base must name another city" in p for p in self.problems(ch)), base)
        ch, _, m, _ = self.life()
        m["setting"] = "stone-enclosure"
        self.assertTrue(any("carries on in its base's setting" in p for p in self.problems(ch)))

    def test_account_date_must_say_so(self):
        ch, sc, _, _ = self.life()
        sc["beats"][-1]["when"]["label"] = "1526 · Leo Africanus"
        self.assertTrue(any("from a writer's account must say so" in p for p in self.problems(ch)))

    def test_sensitive_beats_are_solemn(self):
        # Captives, eunuchs and war are told with the still, solemn guide pose
        _, sc, _, _ = self.life()
        for beat in sc["beats"]:
            if any(w in beat["text"] for w in ("captives", "eunuchs", "war ")):
                self.assertEqual(beat["pose"], 7, beat["text"])

    def test_captive_towns_are_a_count_not_places(self):
        _, _, _, parts = self.life()
        towns = parts["captive-towns"]
        self.assertIn("places are not known", towns["label"])
        self.assertIn("until", towns)

    def test_nothing_later_is_drawn(self):
        ch, sc, _, _ = self.life()
        parts = self.expanded(ch)
        self.assertFalse([p for p in parts if any(w in p for w in ("mosque", "minaret", "bridge", "flag"))])
        self.assertLessEqual(max(p.get("year", 0) for p in parts.values()), sc["when"]["to"])

    def test_text_version_lists_only_what_is_new(self):
        text = bh.transcript([self.hausa], self.sources, self.states)
        self.assertIn("<em>1526 · Leo Africanus&#x27;s account; his visit is doubted.</em>", text)
        life = text[text.index("Kano · the people inside"):]
        appears = life[life.index("What appears when:"):]
        self.assertIn("Twenty-one towns of captives", appears)
        self.assertNotIn("First wall begun under Gijimasu", appears[:appears.index("</p>") if "</p>" in appears else None])


if __name__ == "__main__":
    unittest.main()

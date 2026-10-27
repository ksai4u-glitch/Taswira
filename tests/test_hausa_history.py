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


if __name__ == "__main__":
    unittest.main()

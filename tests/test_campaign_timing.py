import unittest

import build_history as bh


class CampaignTimingTests(unittest.TestCase):
    def parse(self, record):
        parser = getattr(bh, "parse_campaign_stop", None)
        self.assertIsNotNone(parser, "Campaign dates need a real parser")
        return parser(record)

    def fixture(self):
        ch = bh.read_json(bh.HISTORY_DIR + "/chapters/key.json")
        campaign = next(f for f in ch["features"] if f["id"] == "conquest-1903")
        campaign.pop("dates", None)
        campaign["stops"] = {
            "zazzau-emirate": {"date": "1901", "precision": "year", "approximate": True, "label": "taken 1901"},
            "kano-emirate": {"date": "1903-02-03", "precision": "day", "label": "3 Feb 1903"},
            "sokoto": {"date": "1903-03-15", "precision": "day", "label": "15 Mar 1903"},
        }
        return ch, campaign, next(s for s in ch["scenes"] if s["id"] == "taken")

    def problems(self, chapter):
        states, _, _ = bh.load_states()
        return bh.check([chapter], bh.read_json(bh.SOURCES_PATH), states, set(), bh.load_emblems(), bh.load_plates())

    def test_year_month_day_precision(self):
        for record, year in [
            ({"date": "1901", "precision": "year", "approximate": True}, 1901),
            ({"date": "1903-02", "precision": "month"}, 1903 + 31 / 365),
            ({"date": "1903-02-03", "precision": "day"}, 1903 + 33 / 365),
            ({"date": "1904-02-29", "precision": "day"}, 1904 + 59 / 366),
        ]:
            with self.subTest(record=record):
                self.assertAlmostEqual(self.parse(record)["year"], year)
        self.assertIn("year only", self.parse({"date": "1901", "precision": "year"})["label"])
        self.assertIn("approx.", self.parse({"date": "1901", "precision": "year", "approximate": True})["label"])

    def test_invalid_dates_and_precision_are_rejected(self):
        for record in [
            {"date": "1903", "precision": []},
            {"date": "1903-02-30", "precision": "day"},
            {"date": "3 Feb 1903", "precision": "day"},
            {"date": "1903-02", "precision": "day"},
            {"date": "1903", "precision": "year", "approximate": "yes"},
        ]:
            with self.subTest(record=record), self.assertRaises(ValueError):
                self.parse(record)

    def test_malformed_stop_mapping_is_a_validation_error(self):
        chapter, campaign, _ = self.fixture()
        campaign["stops"] = ["1901", "1903"]
        self.assertTrue(any("campaign stops must" in p for p in self.problems(chapter)))

    def test_scene_too_short_for_readable_legs_is_rejected(self):
        chapter, _, sc = self.fixture()
        sc["duration"] = 2
        self.assertTrue(any("longer scene duration" in p for p in self.problems(chapter)))

    def test_validator_rejects_missing_or_unparseable_stops(self):
        for value in (None, {"date": "not a date", "precision": "day"}):
            chapter, campaign, _ = self.fixture()
            if value is None:
                del campaign["stops"]["sokoto"]
            else:
                campaign["stops"]["sokoto"] = value
            self.assertTrue(any("stop" in p for p in self.problems(chapter)))

    def test_validator_rejects_out_of_order_stops(self):
        chapter, campaign, _ = self.fixture()
        campaign["stops"]["sokoto"]["date"] = "1903-01-01"
        self.assertTrue(any("chronological order" in p for p in self.problems(chapter)))

    def test_validator_rejects_dates_outside_scene(self):
        chapter, campaign, _ = self.fixture()
        campaign["stops"]["sokoto"]["date"] = "1904-03-15"
        self.assertTrue(any("outside the scene" in p for p in self.problems(chapter)))

    def test_clock_uses_dates_and_reserves_readable_legs(self):
        chapter, _, sc = self.fixture()
        compiler = getattr(bh, "campaign_clock", None)
        self.assertIsNotNone(compiler)
        clock = compiler(sc, {f["id"]: f for f in chapter["features"]}, 30)
        stops = clock["campaigns"]["conquest-1903"]
        long_leg = stops[1]["at"] - stops[0]["at"]
        short_leg = stops[2]["at"] - stops[1]["at"]
        self.assertGreater(long_leg, short_leg)
        self.assertGreaterEqual(short_leg, 1.8)
        self.assertAlmostEqual(stops[1]["year"], 1903 + 33 / 365)
        self.assertAlmostEqual(stops[2]["year"], 1903 + 73 / 365)
        for stop in stops:
            self.assertIn([stop["at"], stop["year"]], clock["knots"])

    def test_equal_dates_hold_the_clock_while_each_leg_remains_readable(self):
        chapter, campaign, sc = self.fixture()
        campaign["stops"]["sokoto"]["date"] = "1903-02-03"
        clock = bh.campaign_clock(sc, {f["id"]: f for f in chapter["features"]}, 30)
        stops = clock["campaigns"]["conquest-1903"]
        self.assertEqual(stops[1]["year"], stops[2]["year"])
        self.assertGreaterEqual(stops[2]["at"] - stops[1]["at"], 1.8 - 1e-9)


if __name__ == "__main__":
    unittest.main()

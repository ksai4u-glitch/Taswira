"""Checks for the globe front door (build_home.py). Run: python -m unittest tests.test_build_home"""
import re
import unittest

import build_home as bh


class FrontDoorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = bh.build("", bh.LIVE_MAP_URL)
        cls.mapped, cls.unmapped = bh.read_events(bh.MAP_PAGE)

    def test_every_placeholder_is_filled(self):
        self.assertEqual(re.findall(r"__[A-Z_]+__", self.page), [])

    def test_credits_ucdp_versions_and_labels_preliminary_data(self):
        stats = bh.summarise(self.mapped, self.unmapped)
        self.assertIn("Uppsala Conflict Data Program", self.page)
        self.assertIn("version " + stats["stable"], self.page)
        for version in stats["candidates"].split(", "):
            self.assertIn(version, self.page)
        self.assertIn("preliminary", self.page.lower())
        self.assertIn("not a live feed", self.page)

    def test_figures_match_the_published_conflict_map(self):
        stats = bh.summarise(self.mapped, self.unmapped)
        self.assertEqual(stats["events"], len(self.mapped) + len(self.unmapped))
        self.assertIn(f'{stats["events"]:,}', self.page)
        self.assertIn(f'{stats["nigeriaDeaths"]:,}', self.page)

    def test_unpublished_history_map_is_not_linked(self):
        self.assertIn('data-history="draft"', self.page)
        self.assertNotIn("history.html", self.page)
        self.assertIn('data-history="ready"', bh.build("history.html", bh.LIVE_MAP_URL))

    def test_nigeria_dots_fall_inside_nigeria(self):
        land, lakes, _ = bh.load_background()
        dots = bh.dot_layer(bh.NIGERIA_SPACING, bh.NIGERIA_BOX, bh.load_nigeria(), lakes)
        self.assertGreater(len(dots), 1000)
        lats, lons = dots[0::2], dots[1::2]
        self.assertTrue(400 <= min(lats) and max(lats) <= 1400)    # about 4.3 to 13.9 N
        self.assertTrue(260 <= min(lons) and max(lons) <= 1470)    # about 2.7 to 14.7 E
        self.assertFalse(bh.is_africa(45.0, 24.0))                   # Riyadh, Arabia
        self.assertTrue(bh.is_africa(8.5, 12.0))                     # Kano

    def test_no_token_or_env_values_in_page(self):
        self.assertNotIn("x-ucdp-access-token", self.page)
        self.assertNotIn("UCDP_TOKEN", self.page)


if __name__ == "__main__":
    unittest.main()

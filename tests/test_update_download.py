"""Tests for the download side of the weekly update: ucdp_api.py, fetch_all.py and
save_events.py, with the API faked (tests/fake_ucdp.py) and a temporary database.

    python -m unittest discover -s tests
"""

import os
import sqlite3
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fake_ucdp import TOKEN, FakeUCDP, event, http_error, page, timeout  # noqa: E402

import fetch_all  # noqa: E402
import save_events  # noqa: E402
import ucdp_api  # noqa: E402

NEXT = ucdp_api.API_URL + "26.0.10?pagesize=1000&Country=475&page=1"


class GetPageTests(unittest.TestCase):
    def test_retry_after_is_honoured(self):
        with FakeUCDP([http_error(503, retry_after=7), page()]) as api, redirect_stdout(StringIO()):
            ucdp_api.get_page("https://ucdpapi.pcr.uu.se/api/gedevents/26.1", TOKEN)
        self.assertEqual(api.sleeps, [7])

    def test_other_client_errors_are_not_retried(self):
        with FakeUCDP([http_error(404)]) as api, self.assertRaises(ucdp_api.HTTPStatusError) as caught:
            ucdp_api.get_page("https://ucdpapi.pcr.uu.se/api/gedevents/26.0.99", TOKEN)
        self.assertEqual((len(api.urls), caught.exception.code), (1, 404))

    def test_cut_off_json_is_retried(self):
        with FakeUCDP([b'{"TotalCount": 3, "Res', page()]) as api, redirect_stdout(StringIO()):
            ucdp_api.get_page("https://ucdpapi.pcr.uu.se/api/gedevents/26.1", TOKEN)
        self.assertEqual(len(api.urls), 2)

    def test_counts_every_attempt(self):
        with FakeUCDP([timeout(), http_error(500), page()]), redirect_stdout(StringIO()):
            ucdp_api.get_page("https://ucdpapi.pcr.uu.se/api/gedevents/26.1", TOKEN)
            self.assertEqual(ucdp_api.requests_made, 3)

    def test_token_is_only_sent_to_the_ucdp_api(self):
        for url in ("https://evil.example/api/gedevents/26.1",
                    "http://ucdpapi.pcr.uu.se/api/gedevents/26.1"):
            with self.subTest(url=url), FakeUCDP([]) as fake, \
                    self.assertRaises(ucdp_api.UCDPError):
                ucdp_api.get_page(url, TOKEN)
            self.assertEqual(fake.urls, [])          # nothing was sent

    def test_shape_checks(self):
        url = "https://ucdpapi.pcr.uu.se/api/gedevents/26.1"
        bad = [page(total=-1), page(total="3"), page(total=True), dict(page(), Result={}),
               {"Result": [], "TotalCount": 0}, page(next_url="https://evil.example/steal")]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ucdp_api.UCDPError):
                ucdp_api.check_page(data, url)
        ucdp_api.check_page(page([event(1)], next_url=NEXT), url)        # fine


class FetchAllTests(unittest.TestCase):
    def setUp(self):
        for p in (mock.patch.object(fetch_all, "COUNTRIES", [475, 471]),
                  mock.patch.object(fetch_all.time, "sleep", lambda s: None)):
            p.start()
            self.addCleanup(p.stop)

    def fetch(self, answers):
        with FakeUCDP(answers) as api, redirect_stdout(StringIO()):
            result = fetch_all.fetch_all(TOKEN, "26.0.10")
        return result, api

    def test_follows_pages_and_counts_retries(self):
        answers = [page([event(1)], total=2, pages=2, next_url=NEXT), http_error(503),
                   page([event(2)], total=2, pages=2), page([event(3)])]
        (events, total, requests), api = self.fetch(answers)
        self.assertEqual(([e["id"] for e in events], total, requests), ([1, 2, 3], 3, 4))
        self.assertEqual(api.urls[1], NEXT)

    def test_a_page_that_keeps_failing_stops_the_download(self):
        with self.assertRaises(SystemExit) as caught:
            self.fetch([page([event(1)], total=2, pages=2, next_url=NEXT)] + [timeout()] * 3)
        self.assertIn("Download stopped", str(caught.exception.code))

    def test_changed_shape_stops_the_download(self):
        with self.assertRaises(SystemExit) as caught:
            self.fetch([{"Events": []}])
        self.assertIn("has the API changed", str(caught.exception.code))


class SaveEventsTests(unittest.TestCase):
    def test_check_complete(self):
        three = [event(1), event(2), event(3)]
        self.assertIsNone(save_events.check_complete(three, 3, "26.0.10"))
        self.assertIn("API said 4", save_events.check_complete(three, 4, "26.0.10"))
        self.assertIn("came twice", save_events.check_complete([event(1), event(1), event(3)], 3, "26.0.10"))
        self.assertIn("no events at all", save_events.check_complete([], 0, "26.0.10"))

    def test_events_and_log_are_saved_together_or_not_at_all(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.execute("CREATE TABLE fetch_log (dataset_version TEXT, query TEXT, fetched_at TEXT, event_count INTEGER)")
        events = [{"id": 1, "best": 2}, {"id": 2, "best": 0}]
        with mock.patch.object(save_events, "log_fetch", side_effect=sqlite3.OperationalError("disk I/O error")):
            with self.assertRaises(sqlite3.OperationalError):
                save_events.save_version(db, events, "26.0.10")
        self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0], 0)

        save_events.save_version(db, events, "26.0.10")
        self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 2)
        self.assertEqual(db.execute("SELECT event_count FROM fetch_log").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()

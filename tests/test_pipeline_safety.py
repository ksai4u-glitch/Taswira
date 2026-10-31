"""Safety tests for the data pipeline (token handling, page output, saving).
No test here calls the UCDP API: requests go to a local test server or are faked.

    python -m unittest discover -s tests
"""

import http.server
import json
import os
import sqlite3
import sys
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_map  # noqa: E402
import fetch_all  # noqa: E402
import fetch_nigeria  # noqa: E402
import save_events  # noqa: E402
import ucdp_api  # noqa: E402


class UcdpUrlTests(unittest.TestCase):
    def test_only_https_ucdp_api_is_allowed(self):
        ok = fetch_nigeria.is_ucdp_url
        self.assertTrue(ok("https://ucdpapi.pcr.uu.se/api/gedevents/26.1?pagesize=1"))
        self.assertTrue(ok("https://ucdpapi.pcr.uu.se:443/api/gedevents/26.1"))
        for bad in ("http://ucdpapi.pcr.uu.se/api/gedevents/26.1",       # no TLS
                    "https://ucdpapi.pcr.uu.se.evil.example/api",          # look-alike host
                    "https://evil.example/?u=https://ucdpapi.pcr.uu.se/",
                    "https://user@ucdpapi.pcr.uu.se/api",
                    "https://ucdpapi.pcr.uu.se:8443/api",
                    "//ucdpapi.pcr.uu.se/api", "", None, "https://[bad"):
            self.assertFalse(ok(bad), bad)

    def test_open_ucdp_refuses_other_addresses(self):
        with self.assertRaises(ValueError):
            fetch_nigeria.open_ucdp("https://example.org/", "SECRET")


class RedirectTests(unittest.TestCase):
    """urllib copies custom headers to a redirect target; the token must not go along."""

    def test_redirect_away_from_ucdp_is_refused_and_token_not_sent(self):
        seen = []

        class Target(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(self.headers.get("x-ucdp-access-token"))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *args):
                pass

        target = http.server.HTTPServer(("127.0.0.1", 0), Target)

        class Redirect(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{target.server_port}/steal")
                self.end_headers()

            def log_message(self, *args):
                pass

        start = http.server.HTTPServer(("127.0.0.1", 0), Redirect)
        for server in (start, target):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            request = urllib.request.Request(f"http://127.0.0.1:{start.server_port}/",
                                             headers={"x-ucdp-access-token": "SECRET"})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                fetch_nigeria._OPENER.open(request, timeout=5)
            self.assertIn("refused a redirect", str(caught.exception.reason))
            self.assertEqual(seen, [])
        finally:
            for server in (start, target):
                server.shutdown()
                server.server_close()


def page(events, next_url="", total=None, pages=1):
    return {"Result": events, "TotalCount": len(events) if total is None else total,
            "TotalPages": pages, "NextPageUrl": next_url}


class FetchAllTests(unittest.TestCase):
    def run_fetch(self, responses):
        calls = []

        def fake_get_json(url, token):
            calls.append(url)
            ucdp_api.requests_made += 1     # fetch_all counts the attempts ucdp_api makes
            return responses.pop(0)

        with mock.patch.object(fetch_all, "get_json", fake_get_json), \
             mock.patch.object(ucdp_api, "requests_made", 0), \
             mock.patch.object(fetch_all, "COUNTRIES", [475]), \
             mock.patch.object(fetch_all.time, "sleep"):
            result = fetch_all.fetch_all("SECRET", "26.1")
        return result, calls

    def test_follows_next_page_on_the_api(self):
        (events, total, requests), calls = self.run_fetch([
            page([{"id": 1}], "https://ucdpapi.pcr.uu.se/api/gedevents/26.1?page=1", total=2, pages=2),
            page([{"id": 2}], total=2, pages=2),
        ])
        self.assertEqual(([e["id"] for e in events], total, requests), ([1, 2], 2, 2))
        self.assertEqual(calls[1], "https://ucdpapi.pcr.uu.se/api/gedevents/26.1?page=1")

    def test_stops_before_sending_the_token_elsewhere(self):
        responses = [page([{"id": 1}], "https://evil.example/next", total=2, pages=2)]
        with self.assertRaises(SystemExit) as caught:
            self.run_fetch(responses)
        self.assertIn("NextPageUrl", str(caught.exception))


class SaveTests(unittest.TestCase):
    def test_incomplete_download_is_not_saved(self):
        self.assertIsNone(save_events.incomplete([{"id": 1}, {"id": 2}], 2))
        self.assertIn("API said 3", save_events.incomplete([{"id": 1}, {"id": 2}], 3))
        # Same count, but one event twice and another missing
        self.assertIn("different ids", save_events.incomplete([{"id": 1}, {"id": 1}], 2))

    def test_field_names_are_quoted_safely(self):
        db = sqlite3.connect(":memory:")
        odd = 'x"); DROP TABLE fetch_log; --'
        db.execute("CREATE TABLE fetch_log (a)")
        save_events.save(db, [{"id": 1, "best": 3, odd: "v"}], "26.1")
        self.assertEqual(db.execute(f"SELECT {save_events.quote_name(odd)} FROM events").fetchone(), ("v",))
        self.assertEqual(db.execute("SELECT COUNT(*) FROM fetch_log").fetchone(), (0,))


def event(**changes):
    e = {"date_start": "2024-01-02", "date_end": "2024-01-02", "country": "Nigeria", "state": "Borno",
         "lga": None, "place": "Maiduguri", "latitude": 11.8, "longitude": 13.15,
         "violence_label": "one-sided", "side_a": "IS", "side_b": "Civilians",
         "deaths_best": 3, "deaths_low": 3, "deaths_high": 4, "dataset_version": "26.1", "preliminary": 0}
    e.update(changes)
    return e


class PageTests(unittest.TestCase):
    def test_data_cannot_leave_the_script_tag(self):
        text = build_map.to_js({"place": "</script><script>alert(1)</script><!--<script>"})
        self.assertNotIn("<", text)
        self.assertEqual(json.loads(text)["place"], "</script><script>alert(1)</script><!--<script>")

    def test_line_separators_are_escaped(self):
        self.assertEqual(build_map.to_js("a b c"), '"a\\u2028b\\u2029c"')

    def test_placeholder_text_in_the_data_is_left_alone(self):
        sneaky = "__UNMAPPED_JSON__ __VERSION__ __AREA__"
        page = build_map.fill_template([event(place=sneaky), event()], [event(side_a="</script>")])
        self.assertIn(json.dumps(sneaky)[1:-1], page)
        self.assertEqual(page.count("</script>"), page.count("<script"))
        for name in ("__EVENTS_JSON__", "__UNMAPPED_JSON__", "__BUILT__", "__COUNTRY_HEAT_MAX__"):
            self.assertNotIn(name, page.replace(sneaky, ""))

    def test_fill_replaces_every_placeholder_once(self):
        self.assertEqual(build_map.fill("__A__ __AB__ __A__", {"__A__": "__AB__", "__AB__": "x"}),
                         "__AB__ x __AB__")


if __name__ == "__main__":
    unittest.main()

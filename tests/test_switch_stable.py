"""Tests for switch_stable.py (no network: the HTTP layer is mocked). Run from the repository folder:

    python -m unittest discover -s tests
"""

import io
import os
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import date
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fetch_nigeria  # noqa: E402
import switch_stable as ss  # noqa: E402

SETTINGS = '''"""Settings."""

API_VERSION = "26.1"          # stable yearly GED release (covers events up to the end of 2025)

CANDIDATE_VERSIONS = ["26.01.26.06", "26.0.7", "26.0.12", "27.0.1", "27.01.27.03", "27.0.2"]

START_DATE = "2020-01-01"     # the API filters both dates on date_end
END_DATE = "2025-12-31"       # the stable release; Candidate data covers what comes after
'''


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(code):
    return urllib.error.HTTPError("https://example.invalid", code, "error", {}, None)


class VersionTests(unittest.TestCase):
    def test_covered_year(self):
        self.assertEqual(ss.covered_year("27.1"), 2026)
        self.assertEqual(ss.next_stable("26.1"), "27.1")

    def test_rejects_non_stable_versions(self):
        for bad in ("27", "27.0.1", "27.2", "2027.1", "abc"):
            with self.assertRaises(SystemExit):
                ss.parse_stable(bad)

    def test_candidate_year(self):
        self.assertEqual(ss.candidate_year("26.0.7"), 2026)
        self.assertEqual(ss.candidate_year("26.01.26.06"), 2026)
        self.assertEqual(ss.candidate_year("26.10.27.01"), 2027)
        self.assertIsNone(ss.candidate_year("weird"))

    def test_split_candidates(self):
        dropped, kept, unknown = ss.split_candidates(
            ["26.01.26.06", "26.0.12", "27.0.1", "26.10.27.01", "x.y"], "27.1")
        self.assertEqual(dropped, ["26.01.26.06", "26.0.12"])
        self.assertEqual(kept, ["27.0.1", "26.10.27.01", "x.y"])
        self.assertEqual(unknown, ["x.y"])


class SwitchTextTests(unittest.TestCase):
    def test_updates_version_end_date_and_candidates(self):
        new, dropped, kept, unknown = ss.switch_text(SETTINGS, "27.1")
        self.assertIn('API_VERSION = "27.1"          # stable yearly GED release (covers events up to the end of 2026)', new)
        self.assertIn('END_DATE = "2026-12-31"       # the stable release', new)
        self.assertIn('START_DATE = "2020-01-01"', new)
        self.assertIn('CANDIDATE_VERSIONS = ["27.0.1", "27.01.27.03", "27.0.2"]', new)
        self.assertEqual(dropped, ["26.01.26.06", "26.0.7", "26.0.12"])
        self.assertEqual(unknown, [])

    def test_result_is_valid_python(self):
        new, *_ = ss.switch_text(SETTINGS, "27.1")
        values = {}
        exec(new, values)
        self.assertEqual(values["API_VERSION"], "27.1")
        self.assertEqual(values["END_DATE"], "2026-12-31")

    def test_refuses_same_or_older_version(self):
        for v in ("26.1", "25.1"):
            with self.assertRaises(SystemExit):
                ss.switch_text(SETTINGS, v)

    def test_works_on_the_real_settings_file(self):
        with open(ss.SETTINGS_PATH, encoding="utf-8") as f:
            text = f.read()
        current = ss.read_value(text, "API_VERSION")
        new, *_ = ss.switch_text(text, ss.next_stable(current))
        self.assertIn(f'API_VERSION = "{ss.next_stable(current)}"', new)


class ApiTests(unittest.TestCase):
    def test_version_exists(self):
        with mock.patch.object(fetch_nigeria._OPENER, "open", return_value=FakeResponse()) as urlopen:
            self.assertTrue(ss.version_exists("27.1", "secret"))
        request = urlopen.call_args[0][0]
        self.assertIn("/gedevents/27.1?pagesize=1", request.full_url)
        self.assertEqual(urlopen.call_count, 1)

    def test_version_missing_or_unknown(self):
        cases = [(http_error(404), False), (http_error(400), False), (http_error(401), None),
                 (http_error(500), None), (urllib.error.URLError("down"), None)]
        for error, expected in cases:
            with mock.patch.object(fetch_nigeria._OPENER, "open", side_effect=error):
                self.assertIs(ss.version_exists("27.1", "secret"), expected)

    def test_notice_costs_nothing_before_may(self):
        with mock.patch.object(fetch_nigeria._OPENER, "open") as urlopen:
            self.assertIsNone(ss.stable_notice("26.1", "secret", today=date(2027, 4, 30)))
        urlopen.assert_not_called()

    def test_notice_when_published(self):
        with mock.patch.object(fetch_nigeria._OPENER, "open", return_value=FakeResponse()) as urlopen:
            notice = ss.stable_notice("26.1", "secret", today=date(2027, 6, 15))
        self.assertIn("switch_stable.py 27.1", notice)
        self.assertEqual(urlopen.call_count, 1)

    def test_notice_silent_when_missing_or_failing(self):
        for error in (http_error(404), http_error(500), urllib.error.URLError("down")):
            with mock.patch.object(fetch_nigeria._OPENER, "open", side_effect=error):
                self.assertIsNone(ss.stable_notice("26.1", "secret", today=date(2027, 6, 15)))


class MainTests(unittest.TestCase):
    def setUp(self):
        handle, self.path = tempfile.mkstemp(suffix=".py")
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            f.write(SETTINGS)
        patcher = mock.patch.object(ss, "SETTINGS_PATH", self.path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(os.remove, self.path)

    def read(self):
        with open(self.path, encoding="utf-8") as f:
            return f.read()

    def run_main(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            ss.main(list(args))
        return out.getvalue()

    def test_dry_run_writes_nothing(self):
        with mock.patch.object(fetch_nigeria._OPENER, "open") as urlopen:
            out = self.run_main("27.1", "--dry-run", "--no-check")
        urlopen.assert_not_called()
        self.assertEqual(self.read(), SETTINGS)
        self.assertIn('+API_VERSION = "27.1"', out)
        self.assertIn('-END_DATE = "2025-12-31"', out)
        self.assertIn("Dry run", out)

    def test_writes_after_check(self):
        with mock.patch("fetch_nigeria.load_token", return_value="secret"), \
             mock.patch.object(fetch_nigeria._OPENER, "open", return_value=FakeResponse()) as urlopen:
            out = self.run_main("27.1")
        self.assertEqual(urlopen.call_count, 1)
        self.assertIn('API_VERSION = "27.1"', self.read())
        self.assertIn("python save_events.py", out)
        self.assertIn("python publish.py", out)
        self.assertNotIn("secret", out)

    def test_unpublished_version_changes_nothing(self):
        with mock.patch("fetch_nigeria.load_token", return_value="secret"), \
             mock.patch.object(fetch_nigeria._OPENER, "open", side_effect=http_error(404)):
            with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                ss.main(["27.1"])
        self.assertEqual(self.read(), SETTINGS)

    def test_warns_when_no_monthly_version_is_left(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(SETTINGS.replace(', "27.0.1", "27.01.27.03", "27.0.2"', ""))
        out = self.run_main("27.1", "--no-check")
        self.assertIn("CANDIDATE_VERSIONS = []", self.read())
        self.assertIn("Warning: no monthly Candidate version", out)


if __name__ == "__main__":
    unittest.main()

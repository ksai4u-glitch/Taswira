"""Tests for update_candidates.py (the weekly check for a new Candidate release).
The API is faked (tests/fake_ucdp.py): no network, no token. Run from the repository folder:

    python -m unittest discover -s tests
"""

import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fake_ucdp import TOKEN, FakeUCDP, event, http_error, page, timeout  # noqa: E402

import update_candidates as uc  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOUND = page([event(1)], total=12)          # "yes, this version exists"


class NextVersionTests(unittest.TestCase):
    def test_counts_up_within_a_year(self):
        self.assertEqual(uc.next_version("26.0.7"), "26.0.8")
        self.assertEqual(uc.next_version("26.0.9"), "26.0.10")     # not "26.0.9" + "1" text
        self.assertEqual(uc.next_version("26.0.10"), "26.0.11")
        self.assertEqual(uc.next_version("26.0.11"), "26.0.12")

    def test_year_rollover(self):
        self.assertEqual(uc.next_version("26.0.12"), "27.0.1")
        self.assertEqual(uc.next_version("99.0.12"), "100.0.1")

    def test_rejects_versions_that_are_not_monthly(self):
        for bad in ["26.1", "26.01.26.06", "26.0.13", "26.0.0", "26.1.3", "26.0.x", "", "26.0.9 "]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                uc.next_version(bad)

    def test_last_monthly_compares_numbers_not_text(self):
        # as text "26.0.9" > "26.0.10"; as numbers it is older
        self.assertEqual(uc.last_monthly(["26.01.26.06", "26.0.9", "26.0.10", "26.0.8"]), "26.0.10")
        self.assertEqual(uc.last_monthly(["26.0.12", "27.0.1"]), "27.0.1")

    def test_last_monthly_ignores_quarterly_and_needs_one_monthly(self):
        self.assertEqual(uc.last_monthly(["26.01.26.06", "26.0.7"]), "26.0.7")
        with self.assertRaises(SystemExit):
            uc.last_monthly(["26.01.26.06"])


class IsPublishedTests(unittest.TestCase):
    def test_published_costs_one_request_with_the_token_in_the_header_only(self):
        with FakeUCDP([FOUND]) as api:
            self.assertTrue(uc.is_published("26.0.10", TOKEN))
        self.assertEqual(len(api.urls), 1)
        self.assertIn("/gedevents/26.0.10?pagesize=1", api.urls[0])
        self.assertNotIn(TOKEN, api.urls[0])
        self.assertEqual(api.headers[0]["X-ucdp-access-token"], TOKEN)

    def test_not_published_yet(self):
        for code in (400, 404):
            with self.subTest(code=code), FakeUCDP([http_error(code)]) as api:
                self.assertFalse(uc.is_published("26.0.10", TOKEN))
                self.assertEqual(len(api.urls), 1)        # no retries for "not there"

    def test_empty_release_is_not_added(self):
        with FakeUCDP([page([], total=0)]), redirect_stdout(StringIO()) as out:
            self.assertFalse(uc.is_published("26.0.10", TOKEN))
        self.assertIn("no Nigeria events", out.getvalue())

    def test_token_refused_is_an_error_not_a_no(self):
        for code in (401, 403):
            with self.subTest(code=code), FakeUCDP([http_error(code)]) as api:
                with self.assertRaises(uc.ucdp_api.AuthError):
                    uc.is_published("26.0.10", TOKEN)
                self.assertEqual(len(api.urls), 1)

    def test_rate_limit_is_retried_not_taken_as_unpublished(self):
        # before, HTTP 429 counted as "not published" and the week was silently skipped
        with FakeUCDP([http_error(429), FOUND]) as api, redirect_stdout(StringIO()):
            self.assertTrue(uc.is_published("26.0.10", TOKEN))
        self.assertEqual(len(api.urls), 2)

    def test_server_errors_and_timeouts_are_retried_with_backoff(self):
        with FakeUCDP([http_error(503), timeout(), FOUND]) as api, redirect_stdout(StringIO()):
            self.assertTrue(uc.is_published("26.0.10", TOKEN))
        self.assertEqual(api.sleeps, list(uc.ucdp_api.BACKOFF_SECONDS))

    def test_gives_up_after_three_attempts(self):
        with FakeUCDP([http_error(500)] * 3) as api, redirect_stdout(StringIO()):
            with self.assertRaises(uc.ucdp_api.UCDPError) as caught:
                uc.is_published("26.0.10", TOKEN)
        self.assertEqual(len(api.urls), 3)
        self.assertIn("after 3 attempts", str(caught.exception))

    def test_changed_answer_shape_is_an_error(self):
        for answer in [{"results": []}, [], b"<html>maintenance</html>", page([{"no_id": 1}])]:
            with self.subTest(answer=answer), FakeUCDP([answer] * 3), redirect_stdout(StringIO()):
                with self.assertRaises(uc.ucdp_api.UCDPError):
                    uc.is_published("26.0.10", TOKEN)


class SettingsEditTests(unittest.TestCase):
    SAMPLE = ('API_VERSION = "26.1"\n\n# comment with [brackets]\n'
              'CANDIDATE_VERSIONS = ["26.01.26.06", "26.0.8", "26.0.9"]\n\nPAGE_SIZE = 1000\n')

    def test_appends_and_leaves_the_rest_alone(self):
        text = uc.with_versions_added(self.SAMPLE, ["26.0.10", "26.0.11"])
        self.assertEqual(uc.read_candidates(text), ["26.01.26.06", "26.0.8", "26.0.9", "26.0.10", "26.0.11"])
        self.assertEqual(text.replace(', "26.0.10", "26.0.11"', ""), self.SAMPLE)

    def test_list_written_over_several_lines(self):
        sample = 'X = 1\nCANDIDATE_VERSIONS = [\n    "26.0.8",\n    "26.0.9",\n]\nY = 2\n'
        text = uc.with_versions_added(sample, ["26.0.10"])
        self.assertEqual(uc.read_candidates(text), ["26.0.8", "26.0.9", "26.0.10"])
        self.assertTrue(text.startswith("X = 1\n") and text.endswith("\nY = 2\n"))

    def test_refuses_duplicates_and_missing_list(self):
        with self.assertRaises(ValueError):
            uc.with_versions_added(self.SAMPLE, ["26.0.9"])
        with self.assertRaises(ValueError):
            uc.with_versions_added("API_VERSION = '26.1'\n", ["26.0.10"])

    def test_works_on_the_real_settings_file(self):
        with open(os.path.join(REPO, "settings.py"), encoding="utf-8") as f:
            real = f.read()
        current = uc.read_candidates(real)
        nxt = uc.next_version(uc.last_monthly(current))
        self.assertEqual(uc.read_candidates(uc.with_versions_added(real, [nxt])), current + [nxt])


class MainTests(unittest.TestCase):
    """The whole check, against a copy of settings.py in a temporary folder."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder)
        self.settings = os.path.join(self.folder, "settings.py")
        self.output = os.path.join(self.folder, "github_output")
        with open(self.settings, "w", encoding="utf-8") as f:
            f.write(SettingsEditTests.SAMPLE)
        with open(self.settings, encoding="utf-8") as f:
            self.original = f.read()
        patches = [mock.patch.object(uc, "load_token", return_value=TOKEN),
                   mock.patch.dict(os.environ, {"GITHUB_OUTPUT": self.output}),
                   # The yearly-release notice (tested in test_switch_stable.py) asks the
                   # API once from May of the expected year; keep it out of these counts.
                   mock.patch.object(uc, "stable_notice", return_value=None)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def run_main(self, answers):
        with FakeUCDP(answers) as api, redirect_stdout(StringIO()) as out:
            uc.main(self.settings)
        return api, out.getvalue()

    def read(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def assert_unchanged(self):
        self.assertEqual(self.read(self.settings), self.original)
        self.assertEqual(os.listdir(self.folder), ["settings.py"])     # no output, no temp files

    def test_nothing_new(self):
        api, out = self.run_main([http_error(404)])
        self.assertEqual(self.read(self.settings), self.original)
        self.assertEqual(self.read(self.output), "new_versions=\n")
        self.assertIn("26.0.10 is not published", out)
        self.assertIn("/26.0.10?", api.urls[0])

    def test_one_new_release(self):
        self.run_main([FOUND, http_error(404)])
        self.assertEqual(uc.read_candidates(self.read(self.settings))[-1], "26.0.10")
        self.assertEqual(self.read(self.output), "new_versions=26.0.10\n")

    def test_at_most_three_new_releases(self):
        api, _ = self.run_main([FOUND, FOUND, FOUND])
        self.assertEqual(len(api.urls), 3)
        self.assertEqual(uc.read_candidates(self.read(self.settings))[-3:], ["26.0.10", "26.0.11", "26.0.12"])
        self.assertEqual(self.read(self.output), "new_versions=26.0.10 26.0.11 26.0.12\n")

    def test_failure_exits_non_zero_and_changes_nothing(self):
        # 26.0.10 is found, then UCDP fails for 26.0.11: nothing at all is written
        with self.assertRaises(SystemExit) as caught:
            self.run_main([FOUND] + [http_error(502)] * 3)
        self.assertIn("Update check failed, nothing changed", str(caught.exception.code))
        self.assertNotIn(TOKEN, str(caught.exception.code))
        self.assert_unchanged()

    def test_daily_limit_message(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_main([http_error(429, retry_after=36000)])
        self.assertIn("midnight UTC", str(caught.exception.code))
        self.assert_unchanged()

    def test_request_budget_is_enforced(self):
        with mock.patch.object(uc.ucdp_api, "MAX_REQUESTS_PER_RUN", 2), self.assertRaises(SystemExit) as caught:
            self.run_main([http_error(503), http_error(503), FOUND])
        self.assertIn("MAX_REQUESTS_PER_RUN", str(caught.exception.code))
        self.assert_unchanged()

    def test_failed_write_leaves_settings_untouched(self):
        with mock.patch("safe_files.os.replace", side_effect=OSError("disk full")), self.assertRaises(OSError):
            self.run_main([FOUND, http_error(404)])
        self.assert_unchanged()


if __name__ == "__main__":
    unittest.main()

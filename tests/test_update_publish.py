"""Tests for publish.py's safety checks and its all-or-nothing write of docs/index.html.
No database, network or token needed; the real docs/index.html is never touched.

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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_map  # noqa: E402
import publish  # noqa: E402

TOKEN = "test-token-not-real-1234"


def clean_event(n, version="26.1", preliminary=0):
    """One row of clean_events with the fields the map page uses."""
    return {"date_start": f"2025-0{n % 9 + 1}-01", "date_end": f"2025-0{n % 9 + 1}-01",
            "country": "Nigeria", "state": "Borno", "lga": "Maiduguri", "place": "Maiduguri",
            "latitude": 11.8333 + n / 1000, "longitude": 13.15, "violence_label": "non-state",
            "side_a": "Group A", "side_b": "Civilians", "deaths_best": 2, "deaths_low": 1,
            "deaths_high": 3, "dataset_version": version, "preliminary": preliminary}


STABLE = [clean_event(n) for n in range(5)]
PRELIM = [clean_event(n, "26.0.9", 1) for n in range(3)]
GOOD_PAGE = ("<p>Data: Uppsala Conflict Data Program, GED version 26.1; "
             "preliminary Candidate releases 26.01.26.06, 26.0.7, 26.0.8, 26.0.9.</p>")
CANDIDATES = ["26.01.26.06", "26.0.7", "26.0.8", "26.0.9"]


class ChecksTests(unittest.TestCase):
    def setUp(self):
        for p in (mock.patch.object(publish, "API_VERSION", "26.1"),
                  mock.patch.object(publish, "CANDIDATE_VERSIONS", CANDIDATES)):
            p.start()
            self.addCleanup(p.stop)

    def problems(self, page, mapped=STABLE + PRELIM, unmapped=(), token=TOKEN):
        return publish.problems_with(page, list(mapped), list(unmapped), token)

    def test_a_good_page_passes(self):
        self.assertEqual(self.problems(GOOD_PAGE), [])
        self.assertEqual(self.problems(GOOD_PAGE, token=None), [])     # no token on this computer

    def test_token_in_page(self):
        self.assertIn("the page contains your UCDP token", self.problems(GOOD_PAGE + f"<!-- {TOKEN} -->"))

    def test_ucdp_credit_missing(self):
        page = GOOD_PAGE.replace("Uppsala Conflict Data Program", "UCDP")
        self.assertIn("the UCDP credit or dataset version is missing", self.problems(page))

    def test_dataset_version_missing(self):
        page = GOOD_PAGE.replace("version 26.1", "version 25.1")
        self.assertIn("the UCDP credit or dataset version is missing", self.problems(page))

    def test_preliminary_label_missing(self):
        page = GOOD_PAGE.replace("preliminary", "new")
        self.assertIn("preliminary Candidate events are not labelled", self.problems(page))

    def test_a_candidate_version_missing_from_the_label(self):
        page = GOOD_PAGE.replace(", 26.0.9", "")
        self.assertIn("preliminary Candidate events are not labelled", self.problems(page))

    def test_label_only_needed_when_there_is_preliminary_data(self):
        page = GOOD_PAGE.replace("preliminary", "new")
        self.assertEqual(self.problems(page, mapped=STABLE), [])
        # preliminary events that could not be mapped still need the label
        self.assertIn("preliminary Candidate events are not labelled",
                      self.problems(page, mapped=STABLE, unmapped=PRELIM))

    def test_no_events(self):
        self.assertIn("there are no events to put on the map", self.problems(GOOD_PAGE, mapped=[]))

    def test_unfilled_template(self):
        self.assertTrue(any("not filled in" in p for p in self.problems(GOOD_PAGE + "__EVENTS_JSON__")))

    def test_check_stops_with_every_problem(self):
        with mock.patch.object(publish, "load_token", return_value=TOKEN), self.assertRaises(SystemExit) as caught:
            publish.check(f"{TOKEN} preliminary", STABLE + PRELIM, [])
        message = str(caught.exception.code)
        self.assertTrue(message.startswith("Not publishing:"))
        self.assertIn("token", message)
        self.assertIn("UCDP credit", message)
        self.assertNotIn(TOKEN, message)

    def test_check_without_a_token_still_checks_the_rest(self):
        with mock.patch.object(publish, "load_token", side_effect=SystemExit("No token found.")):
            publish.check(GOOD_PAGE, STABLE + PRELIM, [])        # passes
            with self.assertRaises(SystemExit):
                publish.check("nothing", STABLE + PRELIM, [])


class RealTemplateTests(unittest.TestCase):
    def test_the_real_template_passes_the_checks(self):
        page = build_map.fill_template(STABLE + PRELIM[:2], PRELIM[2:])
        self.assertEqual(publish.problems_with(page, STABLE + PRELIM[:2], PRELIM[2:], TOKEN), [])


class WriteTests(unittest.TestCase):
    """main() against a temporary docs/index.html."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder)
        self.output = os.path.join(self.folder, "docs", "index.html")
        os.makedirs(os.path.dirname(self.output))
        with open(self.output, "w", encoding="utf-8") as f:
            f.write("OLD PAGE")
        for p in (mock.patch.object(publish, "OUTPUT_PATH", self.output),
                  mock.patch.object(publish, "API_VERSION", "26.1"),
                  mock.patch.object(publish, "CANDIDATE_VERSIONS", CANDIDATES),
                  mock.patch.object(publish, "load_token", return_value=TOKEN),
                  mock.patch.object(publish, "load_all", return_value=(STABLE + PRELIM, []))):
            p.start()
            self.addCleanup(p.stop)

    def page_on_disk(self):
        with open(self.output, encoding="utf-8") as f:
            return f.read()

    def assert_old_page_kept(self):
        self.assertEqual(self.page_on_disk(), "OLD PAGE")
        self.assertEqual(os.listdir(os.path.dirname(self.output)), ["index.html"])   # no temp files

    def test_writes_a_good_page(self):
        with mock.patch.object(publish, "fill_template", return_value=GOOD_PAGE), redirect_stdout(StringIO()):
            publish.main()
        self.assertEqual(self.page_on_disk(), GOOD_PAGE)
        self.assertEqual(os.listdir(os.path.dirname(self.output)), ["index.html"])

    def test_failed_check_keeps_the_old_page(self):
        with mock.patch.object(publish, "fill_template", return_value=GOOD_PAGE + TOKEN):
            with self.assertRaises(SystemExit) as caught:
                publish.main()
        self.assertNotEqual(caught.exception.code, 0)
        self.assert_old_page_kept()

    def test_failed_write_keeps_the_old_page(self):
        with mock.patch.object(publish, "fill_template", return_value=GOOD_PAGE), \
                mock.patch("safe_files.os.replace", side_effect=OSError("disk full")), \
                self.assertRaises(OSError):
            publish.main()
        self.assert_old_page_kept()

    def test_crash_while_writing_keeps_the_old_page(self):
        # the run is stopped (Ctrl+C, a killed job) after the text is written, before the swap
        with mock.patch.object(publish, "fill_template", return_value=GOOD_PAGE), \
                mock.patch("safe_files.os.fsync", side_effect=KeyboardInterrupt), \
                self.assertRaises(KeyboardInterrupt):
            publish.main()
        self.assert_old_page_kept()


if __name__ == "__main__":
    unittest.main()

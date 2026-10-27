from pathlib import Path
from contextlib import redirect_stdout
import io
import tempfile
import unittest
from unittest.mock import patch

import build_history as bh


class PreviewOutputTests(unittest.TestCase):
    def test_explicit_preview_path_leaves_default_output_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            default = Path(directory) / "default.html"
            requested = Path(directory) / "preview.html"
            with patch.object(bh, "OUTPUT_PATH", str(default)), patch("sys.argv", ["build_history.py", "--output", str(requested)]), redirect_stdout(io.StringIO()):
                bh.main()
            self.assertTrue(requested.exists(), "--output must build the requested preview, not the live default")
            self.assertFalse(default.exists())
            self.assertIn('id="video-caption"', requested.read_text())

    def test_check_never_writes_requested_output(self):
        with tempfile.TemporaryDirectory() as directory:
            requested = Path(directory) / "preview.html"
            with patch("sys.argv", ["build_history.py", "--check", "--output", str(requested)]), redirect_stdout(io.StringIO()):
                bh.main()
            self.assertFalse(requested.exists())

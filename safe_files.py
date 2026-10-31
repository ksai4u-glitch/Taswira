"""
Write a file all at once or not at all.

The text goes to a temporary file in the same folder, which then replaces the
real file in one step (os.replace). If anything fails before that step, the
old file is left exactly as it was and the temporary file is removed, so a
crash can never leave a half-written settings.py or docs/index.html.

Uses only the Python standard library.
"""

import os
import tempfile


def write_text(path, text):
    """Replace the file at path with text (UTF-8), atomically."""
    folder = os.path.dirname(os.path.abspath(path))
    fd, temp_path = tempfile.mkstemp(dir=folder, prefix="." + os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        try:
            mode = os.stat(path).st_mode & 0o777      # keep the old file's permissions
        except FileNotFoundError:
            mode = 0o644
        os.chmod(temp_path, mode)
        os.replace(temp_path, path)
    except BaseException:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise

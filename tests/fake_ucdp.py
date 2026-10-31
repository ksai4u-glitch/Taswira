"""A stand-in for the UCDP API, so tests never touch the network or need a token.

    with FakeUCDP([page(...), http_error(503), timeout()]) as api:
        ...            # each request to the UCDP API takes the next answer
    api.urls           # the URLs that were asked for, in order
"""

import email.message
import io
import json
import os
import sys
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fetch_nigeria  # noqa: E402
import ucdp_api  # noqa: E402

TOKEN = "test-token-not-real-1234"


def page(events=(), total=None, pages=1, next_url=""):
    """A GED page as the API sends it."""
    events = list(events)
    return {"TotalCount": len(events) if total is None else total, "TotalPages": pages,
            "PreviousPageUrl": "", "NextPageUrl": next_url, "Result": events}


def event(event_id, **fields):
    return {"id": event_id, **fields}


def http_error(code, retry_after=None):
    headers = email.message.Message()
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return urllib.error.HTTPError("https://ucdpapi.pcr.uu.se/x", code, "error", headers, io.BytesIO(b""))


def timeout():
    return urllib.error.URLError(TimeoutError("timed out"))


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class FakeUCDP:
    """Patch the UCDP opener and sleep; answers are dicts (sent as JSON), bytes (sent raw) or exceptions."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.urls, self.headers, self.sleeps = [], [], []

    def _urlopen(self, request, timeout=None):
        self.urls.append(request.full_url)
        self.headers.append(dict(request.header_items()))
        if not self.answers:
            raise AssertionError(f"unexpected extra request: {request.full_url}")
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        body = answer if isinstance(answer, bytes) else json.dumps(answer).encode()
        return _Response(body)

    def __enter__(self):
        self._patches = [
            # requests go through fetch_nigeria.open_ucdp (UCDP-only, no redirects away)
            mock.patch.object(fetch_nigeria._OPENER, "open", self._urlopen),
            mock.patch.object(ucdp_api.time, "sleep", self.sleeps.append),
            mock.patch.object(ucdp_api, "requests_made", 0),
        ]
        for p in self._patches:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in reversed(self._patches):
            p.stop()

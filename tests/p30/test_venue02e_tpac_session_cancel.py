#!/usr/bin/env python3
"""TPAC canceled-session role safety: synthetic topology, official signal external."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02e_tpac_session_cancel import inspect_detail

URL = "https://tpac.org.taipei/program/2053"
TITLE = "深夜小狗神秘習題"
ROWS = ["2026-10-29 (四) 19:30",
        "2026-10-30 (五) 19:30 已取消，詳細退票資訊請洽詢opentix",
        "2026-10-31 (六) 14:30",
        "2026-10-31 (六) 19:30 已取消，詳細退票資訊請洽詢opentix",
        "2026-11-01 (日) 14:30"]
def fixture(rows=ROWS, title=TITLE, label="場次"):
    return ('<main><h1>' + title + '</h1><h3>' + label +
            '</h3><ul>' + ''.join('<li>' + x + '</li>' for x in rows) +
            '</ul></main>').encode()

class TpacCancellationTests(unittest.TestCase):
    def check(self, html, decision, url=URL, title=TITLE):
        r = inspect_detail(html, url, title)
        self.assertEqual(r["decision"], decision)
        self.assertEqual(r["acceptedFields"], 0)
        self.assertEqual(r["goldenAccepted"], 0)
        self.assertFalse(r["published"])
        self.assertIsNone(r["ticketEventId"])
        self.assertEqual(r["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        return r
    def test_real_shape_cancel_split(self):
        r = self.check(fixture(), "REVIEW_SESSION_CANCEL_SPLIT_NOT_ACCEPTED")
        self.assertEqual((r["sessionCount"], r["canceledCount"], r["activeCount"]), (5, 2, 3))
    def test_all_canceled(self):
        r = self.check(fixture([ROWS[1]]), "REVIEW_SESSION_CANCEL_SPLIT_NOT_ACCEPTED")
        self.assertEqual((r["canceledCount"], r["activeCount"]), (1, 0))
    def test_unmarked_not_assumed_cancel(self):
        r = self.check(fixture([ROWS[0]]), "REVIEW_SESSION_CANCEL_SPLIT_NOT_ACCEPTED")
        self.assertEqual((r["canceledCount"], r["activeCount"]), (0, 1))
    def test_ambiguous_status(self):
        self.check(fixture(["2026-10-30 (五) 19:30 取消待確認"]), "HOLD_AMBIGUOUS_SESSION_TEXT")
    def test_other_title(self):
        self.check(fixture(title="別的活動"), "HOLD_TITLE_IDENTITY")
    def test_duplicate_title(self):
        self.check(fixture() + f"<h1>{TITLE}</h1>".encode(), "HOLD_TITLE_IDENTITY")
    def test_duplicate_session_label(self):
        self.check(fixture() + b"<h3>\xe5\xa0\xb4\xe6\xac\xa1</h3>", "HOLD_SESSION_LABEL_NOT_UNIQUE")
    def test_hidden_ancestor(self):
        self.check(b'<main hidden>' + fixture() + b'</main>', "HOLD_TITLE_IDENTITY")
    def test_no_list(self):
        self.check(f'<h1>{TITLE}</h1><h3>場次</h3>'.encode(), "HOLD_NO_LOCAL_SESSION_LIST")
    def test_external_url(self):
        self.check(fixture(), "HOLD_SOURCE_URL", url="https://other.example/program/2053")
    def test_query_url(self):
        self.check(fixture(), "HOLD_SOURCE_URL", url=URL+"?ticket=123")
    def test_cap(self):
        self.check(fixture([ROWS[0]] * 31), "HOLD_SESSION_COUNT_CAP")
    def test_oversize(self):
        self.check(b"x" * 800001, "HOLD_INPUT")

if __name__ == "__main__":
    unittest.main()

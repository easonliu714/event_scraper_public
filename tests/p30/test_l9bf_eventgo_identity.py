#!/usr/bin/env python3
"""P30-L9-BF fail-closed Event Go list/detail identity regression."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bf_eventgo_identity import safe_detail, list_candidates, inspect_detail

class Cases(unittest.TestCase):
    def test_same_origin(self):
        self.assertEqual(safe_detail("/event/detail?id=5"), "https://eventgo.bnextmedia.com.tw/event/detail?id=5")
    def test_external(self):
        self.assertIsNone(safe_detail("https://evil.example/event/detail?id=5"))
    def test_http(self):
        self.assertIsNone(safe_detail("http://eventgo.bnextmedia.com.tw/event/detail?id=5"))
    def test_credentials(self):
        self.assertIsNone(safe_detail("https://x@eventgo.bnextmedia.com.tw/event/detail?id=5"))
    def test_unrelated(self):
        self.assertIsNone(safe_detail("/article/detail?id=5"))
    def test_valid_index(self):
        h = '<a href="/event/detail?id=5">臺北數位文化年度論壇</a>'
        self.assertEqual(len(list_candidates(h)), 1)
    def test_conflicting_index_labels(self):
        h = '<a href="/event/detail?id=5">臺北數位文化年度論壇</a><a href="/event/detail?id=5">完全不同活動</a>'
        self.assertEqual(list_candidates(h), [])
    def test_generic_label(self):
        self.assertEqual(list_candidates('<a href="/event/detail?id=5">立即報名</a>'), [])
    def test_exact_heading_review(self):
        d = inspect_detail("<h1>臺北數位文化年度論壇</h1>", "臺北數位文化年度論壇")
        self.assertEqual(d["decision"], "REVIEW_SAME_URL_EXACT_TITLE_NO_FIELDS")
        self.assertEqual(d["acceptedFields"], 0)
    def test_mismatch_hold(self):
        self.assertEqual(inspect_detail("<h1>其他活動</h1>", "臺北數位文化年度論壇")["decision"], "HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_duplicate_heading_hold(self):
        d = inspect_detail("<h1>臺北數位文化年度論壇</h1><h2>臺北數位文化年度論壇</h2>", "臺北數位文化年度論壇")
        self.assertEqual(d["decision"], "HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")

if __name__ == "__main__":
    unittest.main()

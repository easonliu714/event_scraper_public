#!/usr/bin/env python3
"""Regression for source-observed percent-encoded Chinese exhibition slug."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bm_huashan_route_diagnostic import classify_href, diagnose_index

class Cases(unittest.TestCase):
    def test_chinese_slug(self):
        kind, url = classify_href("/exhibition/%E9%A2%A8%E5%9C%9F%E9%9B%BB%E5%BD%B1%E9%99%A2")
        self.assertEqual(kind, "ENCODED_UNICODE_DETAIL")
        self.assertIn("%E9%A2%A8", url)
    def test_plain_legacy_slug(self):
        self.assertEqual(classify_href("/exhibition/123456")[0], "PLAIN_DETAIL")
    def test_cross_host(self):
        self.assertEqual(classify_href("https://evil.example/exhibition/123456")[0], "UNSAFE")
    def test_encoded_slash(self):
        self.assertIsNone(classify_href("/exhibition/a%2Fb")[1])
    def test_double_encoded(self):
        self.assertIsNone(classify_href("/exhibition/%252F")[1])
    def test_query(self):
        self.assertIsNone(classify_href("/exhibition/abc?redirect=x")[1])
    def test_fragment(self):
        self.assertIsNone(classify_href("/exhibition/abc#x")[1])
    def test_dot_segment(self):
        self.assertIsNone(classify_href("/exhibition/%2E%2E/other")[1])
    def test_aggregate(self):
        self.assertIsNone(classify_href("/exhibition")[1])
    def test_source_route_not_identity(self):
        a=diagnose_index('<a href="/exhibition/%E9%A2%A8%E5%9C%9F">2026.10.30 風土電影院</a>')
        self.assertEqual(a["sourceDerivedRouteCandidates"],1)
        self.assertEqual(a["acceptedFields"],0)
        self.assertFalse(a["published"])
        self.assertEqual(a["decision"],"REVIEW_ROUTE_TOPOLOGY_NOT_EVENT_IDENTITY")
    def test_conflicting_title_holds(self):
        html='<a href="/exhibition/abc">甲甲甲甲</a><a href="/exhibition/abc">乙乙乙乙</a>'
        self.assertEqual(diagnose_index(html)["decision"],"HOLD_ROUTE_OR_TITLE")
if __name__ == "__main__":
    unittest.main()

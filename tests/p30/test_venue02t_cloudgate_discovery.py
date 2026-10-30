#!/usr/bin/env python3
"""P30-VENUE-02T Cloud Gate source-local role/identity fail-closed tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02t_cloudgate_discovery import safe_link, index_edges, inspect_detail

class Cases(unittest.TestCase):
    def test_same_origin(self):
        self.assertEqual(safe_link("/events/123"), "https://www.cloudgate.org.tw/events/123")
    def test_external(self):
        self.assertIsNone(safe_link("https://evil.example/events/123"))
    def test_http(self):
        self.assertIsNone(safe_link("http://www.cloudgate.org.tw/events/123"))
    def test_credentials(self):
        self.assertIsNone(safe_link("https://x@www.cloudgate.org.tw/events/123"))
    def test_protocol_relative(self):
        self.assertIsNone(safe_link("//www.cloudgate.org.tw/events/123"))
    def test_candidate(self):
        x, edges = index_edges('<a href="/events/123">雲門劇場年度演出節目</a>')
        self.assertEqual(x["candidateDetailEdges"], 1)
        self.assertEqual(len(edges), 1)
    def test_generic(self):
        x, edges = index_edges('<a href="/events/123">立即購票</a>')
        self.assertEqual(edges, [])
    def test_non_event_path(self):
        x, edges = index_edges('<a href="/about/123">雲門劇場年度演出節目</a>')
        self.assertEqual(edges, [])
    def test_conflict(self):
        h = '<a href="/events/123">雲門劇場年度演出節目</a><a href="/events/123">另一場完全不同節目</a>'
        self.assertEqual(index_edges(h)[1], [])
    def test_exact_review(self):
        d = inspect_detail("<h1>雲門劇場年度演出節目</h1>", "雲門劇場年度演出節目")
        self.assertEqual(d["decision"], "REVIEW_EXACT_VENUE_INDEX_DETAIL_TITLE_NO_EVENT_ID")
        self.assertEqual(d["acceptedFields"], 0)
    def test_mismatch(self):
        self.assertEqual(inspect_detail("<h1>另一活動</h1>", "雲門劇場年度演出節目")["decision"], "HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_duplicate(self):
        h = "<h1>雲門劇場年度演出節目</h1><h2>雲門劇場年度演出節目</h2>"
        self.assertEqual(inspect_detail(h, "雲門劇場年度演出節目")["decision"], "HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")

if __name__ == "__main__":
    unittest.main()

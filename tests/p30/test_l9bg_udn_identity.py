#!/usr/bin/env python3
"""P30-L9-BG UDN #06 strict same-product identity regression."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bg_udn_identity import safe_detail, index_edges, inspect_detail

GOOD = "/application/UTK02/UTK0201_00.aspx?PRODUCT_ID=ABC123"
TITLE = "臺北國際文化年度演出"

class Cases(unittest.TestCase):
    def test_good(self):
        self.assertIsNotNone(safe_detail(GOOD))
    def test_external(self):
        self.assertIsNone(safe_detail("https://evil.example" + GOOD))
    def test_http(self):
        self.assertIsNone(safe_detail("http://tickets.udnfunlife.com" + GOOD))
    def test_credentials(self):
        self.assertIsNone(safe_detail("https://x@tickets.udnfunlife.com" + GOOD))
    def test_no_id(self):
        self.assertIsNone(safe_detail("/application/UTK02/UTK0201_00.aspx"))
    def test_duplicate_id(self):
        self.assertIsNone(safe_detail(GOOD + "&PRODUCT_ID=BAD"))
    def test_wrong_path(self):
        self.assertIsNone(safe_detail("/application/UTK01/UTK0101_03.aspx?PRODUCT_ID=ABC"))
    def test_fragment(self):
        self.assertIsNone(safe_detail(GOOD + "#spoof"))
    def test_candidate(self):
        self.assertEqual(len(index_edges('<a href="' + GOOD + '">' + TITLE + '</a>')), 1)
    def test_conflicting_title(self):
        h = '<a href="' + GOOD + '">' + TITLE + '</a><a href="' + GOOD + '">另一場活動</a>'
        self.assertEqual(index_edges(h), [])
    def test_generic(self):
        self.assertEqual(index_edges('<a href="' + GOOD + '">立即購票</a>'), [])
    def test_exact(self):
        d = inspect_detail("<h1>" + TITLE + "</h1>", TITLE)
        self.assertEqual(d["decision"], "REVIEW_SAME_PRODUCT_EXACT_TITLE_NO_FIELDS")
        self.assertEqual(d["acceptedFields"], 0)
    def test_mismatch(self):
        self.assertEqual(inspect_detail("<h1>其他活動</h1>", TITLE)["decision"], "HOLD_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_ambiguous(self):
        self.assertEqual(inspect_detail("<h1>" + TITLE + "</h1><h2>" + TITLE + "</h2>", TITLE)["decision"], "HOLD_TITLE_MISMATCH_OR_AMBIGUITY")

if __name__ == "__main__":
    unittest.main()

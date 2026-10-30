#!/usr/bin/env python3
"""P30-VENUE-02U Fuzhong15 screening identity and date-role negative tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02u_fuzhong15_sessions import safe_detail, index_edges, inspect_detail

GOOD = "/xcmovie/cont?sid=0Q123&xsmsid=0M361641875264878260"
TITLE = "我在荒野做了一場夢"

class Cases(unittest.TestCase):
    def test_good(self):
        self.assertIsNotNone(safe_detail(GOOD))
    def test_external(self):
        self.assertIsNone(safe_detail("https://evil.example" + GOOD))
    def test_http(self):
        self.assertIsNone(safe_detail("http://www.fuzhong15.ntpc.gov.tw" + GOOD))
    def test_credentials(self):
        self.assertIsNone(safe_detail("https://x@www.fuzhong15.ntpc.gov.tw" + GOOD))
    def test_protocol_relative(self):
        self.assertIsNone(safe_detail("//www.fuzhong15.ntpc.gov.tw" + GOOD))
    def test_wrong_page(self):
        self.assertIsNone(safe_detail("/xcmovie?XsmSId=0M361641875264878260"))
    def test_missing_sid(self):
        self.assertIsNone(safe_detail("/xcmovie/cont?xsmsid=0M361641875264878260"))
    def test_wrong_list(self):
        self.assertIsNone(safe_detail("/xcmovie/cont?sid=0Q123&xsmsid=WRONG"))
    def test_duplicate_sid(self):
        self.assertIsNone(safe_detail(GOOD + "&sid=0Q456"))
    def test_candidate(self):
        self.assertEqual(len(index_edges('<a href="' + GOOD + '">' + TITLE + '</a>')), 1)
    def test_conflict(self):
        h = '<a href="' + GOOD + '">' + TITLE + '</a><a href="' + GOOD + '">完全不同電影</a>'
        self.assertEqual(index_edges(h), [])
    def test_generic(self):
        self.assertEqual(index_edges('<a href="' + GOOD + '">更多</a>'), [])
    def test_exact_date_role(self):
        d = inspect_detail("<h3>" + TITLE + "</h3><div>放映日期：</div><div>2026/10/30 18:40</div>", TITLE)
        self.assertEqual(d["decision"], "REVIEW_EXACT_SCREENING_TITLE_AND_DATE_ROLE_NO_FIELDS")
        self.assertEqual(d["acceptedFields"], 0)
    def test_no_date(self):
        self.assertEqual(inspect_detail("<h3>" + TITLE + "</h3><div>更新日期：2026/10/02</div>", TITLE)["decision"], "HOLD_TITLE_OR_DATE_ROLE_AMBIGUOUS")
    def test_duplicate_date(self):
        h = "<h3>" + TITLE + "</h3><p>放映日期</p><p>放映日期</p>"
        self.assertEqual(inspect_detail(h, TITLE)["decision"], "HOLD_TITLE_OR_DATE_ROLE_AMBIGUOUS")
    def test_mismatch(self):
        self.assertEqual(inspect_detail("<h3>其他電影</h3><p>放映日期</p>", TITLE)["decision"], "HOLD_TITLE_OR_DATE_ROLE_AMBIGUOUS")

if __name__ == "__main__":
    unittest.main()

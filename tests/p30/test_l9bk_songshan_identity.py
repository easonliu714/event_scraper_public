#!/usr/bin/env python3
"""Fail-closed Songshan #14 same-path list/detail identity regression."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9bk_songshan_identity import index_edges,inspect,safe_detail
URL="/exhibition/activity/9b124255-1672-40fa-99de-225e16299486"
TITLE="GIGABYTE 40 週年品牌特展"
def index(title=TITLE,url=URL):
    return f'<main><a href="{url}">{title} 2026-10-29 - 2026-11-01</a></main>'
def detail(title=TITLE):
    return f'<main><h1>{title}</h1><p>日期</p><p>2026-10-29 - 2026-11-01</p></main>'
class Cases(unittest.TestCase):
    def test_exact_review(self):
        x=inspect(index(),detail())
        self.assertEqual(x["decision"],"REVIEW_SAME_ACTIVITY_PATH_TITLE_NO_FIELDS")
        self.assertEqual(x["exactTitleMatches"],1)
        self.assertEqual(x["acceptedFields"],0)
        self.assertIsNone(x["ticketEventId"])
    def test_title_mismatch(self):
        self.assertEqual(inspect(index(),detail("另一活動"))["decision"],"HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_duplicate_detail_heading(self):
        self.assertEqual(inspect(index(),detail()+f"<h2>{TITLE}</h2>")["decision"],"HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_conflicting_list_title(self):
        self.assertEqual(inspect(index()+index("另一活動"),detail())["decision"],"HOLD_LIST_TITLE_CONFLICT_OR_ZERO")
    def test_no_source_link(self):
        self.assertEqual(inspect('<a href="https://evil.example/x">x</a>',detail())["decision"],"HOLD_LIST_TITLE_CONFLICT_OR_ZERO")
    def test_reject_http(self):
        self.assertIsNone(safe_detail("http://www.songshanculturalpark.org"+URL))
    def test_reject_cross_domain(self):
        self.assertIsNone(safe_detail("https://evil.example"+URL))
    def test_reject_query(self):
        self.assertIsNone(safe_detail(URL+"?redirect=x"))
    def test_reject_fragment(self):
        self.assertIsNone(safe_detail(URL+"#x"))
    def test_reject_aggregate(self):
        self.assertEqual(index_edges(index("11月展演攻略"))[0],[])
    def test_reject_unbounded_date_role(self):
        x=inspect(index(),detail()+ "<p>活動日期：A</p><p>活動日期：B</p>")
        self.assertEqual(x["decision"],"HOLD_MULTIPLE_ACTIVITY_DATE_ROLES")
    def test_single_date_role_still_review(self):
        self.assertEqual(inspect(index(),detail()+"<p>活動日期：2026/10/29</p>")["decision"],"REVIEW_SAME_ACTIVITY_PATH_TITLE_NO_FIELDS")
if __name__=="__main__":
    unittest.main()

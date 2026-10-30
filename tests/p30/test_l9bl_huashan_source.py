#!/usr/bin/env python3
"""Huashan #13 source-derived identity and strict role regression."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9bl_huashan_source import safe_detail,edges,inspect
U="/exhibition/123456"
T="華山獨立展覽測試"
def idx(title=T,url=U):
    return f'<main><a href="{url}">{title}</a></main>'
def detail(title=T):
    return f'<main><h2>{title}</h2><p>展覽日期：2026/10/30</p></main>'
class Cases(unittest.TestCase):
    def test_identity_review(self):
        a=inspect(idx(),detail())
        self.assertEqual(a["decision"],"REVIEW_HUASHAN_EXACT_TITLE_NO_FIELDS")
        self.assertEqual(a["acceptedFields"],0)
        self.assertIsNone(a["ticketEventId"])
    def test_wrong_title(self):
        self.assertEqual(inspect(idx(),detail("不同標題"))["decision"],"HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_duplicate_heading(self):
        self.assertEqual(inspect(idx(),detail()+f"<h1>{T}</h1>")["decision"],"HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_date_role_conflict(self):
        self.assertEqual(inspect(idx(),detail()+"<p>活動日期：2026/11/01</p>")["decision"],"HOLD_DATE_ROLE_AMBIGUITY")
    def test_title_conflict(self):
        self.assertEqual(inspect(idx()+idx("其他展覽"),detail())["decision"],"HOLD_LIST_ZERO_OR_TITLE_CONFLICT")
    def test_reject_cross_domain(self):
        self.assertIsNone(safe_detail("https://evil.example/exhibition/123456"))
    def test_reject_http(self):
        self.assertIsNone(safe_detail("http://www.huashan1914.com/exhibition/123456"))
    def test_reject_query(self):
        self.assertIsNone(safe_detail(U+"?redirect=evil"))
    def test_reject_fragment(self):
        self.assertIsNone(safe_detail(U+"#frag"))
    def test_reject_aggregate(self):
        self.assertEqual(edges(idx("活動總覽"))[0],[])
    def test_no_implicit_identity(self):
        self.assertEqual(inspect('<a href="/other/123">x</a>',detail())["decision"],"HOLD_LIST_ZERO_OR_TITLE_CONFLICT")
if __name__=="__main__":
    unittest.main()

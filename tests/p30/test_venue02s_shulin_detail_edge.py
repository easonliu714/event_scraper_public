#!/usr/bin/env python3
"""VENUE-02S strict same-origin detail selection and title parity, no accepted fields."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02s_shulin_detail_edge import detail_candidates,inspect_detail
class Cases(unittest.TestCase):
    def test_one_same_origin(self):
        h='<a href="/shulin_artcenter_chi/xmdoc/cont?xsmsid=abc&sid=123">秋季音樂會演出</a>'
        self.assertEqual(len(detail_candidates(h)),1)
    def test_no_external(self):
        self.assertEqual(detail_candidates('<a href="https://evil.example/xmdoc/cont?sid=123&xsmsid=abc">秋季音樂會演出</a>'),[])
    def test_no_http(self):
        self.assertEqual(detail_candidates('<a href="http://www.culture.ntpc.gov.tw/xmdoc/cont?sid=123&xsmsid=abc">秋季音樂會演出</a>'),[])
    def test_missing_sid(self):
        self.assertEqual(detail_candidates('<a href="/xmdoc/cont?xsmsid=abc">秋季音樂會演出</a>'),[])
    def test_generic_label(self):
        self.assertEqual(detail_candidates('<a href="/xmdoc/cont?sid=1&xsmsid=a">詳細內容</a>'),[])
    def test_exact_title_review(self):
        x=inspect_detail("<h1>秋季音樂會演出</h1>","秋季音樂會演出")
        self.assertEqual(x["decision"],"REVIEW_EXACT_INDEX_DETAIL_TITLE_NO_EVENT_ID")
        self.assertEqual(x["acceptedFields"],0)
    def test_mismatch_hold(self):
        self.assertEqual(inspect_detail("<h1>別的活動</h1>","秋季音樂會演出")["decision"],"HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_duplicate_heading_hold(self):
        self.assertEqual(inspect_detail("<h1>秋季音樂會演出</h1><h2>秋季音樂會演出</h2>","秋季音樂會演出")["decision"],"HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
if __name__=="__main__": unittest.main()

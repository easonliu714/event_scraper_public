#!/usr/bin/env python3
"""VENUE-02P index/detail exact-title refusal tests; no network."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02p_xinzhuang_detail_parity import select_candidate,inspect_detail

class Cases(unittest.TestCase):
    def test_exact_index_detail_heading_review_only(self):
        x=inspect_detail("<h1>展演活動：音樂會</h1>","展演活動：音樂會")
        self.assertEqual(x["decision"],"REVIEW_EXACT_INDEX_DETAIL_TITLE_NO_EVENT_ID_NO_FIELDS")
    def test_wrong_heading_hold(self):
        self.assertEqual(inspect_detail("<h1>其他活動</h1>","展演活動：音樂會")["decision"],"HOLD_INDEX_DETAIL_TITLE_NOT_EXACT_UNIQUE")
    def test_duplicate_heading_hold(self):
        self.assertEqual(inspect_detail("<h1>展演活動：音樂會</h1><h2>展演活動：音樂會</h2>","展演活動：音樂會")["decision"],"HOLD_INDEX_DETAIL_TITLE_NOT_EXACT_UNIQUE")
    def test_same_origin_candidate(self):
        s,m=select_candidate('<a href="/xmdoc/cont?xsmsid=abc">展演活動：音樂會</a>')
        self.assertIsNotNone(s)
        self.assertEqual(m["candidateLinks"],1)
        self.assertEqual(m["candidateQueryKeys"],["xsmsid"])
        self.assertNotIn("abc",str(m))
    def test_external_rejected(self):
        s,m=select_candidate('<a href="https://evil.example/xmdoc/cont?xsmsid=abc">展演活動：音樂會</a>')
        self.assertIsNone(s)
    def test_http_rejected(self):
        s,m=select_candidate('<a href="http://www.xzcac.ntpc.gov.tw/xmdoc/cont?xsmsid=abc">展演活動：音樂會</a>')
        self.assertIsNone(s)
    def test_conflicting_titles_rejected(self):
        s,m=select_candidate('<a href="/xmdoc/cont?xsmsid=abc">展演活動：音樂會</a><a href="/xmdoc/cont?xsmsid=abc">展演活動：舞蹈會</a>')
        self.assertIsNone(s)
        self.assertEqual(m["decision"],"HOLD_LINK_TITLE_CONFLICT")
    def test_short_label_rejected(self):
        s,m=select_candidate('<a href="/xmdoc/cont?xsmsid=abc">展演</a>')
        self.assertIsNone(s)
    def test_nav_rejected(self):
        s,m=select_candidate('<a href="/contact">聯絡我們</a>')
        self.assertIsNone(s)
if __name__=="__main__":unittest.main()

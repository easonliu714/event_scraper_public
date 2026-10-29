#!/usr/bin/env python3
"""VENUE-02H: strict live parser and same-period distinct-event regression."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02h_tainex_live_identity import inspect_html_pair,compare_distinct_records

LIST='<a href="/event/689">1館 2026 11/13-11/16 2026臺灣國際咖啡展</a>'
DETAIL='<h1>2026臺灣國際咖啡展</h1><h2>展覽活動期間</h2>2026 11.13-11.16<h2>活動地點</h2>一樓展場<h2>主辦單位</h2>展昭國際'
class TainexLiveTests(unittest.TestCase):
    def check(self,l=LIST,d=DETAIL,decision=None):
        r=inspect_html_pair(l,d)
        if decision:
            self.assertEqual(r["decision"],decision)
        self.assertEqual((r["acceptedFields"],r["goldenAccepted"],r["published"]),(0,0,False))
        self.assertIsNone(r["ticketEventId"])
        self.assertEqual(r["releaseState"],"HARD_HOLD_NO_PUBLICATION")
        return r
    def test_exact_same_source_link_heading(self):
        r=self.check(decision="REVIEW_LIVE_LIST_DETAIL_IDENTITY_NO_PROMOTION")
        self.assertEqual(r["venueLocalIdReview"],"689")
    def test_duplicate_link(self):
        self.check(l=LIST+LIST,decision="HOLD_LIST_ANCHOR_NOT_UNIQUE")
    def test_no_link(self):
        self.check(l=LIST.replace("/event/689","/event/690"),decision="HOLD_LIST_ANCHOR_NOT_UNIQUE")
    def test_other_host(self):
        self.check(l=LIST.replace("/event/689","https://evil.example/event/689"),decision="HOLD_LIST_ANCHOR_NOT_UNIQUE")
    def test_wrong_list_title(self):
        self.check(l=LIST.replace("咖啡展","茶業博覽會"),decision="HOLD_LIST_ANCHOR_NOT_UNIQUE")
    def test_wrong_detail_title(self):
        self.check(d=DETAIL.replace("咖啡展","茶業博覽會"),decision="HOLD_DETAIL_TITLE_NOT_UNIQUE")
    def test_duplicate_detail_title(self):
        self.check(d=DETAIL+"<h2>2026臺灣國際咖啡展</h2>",decision="HOLD_DETAIL_TITLE_NOT_UNIQUE")
    def test_missing_period_label(self):
        self.check(d=DETAIL.replace("展覽活動期間","活動日期"),decision="HOLD_MISSING_DETAIL_ROLE_LABEL")
    def test_missing_organizer(self):
        self.check(d=DETAIL.replace("主辦單位","主辦"),decision="HOLD_MISSING_DETAIL_ROLE_LABEL")
    def test_empty(self):
        self.check(l="",decision="HOLD_INPUT")
    def test_body_cap(self):
        self.check(d=DETAIL+"x"*180001,decision="HOLD_INPUT")
    def test_distinct_ids_same_date_hall_organizer(self):
        tea=dict(url="https://www.tainex.com.tw/event/690",period="2026-11-13~16",hall="1館",organizer="展昭")
        coffee={**tea,"url":"https://www.tainex.com.tw/event/689"}
        self.assertEqual(compare_distinct_records(tea,coffee),"REVIEW_DISTINCT_VENUE_LOCAL_IDS_NO_MERGE")
    def test_same_id_not_two_events(self):
        a=dict(url="https://www.tainex.com.tw/event/689")
        self.assertEqual(compare_distinct_records(a,a),"HOLD_SAME_VENUE_LOCAL_ID")
    def test_foreign_id(self):
        self.assertEqual(compare_distinct_records({"url":"https://evil.example/event/689"},{"url":"https://www.tainex.com.tw/event/690"}),"HOLD_SOURCE_URL")
if __name__=="__main__":
    unittest.main()

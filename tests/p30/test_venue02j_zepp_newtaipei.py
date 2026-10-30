#!/usr/bin/env python3
"""P30-VENUE-02J offline strict source and role refusals."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02j_zepp_newtaipei import inspect,DETAIL
L=f'<a href="{DETAIL}">2026 10.30 40 Fingers START 19:30 READ MORE</a>'
D='<h2>FORTY FINGERS ASIAN TOUR 2026</h2><h3>40 Fingers</h3><p>[START] 19:30</p><p>チケット販売 KKTIX</p>'
class Cases(unittest.TestCase):
    def check(self,listing,detail,decision):
        x=inspect(listing,detail,"2026-10-30T00:00:00Z")
        self.assertEqual(x["decision"],decision)
        self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
        self.assertIsNone(x["ticketEventId"])
        self.assertEqual(x["releaseState"],"HARD_HOLD_NO_PUBLICATION")
        return x
    def test_review(self):
        x=self.check(L,D,"REVIEW_ZEPP_SAME_RID_LIST_DETAIL_NO_FIELDS")
        self.assertEqual(x["roleDecisions"]["TICKET"],"VENUE_CLAIMED_KKTIX_NOT_VERIFIED_TICKET_EVENT_ID")
    def test_wrong_rid(self):self.check(L.replace("162473","162474"),D,"HOLD_LIST_RID_OR_TITLE")
    def test_wrong_title(self):self.check(L.replace("40 Fingers","Other"),D,"HOLD_LIST_RID_OR_TITLE")
    def test_duplicate_rid(self):self.check(L+L,D,"HOLD_LIST_RID_OR_TITLE")
    def test_other_domain(self):self.check(L.replace("www.zepp.co.jp","evil.example"),D,"HOLD_LIST_RID_OR_TITLE")
    def test_missing_detail_title(self):self.check(L,D.replace("<h3>40 Fingers</h3>",""),"HOLD_DETAIL_ARTIST_NOT_UNIQUE")
    def test_duplicate_detail_title(self):self.check(L,D+"<h3>40 Fingers</h3>","HOLD_DETAIL_ARTIST_NOT_UNIQUE")
    def test_realistic_300kb_body(self):self.check(L+" "*300000,D,"REVIEW_ZEPP_SAME_RID_LIST_DETAIL_NO_FIELDS")\n    def test_oversize_513kb(self):self.check(L+" "*513000,D,"HOLD_INPUT")\n    def test_missing_start(self):self.check(L,D.replace("19:30",""),"HOLD_START_ROLE_UNVERIFIED")
if __name__=="__main__":unittest.main()

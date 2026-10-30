#!/usr/bin/env python3
"""Source-observed distinct Ceramics SID/title/date evidence, no cross-ID fields."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02ac_ceramics_sid_title import audit_sid_title as audit

SID1="0Q218338899799849722"
SID2="0Q238554544743104681"
T1="山彩疊疊-唐榕個展"
T2="殼之巢 — 情景之階：佐藤雅之個展"
D1="展覽日期:2026年10月16日至2026年11月15日/展覽地點:b1陶藝長廊"
D2="展覽日期：2026年10月13日至2026年11月10日"
V2="展覽地點：1樓陽光特展室"
def url(sid): return "https://www.ceramics.ntpc.gov.tw/xmdoc/cont?sid="+sid+"&xsmsid=0J148497613881029302"
def page(title,body): return f"<main><h3>{title}</h3><article><p>{body}</p></article></main>"
class Cases(unittest.TestCase):
    def test_official_first_sid_title_inline_fields_review(self):
        r=audit(url(SID1),page(T1,D1),SID1,T1)
        self.assertEqual(r["decision"],"REVIEW_SAME_SID_TITLE_FIELD_ROLES_NOT_ACCEPTED")
        self.assertTrue(r["sidBound"])
        self.assertEqual(r["acceptedFields"],0)
    def test_official_second_sid_title_separate_fields_review(self):
        r=audit(url(SID2),page(T2,D2+"</p><p>"+V2),SID2,T2)
        self.assertEqual(r["decision"],"REVIEW_SAME_SID_TITLE_FIELD_ROLES_NOT_ACCEPTED")
    def test_prior_ab_cross_sid_title_fixture_rejected(self):
        r=audit(url(SID1),page(T2,D1),SID1,T2)
        self.assertEqual(r["decision"],"HOLD_SOURCE_SID_TITLE_PAIR_CONFLICT")
    def test_detail_heading_from_other_sid_rejected(self):
        r=audit(url(SID1),page(T2,D1),SID1,T1)
        self.assertEqual(r["decision"],"HOLD_DETAIL_TITLE_NOT_BOUND_TO_SID")
    def test_swapped_sid_url_rejected(self):
        self.assertEqual(audit(url(SID2),page(T1,D1),SID1,T1)["decision"],"HOLD_UNSAFE_OR_UNBOUND_DETAIL_SID")
    def test_duplicate_sid_query_rejected(self):
        self.assertEqual(audit(url(SID1)+"&sid="+SID2,page(T1,D1),SID1,T1)["decision"],"HOLD_UNSAFE_OR_UNBOUND_DETAIL_SID")
    def test_wrong_category_rejected(self):
        self.assertEqual(audit(url(SID1).replace("0J148497613881029302","wrong"),page(T1,D1),SID1,T1)["decision"],"HOLD_UNSAFE_OR_UNBOUND_DETAIL_SID")
    def test_foreign_host_rejected(self):
        self.assertEqual(audit(url(SID1).replace("www.ceramics.ntpc.gov.tw","evil.example"),page(T1,D1),SID1,T1)["decision"],"HOLD_UNSAFE_OR_UNBOUND_DETAIL_SID")
    def test_unknown_sid_rejected(self):
        sid="0Q000000000000000000"
        self.assertEqual(audit(url(sid),page(T1,D1),sid,T1)["decision"],"HOLD_SID_NOT_IN_BOUNDED_OFFICIAL_SAMPLE")
    def test_conflicting_venue_stays_hold(self):
        r=audit(url(SID1),page(T1,D1+"</p><p>展覽地點：二樓展廳"),SID1,T1)
        self.assertTrue(r["decision"].startswith("HOLD_FIELD_ROLE_"))
    def test_missing_date_stays_hold(self):
        r=audit(url(SID1),page(T1,"展覽地點：b1陶藝長廊"),SID1,T1)
        self.assertTrue(r["decision"].startswith("HOLD_FIELD_ROLE_"))
    def test_never_ticket_or_publish(self):
        r=audit(url(SID1),page(T1,D1),SID1,T1)
        self.assertIsNone(r["ticketEventId"])
        self.assertFalse(r["published"])
        self.assertEqual(r["goldenAccepted"],0)
if __name__=="__main__": unittest.main()

#!/usr/bin/env python3
"""VENUE-02AG distinct official SID / two role layout regression tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02ag_ceramics_two_sid_roles import inspect_one, inspect_two
ROOT="https://www.ceramics.ntpc.gov.tw/xmdoc/cont?sid="
TAIL="&xsmsid=0J148497613881029302"
S1="0Q218338899799849722"
S2="0Q238554544743104681"
T1="山彩疊疊-唐榕個展"
T2="殼之巢 — 情景之階：佐藤雅之個展"
STAMP="2026-10-30T23:58:00Z"
def rec(sid, title, body):
    return dict(sid=sid, title=title, url=ROOT+sid+TAIL,
                html="<main><h3>"+title+"</h3>"+body+"</main>", observed_at=STAMP)
def samples():
    a=rec(S1,T1,"<p>展覽日期:2026年10月16日至2026年11月15日/展覽地點:b1陶藝長廊</p>")
    b=rec(S2,T2,"<p>展覽日期：2026年10月13日至2026年11月10日</p><p>展覽地點：1樓陽光特展室</p>")
    return a,b
class Cases(unittest.TestCase):
    def test_two_source_observed_role_layouts_are_distinct_review(self):
        a,b=samples()
        x=inspect_two([a,b])
        self.assertEqual(x["decision"],"REVIEW_TWO_DISTINCT_EXHIBITION_SIDS_NO_FIELD_ACCEPTANCE")
        self.assertEqual(x["distinctSIDs"],2)
        self.assertEqual(x["candidateFieldCount"],4)
        self.assertEqual(x["acceptedFields"],0)
        self.assertEqual(x["goldenAccepted"],0)
    def test_one_inline_role_pair_review_only(self):
        a,_=samples()
        x=inspect_one(**a)
        self.assertEqual(x["decision"],"REVIEW_EXACT_SID_DATE_AND_VENUE_CANDIDATES")
        self.assertEqual(x["roleNodes"],1)
        self.assertEqual(len(x["candidateProvenance"]),2)
    def test_two_separate_role_nodes_review_only(self):
        _,b=samples()
        x=inspect_one(**b)
        self.assertEqual(x["roleNodes"],2)
        self.assertEqual(x["dateCandidates"],1)
    def test_cross_sid_title_refused(self):
        a,b=samples(); a["title"]=b["title"]
        self.assertEqual(inspect_one(**a)["decision"],"HOLD_CROSS_SID_TITLE")
    def test_cross_sid_url_refused(self):
        a,b=samples(); a["url"]=b["url"]
        self.assertEqual(inspect_one(**a)["decision"],"HOLD_SID_OR_HEADING_IDENTITY")
    def test_duplicate_sid_refused(self):
        a,_=samples()
        self.assertEqual(inspect_two([a,a])["decision"],"HOLD_DUPLICATE_OR_UNBOUNDED_SID")
    def test_invalid_date_refused(self):
        a,_=samples(); a["html"]=a["html"].replace("10月16日","10月32日")
        self.assertEqual(inspect_one(**a)["decision"],"HOLD_INVALID_DATE")
    def test_reversed_date_refused(self):
        a,_=samples(); a["html"]=a["html"].replace("10月16日","12月16日")
        self.assertEqual(inspect_one(**a)["decision"],"HOLD_REVERSED_DATE_RANGE")
    def test_duplicate_role_refused(self):
        a,_=samples(); a["html"]=a["html"].replace("</main>","<p>展覽地點:另一展廳</p></main>")
        self.assertEqual(inspect_one(**a)["decision"],"HOLD_DUPLICATE_OR_MISSING_ROLE")
    def test_registration_not_venue(self):
        a,_=samples(); a["html"]=a["html"].replace("b1陶藝長廊","報名日期2026年10月16日")
        self.assertEqual(inspect_one(**a)["decision"],"HOLD_MIXED_OR_UNLABELED_ROLE_TEXT")
    def test_no_implicit_publication(self):
        a,b=samples(); x=inspect_two([a,b])
        self.assertFalse(x["published"])
        self.assertIsNone(x["ticketEventId"])
if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""VENUE-02AD: exact selected Ceramics SID fixture and bounded source roles."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02ad_ceramics_live_sid_probe import inspect_detail, URL, TITLE

OTHER="殼之巢 — 情景之階：佐藤雅之個展"
DATE="展覽日期:2026年10月16日至2026年11月15日/展覽地點:b1陶藝長廊"
def page(title=TITLE,body=DATE):
    return "<main><h3>"+title+"</h3><article><p>"+body+"</p></article></main>"

class Cases(unittest.TestCase):
    def test_corrected_same_sid_title_review(self):
        r=inspect_detail(page())
        self.assertEqual(r["decision"],"REVIEW_EXACT_SID_TITLE_FIELD_CANDIDATES_NOT_ACCEPTED")
        self.assertTrue(r["sidBound"])
        self.assertEqual(r["acceptedFields"],0)
        self.assertFalse(r["published"])
    def test_prior_cross_sid_title_holds(self):
        self.assertEqual(inspect_detail(page(OTHER))["decision"],"HOLD_SOURCE_IDENTITY_OR_FIELD_ROLE")
    def test_missing_date_holds(self):
        self.assertEqual(inspect_detail(page(body="展覽地點：b1陶藝長廊"))["decision"],"HOLD_SOURCE_IDENTITY_OR_FIELD_ROLE")
    def test_conflicting_venue_holds(self):
        self.assertEqual(inspect_detail(page(body=DATE+"</p><p>展覽地點：二樓展廳"))["decision"],"HOLD_SOURCE_IDENTITY_OR_FIELD_ROLE")
    def test_wrong_sid_url_holds(self):
        self.assertEqual(inspect_detail(page(),detail_url=URL.replace("0Q218338899799849722","0Q238554544743104681"))["decision"],"HOLD_SOURCE_IDENTITY_OR_FIELD_ROLE")
    def test_no_ticket_or_golden(self):
        r=inspect_detail(page())
        self.assertIsNone(r["ticketEventId"])
        self.assertEqual(r["goldenAccepted"],0)
        self.assertEqual(r["releaseState"],"HARD_HOLD_NO_PUBLICATION")
if __name__=="__main__":unittest.main()

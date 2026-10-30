#!/usr/bin/env python3
"""VENUE-02AE: exact SID leaf role diagnostic, fail-closed."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02ae_ceramics_role_node_cause import diagnose
TITLE="山彩疊疊-唐榕個展"
DATE="展覽日期:2026年10月16日至2026年11月15日"
VENUE="展覽地點:b1陶藝長廊"
def page(*nodes,title=TITLE):
    return "<main><h3>"+title+"</h3><article>"+"".join("<p>"+n+"</p>" for n in nodes)+"</article></main>"
class Cases(unittest.TestCase):
    def test_clean_inline_review_only(self):
        r=diagnose(page(DATE+"/"+VENUE))
        self.assertEqual(r["decision"],"REVIEW_SOURCE_LOCAL_ROLES_NO_FIELD_ACCEPTANCE")
        self.assertEqual(r["inlineBothRoleNodes"],1)
        self.assertEqual(r["acceptedFields"],0)
    def test_separate_lines_review_only(self):
        r=diagnose(page(DATE,VENUE))
        self.assertEqual(r["decision"],"REVIEW_SOURCE_LOCAL_ROLES_NO_FIELD_ACCEPTANCE")
        self.assertEqual(r["dateRoleTextNodes"],1)
        self.assertEqual(r["venueRoleTextNodes"],1)
    def test_cross_sid_title_holds(self):
        self.assertEqual(diagnose(page(DATE,VENUE,title="殼之巢"))["decision"],"HOLD_SID_OR_TITLE_IDENTITY")
    def test_duplicate_same_venue_holds(self):
        r=diagnose(page(DATE,VENUE,VENUE))
        self.assertEqual(r["decision"],"HOLD_DUPLICATE_ROLE_NODE_OWNERSHIP")
    def test_missing_date_holds(self):
        self.assertEqual(diagnose(page(VENUE))["decision"],"HOLD_FIELD_ROLE_UNRESOLVED_NO_PROMOTION")
    def test_bad_date_holds(self):
        self.assertEqual(diagnose(page("展覽日期:未定",VENUE))["decision"],"HOLD_REGEX_OR_INLINE_NODE_OWNERSHIP")
    def test_sale_mixed_holds(self):
        r=diagnose(page(DATE+"/"+VENUE+"/售票日期:明日"))
        self.assertEqual(r["decision"],"HOLD_MIXED_ROLE_TEXT_NODE")
    def test_no_ticket_id(self):
        r=diagnose(page(DATE,VENUE))
        self.assertIsNone(r["ticketEventId"])
        self.assertFalse(r["published"])
        self.assertEqual(r["goldenAccepted"],0)
if __name__=="__main__":unittest.main()

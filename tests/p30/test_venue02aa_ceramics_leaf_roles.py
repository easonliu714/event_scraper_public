#!/usr/bin/env python3
"""Regression: long narrative + local exhibition date and venue text node."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02aa_ceramics_leaf_roles import leaf_role_candidates, diagnose
U="/xmdoc/cont?sid=0Q218338899799849722&xsmsid=0J148497613881029302"
TITLE="山彩疊疊-唐榕個展"
INDEX=f'<a href="{U}"><img alt="標題：{TITLE}"></a>'
def detail(tail="展覽日期:2026年10月16日至2026年11月15日/展覽地點:b1陶藝長廊"):
    return f'<h3>{TITLE}</h3><p>{"自然山水的陶藝表現。"*45}{tail}</p>'
class Cases(unittest.TestCase):
    def test_long_narrative_local_leaf(self):
        dates,places,truncated=leaf_role_candidates(detail())
        self.assertEqual(dates,[("2026-10-16","2026-11-15")])
        self.assertEqual(places,["b1陶藝長廊"])
        self.assertEqual(truncated,0)
    def test_identity_and_role_review_only(self):
        a=diagnose(INDEX,detail())
        self.assertEqual(a["decision"],"REVIEW_LEAF_LOCAL_RANGE_VENUE_NOT_ACCEPTED")
        self.assertEqual(a["acceptedFields"],0)
        self.assertFalse(a["published"])
    def test_conflicting_venues(self):
        a=diagnose(INDEX,detail()+"<p>展覽地點:二樓展廳</p>")
        self.assertEqual(a["decision"],"HOLD_VENUE_LEAF_MISSING_OR_AMBIGUOUS")
    def test_invalid_date(self):
        a=diagnose(INDEX,detail("展覽日期:2026年2月30日至2026年3月15日/展覽地點:b1陶藝長廊"))
        self.assertEqual(a["decision"],"HOLD_DATE_RANGE_LEAF_MISSING_INVALID_OR_AMBIGUOUS")
    def test_inverted_date(self):
        a=diagnose(INDEX,detail("展覽日期:2026年11月16日至2026年10月15日/展覽地點:b1陶藝長廊"))
        self.assertEqual(a["decision"],"HOLD_DATE_RANGE_LEAF_MISSING_INVALID_OR_AMBIGUOUS")
    def test_registration_mixed(self):
        a=diagnose(INDEX,detail()+"<p>報名期間:2026年10月1日</p>")
        self.assertEqual(a["decision"],"HOLD_PRIOR_IDENTITY_OR_ROLE")
    def test_duplicate_date(self):
        a=diagnose(INDEX,detail()+"<p>展覽日期:2026年10月16日至2026年11月15日</p>")
        self.assertEqual(a["decision"],"HOLD_PRIOR_IDENTITY_OR_ROLE")
    def test_no_global_footer_venue(self):
        a=diagnose(INDEX,detail("展覽日期:2026年10月16日至2026年11月15日"))
        self.assertEqual(a["decision"],"HOLD_VENUE_LEAF_MISSING_OR_AMBIGUOUS")
    def test_split_tag_fail_closed(self):
        a=diagnose(INDEX,f'<h3>{TITLE}</h3><p>展覽日期:<b>2026年10月16日至2026年11月15日</b>展覽地點:b1陶藝長廊</p>')
        self.assertEqual(a["decision"],"HOLD_DATE_RANGE_LEAF_MISSING_INVALID_OR_AMBIGUOUS")
    def test_no_accepted_ticket_id(self):
        self.assertIsNone(diagnose(INDEX,detail())["ticketEventId"])
if __name__=="__main__":
    unittest.main()

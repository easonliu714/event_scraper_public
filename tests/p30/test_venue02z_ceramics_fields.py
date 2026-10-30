#!/usr/bin/env python3
"""Ceramics #P0 exhibition date-range/location role negative regression."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02z_ceramics_fields import inspect_range,bounded_roles
URL="/xmdoc/cont?sid=0Q218338899799849722&xsmsid=0J148497613881029302"
TITLE="山彩疊疊-唐榕個展"
def index():
    return f'<a href="{URL}"><img alt="標題：{TITLE}"></a>'
def detail(t=TITLE,body="展覽日期：2026年10月16日至2026年11月15日/展覽地點：B1陶藝長廊"):
    return f'<h3>{t}</h3><p>{body}</p>'
class Cases(unittest.TestCase):
    def test_review_both_roles_not_accepted(self):
        a=inspect_range(index(),detail())
        self.assertEqual(a["decision"],"REVIEW_EXACT_EXHIBITION_RANGE_VENUE_NO_FIELDS")
        self.assertEqual(a["acceptedFields"],0)
        self.assertEqual(len(a["fieldProvenance"]),2)
        self.assertIsNone(a["ticketEventId"])
    def test_missing_venue(self):
        self.assertEqual(inspect_range(index(),detail(body="展覽日期：2026年10月16日至2026年11月15日"))["decision"],"HOLD_VENUE_MISSING_OR_AMBIGUOUS")
    def test_missing_date(self):
        self.assertEqual(inspect_range(index(),detail(body="展覽地點：B1陶藝長廊"))["decision"],"HOLD_DATE_RANGE_MISSING_INVALID_OR_AMBIGUOUS")
    def test_inverted_date(self):
        self.assertEqual(inspect_range(index(),detail(body="展覽日期：2026年11月16日至2026年10月15日/展覽地點：B1陶藝長廊"))["decision"],"HOLD_DATE_RANGE_MISSING_INVALID_OR_AMBIGUOUS")
    def test_invalid_calendar(self):
        self.assertEqual(inspect_range(index(),detail(body="展覽日期：2026年02月30日至2026年03月15日/展覽地點：B1陶藝長廊"))["decision"],"HOLD_DATE_RANGE_MISSING_INVALID_OR_AMBIGUOUS")
    def test_duplicate_date(self):
        self.assertEqual(inspect_range(index(),detail()+detail())["decision"],"HOLD_PRIOR_IDENTITY_OR_ROLE")
    def test_duplicate_venue(self):
        self.assertEqual(inspect_range(index(),detail(body="展覽日期：2026年10月16日至2026年11月15日/展覽地點：B1陶藝長廊/展覽地點：二樓"))["decision"],"HOLD_VENUE_MISSING_OR_AMBIGUOUS")
    def test_registration_role(self):
        self.assertEqual(inspect_range(index(),detail(body="展覽日期：2026年10月16日至2026年11月15日/展覽地點：B1陶藝長廊/報名期間：2026/10/01"))["decision"],"HOLD_PRIOR_IDENTITY_OR_ROLE")
    def test_wrong_title(self):
        self.assertEqual(inspect_range(index(),detail("其他展覽"))["decision"],"HOLD_PRIOR_IDENTITY_OR_ROLE")
    def test_no_global_ancestor(self):
        html='<div><p>展覽日期：2026年10月16日至2026年11月15日/展覽地點：B1陶藝長廊</p></div>'
        dates,places=bounded_roles(html)
        self.assertEqual(len(dates),1)
        self.assertEqual(len(places),1)
if __name__=="__main__":
    unittest.main()

#!/usr/bin/env python3
"""Ceramics role and same-sid detail negative regression, no ticket inference."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02y_ceramics_role import index_edges,inspect,safe_detail
URL="/xmdoc/cont?sid=0Q218338899799849722&xsmsid=0J148497613881029302"
TITLE="山彩疊疊-唐榕個展"
def card(title=TITLE,url=URL):
    return f'<div><a href="{url}"><img alt="標題：{title}"></a><p>展覽日期：2026年10月16日至2026年11月15日</p></div>'
def detail(title=TITLE):
    return f'<h3>{title}</h3><p>展覽日期:2026年10月16日至2026年11月15日/展覽地點:b1陶藝長廊</p>'
class Cases(unittest.TestCase):
    def test_exact_exhibition_review_only(self):
        x=inspect(card(),detail())
        self.assertEqual(x["decision"],"REVIEW_EXHIBITION_IDENTITY_ROLE_NO_FIELDS")
        self.assertEqual(x["exactTitleMatches"],1)
        self.assertEqual(x["acceptedFields"],0)
        self.assertIsNone(x["ticketEventId"])
    def test_application_excluded(self):
        self.assertEqual(inspect(card("117年申請展簡章"),detail())["decision"],"HOLD_ZERO_OR_CONFLICTING_EXHIBITION_EDGES")
    def test_mixed_roles_excluded(self):
        x=inspect(card("117年申請展簡章")+card(),detail())
        self.assertEqual(x["registrationExcludedCount"],1)
    def test_title_mismatch(self):
        self.assertEqual(inspect(card(),detail("另一展覽"))["decision"],"HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_duplicate_heading(self):
        self.assertEqual(inspect(card(),detail()+f"<h2>{TITLE}</h2>")["decision"],"HOLD_DETAIL_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_mixed_registration_role(self):
        self.assertEqual(inspect(card(),detail()+"<p>報名期間：2026/12/01</p>")["decision"],"HOLD_DATE_ROLE_MIXED_OR_AMBIGUOUS")
    def test_duplicate_exhibition_role(self):
        self.assertEqual(inspect(card(),detail()+"<p>展覽日期：2026/12/01</p>")["decision"],"HOLD_DATE_ROLE_MIXED_OR_AMBIGUOUS")
    def test_cross_domain(self):
        self.assertIsNone(safe_detail("https://evil.example"+URL))
    def test_wrong_xsmsid(self):
        self.assertIsNone(safe_detail(URL.replace("0J148497613881029302","0J000000000000000000")))
    def test_no_sid(self):
        self.assertIsNone(safe_detail("/xmdoc/cont?xsmsid=0J148497613881029302"))
    def test_query_extra(self):
        self.assertIsNone(safe_detail(URL+"&redirect=x"))
    def test_no_eligible(self):
        self.assertEqual(index_edges('<a href="https://external.example">X</a>')[0],[])
    def test_conflicting_same_sid(self):
        self.assertEqual(inspect(card()+card("不同標題"),detail())["decision"],"HOLD_ZERO_OR_CONFLICTING_EXHIBITION_EDGES")
if __name__=="__main__":
    unittest.main()

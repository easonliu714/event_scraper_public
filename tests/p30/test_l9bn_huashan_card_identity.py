#!/usr/bin/env python3
"""Source-derived Huashan index-card/date/venue versus detail H1 boundaries."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bn_huashan_card_identity import audit_card_identity

URL = "/exhibition/%E6%9C%97%E8%AE%80%E6%B2%99%E9%BE%8D-%E9%80%99%E6%A8%A3%E5%95%8A%EF%BC%81%E9%82%A3%E4%BA%9B%E7%86%9F%E6%82%89%E5%8F%88%E9%99%8C%E7%94%9F%E7%9A%84%E6%97%A5%E5%B8%B8"
TITLE = "2026華文朗讀節〖朗讀沙龍〗這樣啊！那些熟悉又陌生的日常"
def card(title=TITLE):
    return f'<a href="{URL}"><time>2026.10.31 - 2026.10.31</time><h3>{title}</h3><span>中3A館 2樓拱廳</span></a>'
def detail(title=TITLE):
    return f'<main><h1>{title}</h1><h3>活動時間：</h3><p>2026 10.31(六) 16:00 ~ 17:30</p><h3>地點：</h3><p>中3A館 2樓拱廳</p></main>'
class Cases(unittest.TestCase):
    def test_source_observed_card_title_vs_h1(self):
        r = audit_card_identity(card(), detail(), URL)
        self.assertEqual(r["decision"], "REVIEW_SAME_ROUTE_CARD_TITLE_H1_NOT_FIELDS")
        self.assertFalse(r["wholeCardTextIsTitle"])
        self.assertEqual(r["exactH1Matches"], 1)
        self.assertEqual(r["acceptedFields"], 0)
    def test_full_card_text_must_not_be_h1(self):
        self.assertNotEqual("2026.10.31 - 2026.10.31 "+TITLE+" 中3A館 2樓拱廳", TITLE)
    def test_missing_structured_title_holds(self):
        r=audit_card_identity(f'<a href="{URL}">2026.10.31 {TITLE} 中3A館</a>',detail(),URL)
        self.assertEqual(r["decision"],"HOLD_CARD_TITLE_NOT_STRUCTURALLY_BOUND")
    def test_ambiguous_two_titles_holds(self):
        self.assertEqual(audit_card_identity(card().replace("</h3>","</h3><h4>其他活動</h4>"),detail(),URL)["decision"],"HOLD_CARD_TITLE_NOT_STRUCTURALLY_BOUND")
    def test_mismatch_holds(self):
        self.assertEqual(audit_card_identity(card(),detail("其他不同的活動標題"),URL)["decision"],"HOLD_H1_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_duplicate_h1_holds(self):
        self.assertEqual(audit_card_identity(card(),detail()+f"<h1>{TITLE}</h1>",URL)["decision"],"HOLD_H1_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_duplicate_card_holds(self):
        self.assertEqual(audit_card_identity(card()+card(),detail(),URL)["decision"],"HOLD_CARD_MISSING_OR_DUPLICATED")
    def test_missing_card_holds(self):
        self.assertEqual(audit_card_identity("<p>empty</p>",detail(),URL)["decision"],"HOLD_CARD_MISSING_OR_DUPLICATED")
    def test_foreign_route_holds(self):
        self.assertEqual(audit_card_identity(card(),detail(),"https://evil.example/exhibition/abc")["decision"],"HOLD_UNSAFE_OR_NON_DETAIL_ROUTE")
    def test_encoded_slash_holds(self):
        self.assertEqual(audit_card_identity(card(),detail(),"/exhibition/a%2Fb")["decision"],"HOLD_UNSAFE_OR_NON_DETAIL_ROUTE")
    def test_no_ticket_id_or_publication(self):
        r=audit_card_identity(card(),detail(),URL)
        self.assertEqual(r["goldenAccepted"],0)
        self.assertFalse(r["published"])
        self.assertNotIn("ticketEventId",r)
if __name__=="__main__":
    unittest.main()

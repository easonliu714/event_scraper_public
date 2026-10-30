#!/usr/bin/env python3
"""Two observed Huashan 2026-10-31 official links: same venue/date, distinct event."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bo_huashan_distinct_edges import audit_distinct_edges as audit

U1="/exhibition/%E6%9C%97%E8%AE%80%E6%B2%99%E9%BE%8D-%E9%80%99%E6%A8%A3%E5%95%8A%EF%BC%81%E9%82%A3%E4%BA%9B%E7%86%9F%E6%82%89%E5%8F%88%E9%99%8C%E7%94%9F%E7%9A%84%E6%97%A5%E5%B8%B8"
U2="/exhibition/%E6%9C%97%E8%AE%80%E6%B2%99%E9%BE%8D-%E5%8F%B0%E7%81%A3%E6%BB%8B%E5%91%B3"
T1="2026華文朗讀節〖朗讀沙龍〗這樣啊！那些熟悉又陌生的日常"
T2="2026華文朗讀節〖朗讀沙龍〗台灣滋味"
DATE="2026.10.31 - 2026.10.31"
VENUE="中3A館 2樓拱廳"
def card(url,title,date=DATE,venue=VENUE):
    return f'<a href="{url}"><time>{date}</time><h3>{title}</h3><span>{venue}</span></a>'
def page(title): return f"<main><h1>{title}</h1></main>"
def fixture():
    return card(U1,T1)+card(U2,T2),{U1:page(T1),U2:page(T2)},[U1,U2]
class Cases(unittest.TestCase):
    def test_two_same_date_venue_not_collapsed(self):
        r=audit(*fixture())
        self.assertEqual(r["decision"],"REVIEW_DISTINCT_SOURCE_ROUTE_H1_NO_SESSION_OR_TICKET_ID")
        self.assertTrue(r["sharedDateVenue"])
        self.assertEqual(r["distinctDetailPaths"],2)
        self.assertEqual(r["distinctDetailH1"],2)
        self.assertEqual(r["acceptedFields"],0)
    def test_crossed_detail_h1_holds(self):
        html,details,urls=fixture()
        details[U1]=page(T2)
        self.assertTrue(audit(html,details,urls)["decision"].startswith("HOLD_PREDECESSOR"))
    def test_same_h1_on_two_routes_holds(self):
        html,details,urls=fixture()
        html=card(U1,T1)+card(U2,T1);details[U2]=page(T1)
        self.assertEqual(audit(html,details,urls)["decision"],"HOLD_DIFFERENT_ROUTE_SAME_H1")
    def test_duplicate_route_holds(self):
        html,details,urls=fixture()
        self.assertEqual(audit(html,details,[U1,U1])["decision"],"HOLD_UNSAFE_OR_COLLAPSED_SOURCE_ROUTES")
    def test_missing_detail_holds(self):
        html,details,urls=fixture()
        details.pop(U2)
        self.assertEqual(audit(html,details,urls)["decision"],"HOLD_EXACT_TWO_SOURCE_EDGES_REQUIRED")
    def test_extra_card_same_route_holds(self):
        html,details,urls=fixture()
        self.assertTrue(audit(html+card(U1,T1),details,urls)["decision"].startswith("HOLD_PREDECESSOR"))
    def test_unbound_date_holds(self):
        html,details,urls=fixture()
        self.assertEqual(audit(html.replace("<time>"+DATE+"</time>","",1),details,urls)["decision"],"HOLD_CARD_DATE_VENUE_TITLE_UNBOUND")
    def test_cross_origin_route_holds(self):
        html,details,urls=fixture()
        urls[1]="https://evil.example/exhibition/fake"
        self.assertEqual(audit(html,details,urls)["decision"],"HOLD_UNSAFE_OR_COLLAPSED_SOURCE_ROUTES")
    def test_different_venue_still_distinct(self):
        html,details,urls=fixture()
        html=html.replace("<span>"+VENUE+"</span>", "<span>不同場館</span>",1)
        r=audit(html,details,urls)
        self.assertFalse(r["sharedDateVenue"])
        self.assertEqual(r["distinctDetailPaths"],2)
    def test_never_ticket_or_publish(self):
        r=audit(*fixture())
        self.assertIsNone(r["ticketEventId"])
        self.assertFalse(r["published"])
        self.assertEqual(r["goldenAccepted"],0)
if __name__=="__main__": unittest.main()

#!/usr/bin/env python3
"""L9-BP: bounded index-card DOM topology; no inferred activity time."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9bp_huashan_live_card_probe import inspect_index, ROUTE

TITLE="2026華文朗讀節〖朗讀沙龍〗這樣啊！那些熟悉又陌生的日常"
def card(title=TITLE,extra="",route=ROUTE):
    return '<a href="'+route+'"><time>2026.10.31 - 2026.10.31</time><h3>'+title+'</h3><span>中3A館 2樓拱廳</span>'+extra+'</a>'

class Cases(unittest.TestCase):
    def test_one_card_review_not_field(self):
        r=inspect_index(card())
        self.assertEqual(r["decision"],"REVIEW_CARD_LOCAL_TOPOLOGY_NO_FIELD_ACCEPTANCE")
        self.assertEqual(r["acceptedFields"],0)
        self.assertFalse(r["published"])
        self.assertIsNone(r["ticketEventId"])
    def test_duplicate_route_holds(self):
        self.assertEqual(inspect_index(card()+card())["decision"],"HOLD_CARD_MISSING_OR_DUPLICATE")
    def test_missing_card_holds(self):
        self.assertEqual(inspect_index("<main></main>")["decision"],"HOLD_CARD_MISSING_OR_DUPLICATE")
    def test_heading_outside_anchor_holds(self):
        self.assertEqual(inspect_index(card().replace("<h3>"+TITLE+"</h3>","")+"<h3>"+TITLE+"</h3>")["decision"],"HOLD_CARD_HEADING_OUTSIDE_OR_AMBIGUOUS")
    def test_two_headings_holds(self):
        self.assertEqual(inspect_index(card(extra="<h4>其他活動</h4>"))["decision"],"HOLD_CARD_HEADING_OUTSIDE_OR_AMBIGUOUS")
    def test_missing_date_holds(self):
        self.assertEqual(inspect_index(card().replace("2026.10.31","2026.11.01"))["decision"],"HOLD_DATE_OR_VENUE_NOT_CARD_LOCAL")
    def test_missing_venue_holds(self):
        self.assertEqual(inspect_index(card().replace("中3A館 2樓拱廳","未知"))["decision"],"HOLD_DATE_OR_VENUE_NOT_CARD_LOCAL")
    def test_foreign_route_holds(self):
        self.assertEqual(inspect_index(card(),selected_href="https://evil.example/exhibition/fake")["decision"],"HOLD_UNSAFE_SELECTED_ROUTE")
if __name__=="__main__":unittest.main()

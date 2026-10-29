#!/usr/bin/env python3
"""TAINEX official visible list/detail text-backed strict refusal fixtures."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02g_tainex_parity import inspect_pair

URL = "https://www.tainex.com.tw/event/690"
WHEN = "2026-10-29T21:56:10Z"
CARD = {"title":"2026臺灣茶業博覽會","url":URL,
        "period":["2026-11-13","2026-11-16"],"hall":"1館"}
DETAIL = {"title":"2026臺灣茶業博覽會","url":URL,
          "period":["2026-11-13","2026-11-16"],"hall":"1館",
          "venue":"一樓展場 四樓展場",
          "organizer_url":"https://www.chanchao.com.tw/tea/"}
class TainexTests(unittest.TestCase):
    def check(self, card=CARD, detail=DETAIL, decision=None, when=WHEN):
        r=inspect_pair(card,detail,when)
        if decision:
            self.assertEqual(r["decision"],decision)
        self.assertEqual((r["acceptedFields"],r["goldenAccepted"],r["published"]),(0,0,False))
        self.assertFalse(r["eventDateAccepted"])
        self.assertFalse(r["sessionAccepted"])
        self.assertIsNone(r["ticketEventId"])
        self.assertEqual(r["releaseState"],"HARD_HOLD_NO_PUBLICATION")
        return r
    def test_official_same_path_title_period_hall(self):
        r=self.check(decision="REVIEW_EXACT_VENUE_LIST_DETAIL_ROLES_NO_PROMOTION")
        self.assertEqual(r["venueLocalIdReview"],"690")
        self.assertEqual(r["provenance"]["exhibitionPeriod"]["role"],"EXHIBITION_PERIOD_NOT_SESSION_START")
        self.assertEqual(r["provenance"]["organizerLink"]["role"],"ORGANIZER_REFERENCE_NOT_TICKET_ID")
    def test_wrong_detail_id(self):
        self.check(detail={**DETAIL,"url":"https://www.tainex.com.tw/event/691"},
                   decision="HOLD_SOURCE_PATH_IDENTITY")
    def test_other_host(self):
        self.check(detail={**DETAIL,"url":"https://evil.example/event/690"},
                   decision="HOLD_SOURCE_PATH_IDENTITY")
    def test_query_not_identity(self):
        self.check(detail={**DETAIL,"url":URL+"?q=1"},
                   decision="HOLD_SOURCE_PATH_IDENTITY")
    def test_title_mismatch(self):
        self.check(detail={**DETAIL,"title":"2026臺灣國際咖啡展"},
                   decision="HOLD_EXACT_TITLE_PARITY")
    def test_date_mismatch(self):
        self.check(detail={**DETAIL,"period":["2026-11-13","2026-11-17"]},
                   decision="HOLD_EXHIBITION_PERIOD_PARITY")
    def test_reversed_dates(self):
        self.check(detail={**DETAIL,"period":["2026-11-17","2026-11-13"]},
                   decision="HOLD_EXHIBITION_PERIOD_PARITY")
    def test_invalid_date(self):
        self.check(detail={**DETAIL,"period":["2026-11-33","2026-11-16"]},
                   decision="HOLD_EXHIBITION_PERIOD_PARITY")
    def test_hall_mismatch(self):
        self.check(detail={**DETAIL,"hall":"2館"},decision="HOLD_HALL_IDENTITY")
    def test_unrecognized_hall(self):
        self.check(detail={**DETAIL,"hall":"3館"},decision="HOLD_HALL_IDENTITY")
    def test_unlabeled_venue(self):
        self.check(detail={**DETAIL,"venue":"台北市"},decision="HOLD_VENUE_ROLE")
    def test_external_organizer_not_ticket_id(self):
        self.check(detail={**DETAIL,"organizer_url":"javascript:alert(1)"},
                   decision="HOLD_EXTERNAL_ORGANIZER_LINK")
    def test_invalid_observation(self):
        self.check(when="tomorrow",decision="HOLD_INPUT")
    def test_unknown_extra_key(self):
        self.check(card={**CARD,"price":"100"},decision="HOLD_INPUT")
if __name__=="__main__":
    unittest.main()

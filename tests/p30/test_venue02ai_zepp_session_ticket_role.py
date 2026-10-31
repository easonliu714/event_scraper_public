#!/usr/bin/env python3
"""P30-VENUE-02AI source-observed Zepp list/detail with two session roles."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02ai_zepp_session_ticket_role import inspect, detail_rid, ticket_shape

DETAIL = "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=163025"
TICKET = "https://ticketplus.com.tw/activity/a3cb941035a5a7e6898f4000f76bd25c"
def sample():
    return (
        dict(index_url="https://www.zepp.co.jp/hall/newtaipei/schedule/",
             detail_url=DETAIL, title="2026 GMMTV FANDAY 39 in TAIPEI",
             day="2026-10-31", start_time="13:00", observed_at="2026-10-31"),
        dict(url=DETAIL, title="2026 GMMTV FANDAY 39 in TAIPEI",
             day="2026-10-31", header_start="13:00",
             sessions=[dict(time="13:00", label="13:00場次", performer="AlmondProgress"),
                       dict(time="19:30", label="19:30場次", performer="SkyNani")],
             venue="Zepp New Taipei", ticket_url=TICKET,
             ticket_title_verified=False, body_ticket_url_status="網頁建置中"))
class Cases(unittest.TestCase):
    def test_official_rid_and_ticket_link_shape(self):
        self.assertEqual(detail_rid(DETAIL), "163025")
        self.assertTrue(ticket_shape(TICKET))
    def test_source_same_rid_two_sessions_not_formal(self):
        a, b = sample()
        x = inspect(a, b)
        self.assertEqual(x["decision"], "HOLD_TWO_SESSIONS_TICKET_DETAIL_AND_BODY_STATUS_UNVERIFIED")
        self.assertTrue(x["sameRidTitleMatch"])
        self.assertEqual(x["explicitSessionCount"], 2)
        self.assertEqual(len(x["candidateProvenance"]), 6)
        self.assertEqual(x["acceptedFields"], 0)
    def test_other_rid_refused(self):
        a, b = sample()
        b["url"] = DETAIL.replace("163025", "163026")
        self.assertEqual(inspect(a, b)["decision"], "HOLD_LIST_DETAIL_IDENTITY")
    def test_heading_mismatch_refused(self):
        a, b = sample()
        b["title"] = "OTHER SHOW"
        self.assertEqual(inspect(a, b)["decision"], "HOLD_LIST_DETAIL_IDENTITY")
    def test_date_role_mismatch_refused(self):
        a, b = sample()
        b["day"] = "2026-11-01"
        self.assertEqual(inspect(a, b)["decision"], "HOLD_INDEX_DETAIL_DATE_OR_START")
    def test_second_session_cannot_be_dropped(self):
        a, b = sample()
        b["sessions"] = b["sessions"][:1]
        self.assertEqual(inspect(a, b)["decision"], "HOLD_NOT_EXACT_TWO_EXPLICIT_SESSIONS")
    def test_duplicate_session_refused(self):
        a, b = sample()
        b["sessions"][1]["time"] = "13:00"
        b["sessions"][1]["label"] = "13:00場次"
        self.assertEqual(inspect(a, b)["decision"], "HOLD_DUPLICATE_OR_INDEX_SESSION_MISMATCH")
    def test_non_source_session_label_refused(self):
        a, b = sample()
        b["sessions"][1]["label"] = "售票時間"
        self.assertEqual(inspect(a, b)["decision"], "HOLD_SESSION_LABEL_OR_TIME")
    def test_unsafe_ticket_url_refused(self):
        a, b = sample()
        b["ticket_url"] = TICKET.replace("https:", "http:")
        self.assertEqual(inspect(a, b)["decision"], "HOLD_TICKET_URL_NOT_ALLOWLISTED")
    def test_ticket_title_claim_refused(self):
        a, b = sample()
        b["ticket_title_verified"] = True
        self.assertEqual(inspect(a, b)["decision"], "HOLD_TICKET_EVENT_IDENTITY_UNPROVEN")
    def test_unverified_body_status_refused(self):
        a, b = sample()
        b["body_ticket_url_status"] = "購票網址｜已驗證"
        self.assertEqual(inspect(a, b)["decision"], "HOLD_TICKET_BODY_STATUS_NOT_VERIFIED")
    def test_never_publish(self):
        a, b = sample()
        x = inspect(a, b)
        self.assertIsNone(x["ticketEventId"])
        self.assertFalse(x["ticketIdentityVerified"])
        self.assertEqual(x["goldenAccepted"], 0)
        self.assertFalse(x["published"])
        self.assertEqual(x["releaseState"], "HARD_HOLD_NO_PUBLICATION")
if __name__ == "__main__":
    unittest.main()

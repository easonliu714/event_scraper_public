#!/usr/bin/env python3
"""P30-VENUE-02L identity and multi-event monthly bulletin refusal regressions."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02l_ntpc_artcenter import inspect, sid_of, DETAIL, TITLE

L = f'<a href="{DETAIL}">{TITLE}</a>'
D = f'<h3>{TITLE}</h3><p>演出時間：11/01 14:30</p><p>票券資訊：年代售票</p>'

class Cases(unittest.TestCase):
    def check(self, listing, detail, decision):
        x = inspect(listing, detail, "2026-10-30T02:55:00Z")
        self.assertEqual(x["decision"], decision)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
        self.assertIsNone(x["ticketEventId"])
        self.assertEqual(x["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        return x
    def test_same_sid_bulletin_review_not_event(self):
        x = self.check(L, D, "REVIEW_SAME_SID_MONTHLY_ANNOUNCEMENT_NO_FIELDS")
        self.assertEqual(x["roleProvenance"]["SESSION"]["decision"], "HOLD_NO_INDIVIDUAL_SESSION_IDENTITY")
    def test_same_title_distinct_sid_not_collapsed(self):
        self.check(L.replace("0Q152372523738311866", "0Q152378107064377580"), D, "HOLD_LIST_SID_TITLE_NOT_UNIQUE")
    def test_duplicate_link_rejected(self):
        self.check(L + L, D, "HOLD_LIST_SID_TITLE_NOT_UNIQUE")
    def test_title_mismatch_rejected(self):
        self.check(L.replace(TITLE, "另一個節目"), D, "HOLD_LIST_SID_TITLE_NOT_UNIQUE")
    def test_missing_detail_heading(self):
        self.check(L, D.replace("<h3>", "<p>").replace("</h3>", "</p>"), "HOLD_DETAIL_HEADING_NOT_UNIQUE")
    def test_duplicate_detail_heading(self):
        self.check(L, D + f"<h3>{TITLE}</h3>", "HOLD_DETAIL_HEADING_NOT_UNIQUE")
    def test_ticket_name_not_event_id(self):
        x = self.check(L, D + '<a href="https://www.opentix.life/">OPENTIX</a>', "REVIEW_SAME_SID_MONTHLY_ANNOUNCEMENT_NO_FIELDS")
        self.assertIsNone(x["ticketEventId"])
    def test_announcement_date_not_session(self):
        x = self.check(L, D + "<time>2026-10-28</time>", "REVIEW_SAME_SID_MONTHLY_ANNOUNCEMENT_NO_FIELDS")
        self.assertEqual(x["acceptedFields"], 0)
    def test_untrusted_sid_url_rejected(self):
        self.assertIsNone(sid_of("https://www.culture.ntpc.gov.tw.evil.test/artcenter_chi/xmdoc/cont?sid=0Q152372523738311866"))
    def test_wrong_source_path_rejected(self):
        self.assertIsNone(sid_of("https://www.culture.ntpc.gov.tw/artcenter_chi/sitesearch?sid=0Q152372523738311866"))

if __name__ == "__main__":
    unittest.main()

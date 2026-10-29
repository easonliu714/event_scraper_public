#!/usr/bin/env python3
"""Public-text role boundaries from a source-observed detail; synthetic tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9ar_famiticket_role_text import inspect_public_text

URL = "https://www.famiticket.com.tw/Home/Activity/Info/RQA3AHUAbwBwAEgANwBzAFIAQQA1AGEAbABEADgAcABqAGMAbwBaAC8ARgBGAEcAVwBWAEUAdQBXAFEAeQBUAFcAcgAyADUARgBFADUAbgBWADQAdwA9AA2"
TITLE = "CC同人創作展"
LINES = ["活動探索", "#### CC同人創作展", "《活動資訊》", TITLE,
         "2026.11.21-22", "活動時間│10:30-16:00",
         "活動地點│松山文創園區 五號倉庫", "活動票價│",
         "單日票200元", "雙日票350元", "活動內容│同人誌展售會",
         "《活動介紹》", "售票服務", "個人因素退票酌收10%手續費，需於2026年11月20日前辦理"]

class RoleTests(unittest.TestCase):
    def check(self, lines=LINES, decision=None, url=URL, title=TITLE):
        r = inspect_public_text(lines, url, title)
        if decision:
            self.assertEqual(r["decision"], decision)
        self.assertEqual((r["acceptedFields"], r["goldenAccepted"], r["published"]), (0, 0, False))
        self.assertEqual(r["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        self.assertEqual(r["liveHttpGetThisRun"], 0)
        return r
    def test_official_text_role_split(self):
        r = self.check(decision="REVIEW_DISTINCT_EVENT_AND_TICKET_ROLES_NO_ACCEPTANCE")
        self.assertEqual(r["ticketVariantCount"], 2)
        self.assertTrue(r["refundCutoffOutsideEventBlock"])
        self.assertEqual(r["hoursRole"], "REVIEW_EVENT_HOURS_NOT_SESSION_START")
    def test_refund_cutoff_not_event_date(self):
        x = LINES.copy(); x[4] = "2026年11月20日"
        self.check(x, "HOLD_UNLABELED_OR_AMBIGUOUS_EVENT_DATE")
    def test_wrong_title(self):
        self.check(LINES, "HOLD_TITLE_IDENTITY", title="其他活動")
    def test_duplicate_section(self):
        self.check(LINES + ["《活動資訊》"], "HOLD_ACTIVITY_SECTION_NOT_UNIQUE")
    def test_no_section_end(self):
        self.check(LINES[:11], "HOLD_SECTION_BOUNDARY")
    def test_duplicate_hours(self):
        x = LINES.copy(); x.insert(6, x[5])
        self.check(x, "HOLD_EVENT_HOURS_ROLE")
    def test_duplicate_price_label(self):
        x = LINES.copy(); x.insert(8, "活動票價│")
        self.check(x, "HOLD_TICKET_PRICE_LABEL")
    def test_duplicate_ticket_variant(self):
        x = LINES.copy(); x.insert(10, "單日票200元")
        self.check(x, "HOLD_TICKET_VARIANTS")
    def test_ambiguous_ticket_variant(self):
        x = LINES.copy(); x[9] = "免費入場/雙日票350元"
        self.check(x, "HOLD_AMBIGUOUS_TICKET_VARIANT")
    def test_invalid_date(self):
        x = LINES.copy(); x[4] = "2026.11.32-33"
        self.check(x, "HOLD_INVALID_EVENT_DATE")
    def test_reverse_date(self):
        x = LINES.copy(); x[4] = "2026.11.22-21"
        self.check(x, "HOLD_REVERSED_EVENT_DATE")
    def test_external_url(self):
        self.check(LINES, "HOLD_INPUT", url="https://evil.example/Home/Activity/Info/123")
    def test_too_many_lines(self):
        self.check(["x"] * 241, "HOLD_INPUT")
    def test_unlabeled_hours(self):
        x = LINES.copy(); x[5] = "10:30-16:00"
        self.check(x, "HOLD_EVENT_HOURS_ROLE")

if __name__ == "__main__":
    unittest.main()

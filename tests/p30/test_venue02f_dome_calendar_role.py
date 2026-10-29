#!/usr/bin/env python3
"""Official October 2026 calendar semantics represented as minimal text fixtures."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02f_dome_calendar_role import inspect_calendar_cell, CALENDAR

class DomeCalendarTests(unittest.TestCase):
    def check(self, day, entries, decision, url=CALENDAR):
        r = inspect_calendar_cell(day, entries, url)
        self.assertEqual(r["decision"], decision)
        self.assertEqual((r["acceptedFields"], r["goldenAccepted"], r["published"]), (0, 0, False))
        self.assertFalse(r["eventDateAccepted"])
        self.assertFalse(r["officialDetailVerified"])
        self.assertIsNone(r["ticketEventId"])
        self.assertEqual(r["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        return r
    def test_oct29_occupancy(self):
        r=self.check("2026-10-29", ["場館已安排使用", "場館已承租"],
                     "REVIEW_OCCUPANCY_ONLY_NOT_PUBLIC_EVENT")
        self.assertEqual(r["calendarRole"], "VENUE_OCCUPANCY_ONLY")
    def test_oct30_occupancy(self):
        self.check("2026-10-30", ["場館已安排使用", "場館已承租"],
                   "REVIEW_OCCUPANCY_ONLY_NOT_PUBLIC_EVENT")
    def test_oct31_two_names_in_one_cell(self):
        r=self.check("2026-10-31", ["演唱會",
          "《流光穿梭✦十年傳說》 GCS 2026 夏季總決賽、傳說十週年演唱會"],
          "HOLD_POSSIBLE_MULTIPLE_EVENTS_ONE_CELL")
        self.assertEqual(r["identity"], "UNKNOWN_MULTI_EVENT")
    def test_named_concert_no_detail(self):
        self.check("2026-10-09", ["演唱會", "BIGBANG 2026-2027 WORLD TOUR"],
                   "REVIEW_NAMED_PUBLIC_EVENT_DETAIL_NOT_VERIFIED")
    def test_named_baseball_no_detail(self):
        self.check("2026-10-17", ["球賽", "台灣大賽"],
                   "REVIEW_NAMED_PUBLIC_EVENT_DETAIL_NOT_VERIFIED")
    def test_calendar_day_not_show_start(self):
        r=self.check("2026-10-20", ["球賽", "台灣大賽"],
                     "REVIEW_NAMED_PUBLIC_EVENT_DETAIL_NOT_VERIFIED")
        self.assertFalse(r["eventDateAccepted"])
    def test_occupancy_mixed_with_concert(self):
        self.check("2026-10-29", ["場館已承租", "演唱會"],
                   "HOLD_MIXED_OCCUPANCY_AND_EVENT")
    def test_generic_no_name(self):
        self.check("2026-10-29", ["演唱會", "演唱會"],
                   "HOLD_UNIDENTIFIABLE_PUBLIC_TITLE")
    def test_unrecognized_category(self):
        self.check("2026-10-29", ["場館", "不明活動"],
                   "HOLD_UNKNOWN_CALENDAR_CARD_ROLE")
    def test_no_category(self):
        self.check("2026-10-29", ["某活動"], "HOLD_UNKNOWN_CALENDAR_CARD_ROLE")
    def test_external_origin(self):
        self.check("2026-10-29", ["球賽", "台灣大賽"], "HOLD_INPUT",
                   url="https://evil.example/Web/dome/")
    def test_invalid_date(self):
        self.check("2026-10-32", ["球賽", "台灣大賽"], "HOLD_INVALID_CALENDAR_DAY")
    def test_oversized(self):
        self.check("2026-10-29", ["球賽", "x"*500], "HOLD_INPUT")
    def test_blank_title(self):
        self.check("2026-10-29", ["球賽", ""], "HOLD_INPUT")
    def test_duplicate_category(self):
        self.check("2026-10-29", ["球賽", "球賽", "台灣大賽"],
                   "HOLD_UNKNOWN_CALENDAR_CARD_ROLE")

if __name__ == "__main__":
    unittest.main()

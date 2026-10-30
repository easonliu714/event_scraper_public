#!/usr/bin/env python3
"""Offline exact all-showing parity and fail-closed Fuzhong15 regressions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02x_fuzhong15_allshow import inspect_all_showings as inspect
from test_venue02w_fuzhong15_multishow import idx,R,S,TITLE,URL
from test_venue02v_fuzhong15_row_parity import detail
INDEX=idx([R,S])
BOTH="2026/10/14 18:40 2026/10/15 20:00"
class Cases(unittest.TestCase):
    def test_all_exact_review_only(self):
        x=inspect(INDEX,detail(BOTH))
        self.assertEqual(x["decision"],"REVIEW_ALL_SHOWINGS_EXACT_PARITY_NO_SESSION_ID")
        self.assertEqual((x["matchedShowingCount"],x["missingShowingCount"],x["extraDetailDateCount"]),(2,0,0))
        self.assertIsNone(x["venueScreeningId"])
    def test_missing_second_detail(self):
        x=inspect(INDEX,detail("2026/10/14 18:40"))
        self.assertEqual(x["decision"],"HOLD_INCOMPLETE_ALL_SHOWING_PARITY")
        self.assertEqual(x["missingShowingCount"],1)
    def test_extra_detail(self):
        x=inspect(INDEX,detail(BOTH+" 2026/10/16 18:40"))
        self.assertEqual(x["decision"],"HOLD_INCOMPLETE_ALL_SHOWING_PARITY")
        self.assertEqual(x["extraDetailDateCount"],1)
    def test_duplicate_detail(self):
        x=inspect(INDEX,detail(BOTH+" 2026/10/15 20:00"))
        self.assertEqual(x["decision"],"HOLD_DUPLICATE_INDEX_OR_DETAIL_DATETIME")
    def test_duplicate_index(self):
        self.assertEqual(inspect(idx([R,R,S]),detail(BOTH))["decision"],"HOLD_DUPLICATE_SHOWING_OR_FILM_TITLE")
    def test_title_conflict(self):
        bad=("10/15(四)","20:00","另一部片",URL)
        self.assertEqual(inspect(idx([R,bad]),detail(BOTH))["decision"],"HOLD_DUPLICATE_SHOWING_OR_FILM_TITLE")
    def test_single_showing_not_multishow(self):
        self.assertEqual(inspect(idx([R]),detail("2026/10/14 18:40"))["decision"],"HOLD_NO_MULTISHOWING_GROUP")
    def test_title_mismatch(self):
        self.assertEqual(inspect(INDEX,detail(BOTH,title="別的片名"))["decision"],"HOLD_DETAIL_TITLE_LABEL_OR_CAP")
    def test_duplicate_label(self):
        self.assertEqual(inspect(INDEX,detail(BOTH)+"<p>放映日期：</p>")["decision"],"HOLD_DETAIL_TITLE_LABEL_OR_CAP")
    def test_invalid_calendar_date(self):
        bad=("10/32(五)","20:00",TITLE,URL)
        self.assertEqual(inspect(idx([R,bad]),detail(BOTH))["decision"],"HOLD_INVALID_INDEX_CALENDAR_DATE")
    def test_no_index_year(self):
        self.assertEqual(inspect(INDEX.replace("2026年10月放映場次表","放映場次表"),detail(BOTH))["decision"],"HOLD_INDEX_YEAR_MONTH_AMBIGUOUS")
    def test_unrelated_film_not_same_session(self):
        other=("10/16(五)","20:00","其他電影","/xcmovie/cont?sid=0Q231405699420480959&xsmsid=0M361641875264878260")
        x=inspect(idx([R,S,other]),detail(BOTH))
        self.assertEqual(x["matchedShowingCount"],2)
        self.assertEqual(x["decision"],"REVIEW_ALL_SHOWINGS_EXACT_PARITY_NO_SESSION_ID")
    def test_zero_ticket_fields(self):
        x=inspect(INDEX,detail(BOTH))
        self.assertEqual(x["acceptedFields"],0)
        self.assertIsNone(x["ticketEventId"])
if __name__=="__main__":
    unittest.main()

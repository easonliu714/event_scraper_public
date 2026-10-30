#!/usr/bin/env python3
"""Fuzhong15 duplicate showing and multi-date identity refusal tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02w_fuzhong15_multishow import showing_groups,inspect_multishow
from test_venue02v_fuzhong15_row_parity import URL,TITLE,detail
def idx(rows):
    start="<h2>2026年10月放映場次表</h2><table>"
    for d,t,title,url in rows:
        start+=f'<tr><td>{d}</td><td>{t}</td><td><a href="{url}">{title}</a> 售</td><td>124 min</td><td>輔12級</td></tr>'
    return start+"</table>"
R=("10/14(三)","18:40",TITLE,URL)
S=("10/15(四)","20:00",TITLE,URL)
class Cases(unittest.TestCase):
    def test_one_showing(self):
        r,s,e=showing_groups(idx([R]))
        self.assertIsNone(e)
        self.assertEqual(r["distinctShowingCount"],1)
    def test_two_distinct_showings(self):
        r,s,e=showing_groups(idx([R,S]))
        self.assertIsNone(e)
        self.assertEqual((r["sameFilmRowCount"],r["distinctShowingCount"]),(2,2))
    def test_duplicate_showing(self):
        r,s,e=showing_groups(idx([R,R]))
        self.assertEqual(e,"HOLD_DUPLICATE_SHOWING_OR_FILM_TITLE")
        self.assertEqual(r["duplicateShowingCount"],1)
    def test_title_conflict(self):
        r,s,e=showing_groups(idx([R,("10/15(四)","20:00","另一部片",URL)]))
        self.assertEqual(e,"HOLD_DUPLICATE_SHOWING_OR_FILM_TITLE")
    def test_no_year(self):
        r,s,e=showing_groups(idx([R]).replace("2026年10月放映場次表","場次表"))
        self.assertEqual(e,"HOLD_INDEX_YEAR_MONTH_AMBIGUOUS")
    def test_no_row(self):
        r,s,e=showing_groups(idx([]))
        self.assertEqual(e,"HOLD_NO_ELIGIBLE_SCREENING_ROW")
    def test_mismatch_detail(self):
        self.assertEqual(inspect_multishow(idx([R]),detail("2026/10/14 19:40"))["decision"],"HOLD_DETAIL_ROW_PARITY")
    def test_one_review(self):
        x=inspect_multishow(idx([R]),detail("2026/10/14 18:40"))
        self.assertEqual(x["decision"],"REVIEW_ONE_SHOWING_NO_TICKET_ID")
        self.assertIsNone(x["venueScreeningId"])
    def test_multi_review(self):
        x=inspect_multishow(idx([R,S]),detail("2026/10/14 18:40 2026/10/15 20:00"))
        self.assertEqual(x["decision"],"REVIEW_MULTISHOWING_FILM_NOT_UNIQUE_SESSION")
        self.assertEqual(x["acceptedFields"],0)
    def test_multi_missing_second_detail(self):
        x=inspect_multishow(idx([R,S]),detail("2026/10/14 18:40"))
        self.assertEqual(x["acceptedFields"],0)
    def test_duplicate_not_review(self):
        self.assertEqual(inspect_multishow(idx([R,R]),detail())["decision"],"HOLD_DUPLICATE_SHOWING_OR_FILM_TITLE")
    def test_ticket_identity_never_inferred(self):
        self.assertIsNone(inspect_multishow(idx([R]),detail("2026/10/14 18:40"))["ticketEventId"])
if __name__=="__main__":
    unittest.main()

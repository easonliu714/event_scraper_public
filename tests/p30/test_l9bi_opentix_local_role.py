#!/usr/bin/env python3
"""Fail-closed OPENTIX section ownership regression, no network."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bi_opentix_local_role import section_roles
T = "官方節目名稱"
def html(extra="", h1=T, section=True):
    return "<h1>"+h1+"</h1>"+("<h2>購票資訊</h2>" if section else "")+extra
class Cases(unittest.TestCase):
    def test_unique_session_role_review(self):
        x=section_roles(html("<p>選擇場次</p>"),T)
        self.assertEqual(x["decision"],"REVIEW_LOCAL_SESSION_LABEL_NO_VALUE")
        self.assertEqual(x["acceptedFields"],0)
    def test_refund_not_session(self):
        self.assertEqual(section_roles(html("<p>退票期限</p>"),T)["decision"],"HOLD_NO_SOURCE_LOCAL_SESSION_ROLE")
    def test_sale_not_session(self):
        self.assertEqual(section_roles(html("<p>開賣時間</p>"),T)["localSessionLabelCount"],0)
    def test_venue_not_session(self):
        self.assertEqual(section_roles(html("<p>選擇場館</p>"),T)["localSessionLabelCount"],0)
    def test_role_counts(self):
        x=section_roles(html("<p>選擇場館</p><p>選擇場次</p><p>退票期限：</p>"),T)
        self.assertEqual((x["localVenueLabelCount"],x["localSessionLabelCount"],x["localRefundLabelCount"]),(1,1,1))
    def test_duplicate_session(self):
        self.assertEqual(section_roles(html("<p>選擇場次</p><p>選擇場次</p>"),T)["decision"],"HOLD_DUPLICATE_ROLE_LABELS")
    def test_duplicate_venue(self):
        self.assertEqual(section_roles(html("<p>選擇場館</p><p>選擇場館</p><p>選擇場次</p>"),T)["decision"],"HOLD_DUPLICATE_ROLE_LABELS")
    def test_duplicate_title(self):
        self.assertEqual(section_roles(html("<h1>"+T+"</h1><p>選擇場次</p>"),T)["decision"],"HOLD_TITLE_OR_SECTION_IDENTITY")
    def test_mismatch(self):
        self.assertEqual(section_roles(html("<p>選擇場次</p>",h1="不同節目"),T)["decision"],"HOLD_TITLE_OR_SECTION_IDENTITY")
    def test_no_section(self):
        self.assertEqual(section_roles(html("<p>選擇場次</p>",section=False),T)["decision"],"HOLD_TITLE_OR_SECTION_IDENTITY")
    def test_next_section_not_owned(self):
        self.assertEqual(section_roles(html("<h2>退票政策</h2><p>選擇場次</p>"),T)["localSessionLabelCount"],0)
    def test_long_section_hold(self):
        self.assertEqual(section_roles(html("<p>"+"字"*2500+"</p>"),T)["decision"],"HOLD_SECTION_TEXT_CAP")
    def test_no_value_inference(self):
        x=section_roles(html("<p>選擇場次</p><p>2026/10/31 18:00</p>"),T)
        self.assertIsNone(x["sessionId"])
        self.assertIsNone(x["ticketEventId"])
if __name__=="__main__":
    unittest.main()

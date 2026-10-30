#!/usr/bin/env python3
"""Offline, fail-closed OPENTIX role-to-value adjacency regressions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bj_opentix_value_topology import inspect_value_topology as inspect
T = "官方節目名稱"
def html(extra, title=T):
    return "<h1>"+title+"</h1><h2>購票資訊</h2>"+extra
class Cases(unittest.TestCase):
    def test_adjacent_datetime_review_only(self):
        x = inspect(html("<p>選擇場次</p><p>2026/10/31 18:00</p>"), T)
        self.assertEqual(x["decision"], "REVIEW_ADJACENT_DATETIME_NO_TZ_NO_SESSION_ID")
        self.assertEqual(x["adjacentValueCandidateCount"], 1)
        self.assertIsNone(x["sessionDateTime"])
    def test_no_adjacent(self):
        self.assertEqual(inspect(html("<p>選擇場次</p>"),T)["decision"],"HOLD_JS_OR_UNBOUND_SESSION_VALUE")
    def test_select_control(self):
        x=inspect(html("<p>選擇場次</p><select><option>18:00</option></select>"),T)
        self.assertEqual(x["decision"],"HOLD_INTERACTIVE_OR_JS_ONLY_VALUE")
    def test_button_control(self):
        self.assertEqual(inspect(html("<p>選擇場次</p><button>選擇</button>"),T)["decision"],"HOLD_INTERACTIVE_OR_JS_ONLY_VALUE")
    def test_sale_not_showtime(self):
        self.assertEqual(inspect(html("<p>選擇場次</p><p>開賣時間 2026/10/31 18:00</p>"),T)["decision"],"HOLD_MIXED_ROLE_OR_VALUE_CAP")
    def test_refund_not_showtime(self):
        self.assertEqual(inspect(html("<p>選擇場次</p><p>退票期限 2026/10/31 18:00</p>"),T)["decision"],"HOLD_MIXED_ROLE_OR_VALUE_CAP")
    def test_two_dates_ambiguous(self):
        self.assertEqual(inspect(html("<p>選擇場次</p><p>2026/10/31 18:00 2026/11/01 19:00</p>"),T)["decision"],"HOLD_ZERO_MULTI_OR_NONLOCAL_VALUE")
    def test_bad_calendar(self):
        self.assertEqual(inspect(html("<p>選擇場次</p><p>2026/02/31 18:00</p>"),T)["decision"],"HOLD_INVALID_CALENDAR_DATETIME")
    def test_unstructured_text(self):
        self.assertEqual(inspect(html("<p>選擇場次</p>2026/10/31 18:00"),T)["decision"],"HOLD_UNSTRUCTURED_ADJACENCY")
    def test_label_container_mixed(self):
        self.assertEqual(inspect(html("<p>選擇場次 <b>立即購票</b></p><p>2026/10/31 18:00</p>"),T)["decision"],"HOLD_LABEL_CONTAINER_MIXED")
    def test_other_section_not_owned(self):
        self.assertEqual(inspect(html("<p>選擇場次</p><h2>退票資訊</h2><p>2026/10/31 18:00</p>"),T)["decision"],"HOLD_JS_OR_UNBOUND_SESSION_VALUE")
    def test_title_mismatch(self):
        self.assertEqual(inspect(html("<p>選擇場次</p>",title="其他活動"),T)["decision"],"HOLD_TITLE_OR_SECTION_IDENTITY")
    def test_duplicate_label(self):
        self.assertEqual(inspect(html("<p>選擇場次</p><p>選擇場次</p>"),T)["decision"],"HOLD_DUPLICATE_ROLE_LABELS")
    def test_no_ticket_identity_or_fields(self):
        x=inspect(html("<p>選擇場次</p><p>2026/10/31 18:00</p>"),T)
        self.assertIsNone(x["ticketEventId"])
        self.assertIsNone(x["sessionId"])
        self.assertEqual(x["acceptedFields"],0)
if __name__ == "__main__":
    unittest.main()

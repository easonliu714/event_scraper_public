#!/usr/bin/env python3
"""P30-L9-AY strict table-row provenance and refund/date negative cases."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9ay_era_row_role import review
from p30_l9av_era_source_role import TITLE

def page(rows, after=""):
    return (f"<h1>{TITLE}</h1><section><div><h4>場次列表</h4></div>"
            f"<div><table>{rows}</table></div><h4>退票方式</h4>{after}</section>")

ROW = "<tr><td>2026/11/01</td><td>19:30</td></tr>"

class Cases(unittest.TestCase):
    def check(self, html, decision):
        x = review(html, "2026-10-30T03:55:00Z")
        self.assertEqual(x["decision"], decision)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
        self.assertIsNone(x["ticketEventId"])
        self.assertEqual(x["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        return x

    def test_unique_table_date_review_only(self):
        x = self.check(page(ROW), "REVIEW_ONE_SESSION_TABLE_ROW_DATE_HINTS_NO_FIELDS")
        self.assertEqual((x["tableCount"], x["rowsWithDateHint"]), (1, 1))
    def test_refund_after_heading_not_promoted(self):
        self.check(page(ROW, "<p>退票日期 2026/10/22</p>"), "REVIEW_ONE_SESSION_TABLE_ROW_DATE_HINTS_NO_FIELDS")
    def test_refund_in_row_refused(self):
        self.check(page("<tr><td>退票 2026/11/01</td></tr>"), "HOLD_REFUND_OR_OVERSIZE_ROW")
    def test_two_dates_same_row_refused(self):
        self.check(page("<tr><td>2026/11/01 至 2026/11/02</td></tr>"), "HOLD_MULTIPLE_DATES_PER_ROW")
    def test_no_date_refused(self):
        self.check(page("<tr><td>尚未公布</td></tr>"), "HOLD_NO_ROW_LOCAL_DATE_HINT")
    def test_no_rows_refused(self):
        self.check(page(""), "HOLD_TABLE_ROW_BOUND")
    def test_two_tables_refused(self):
        self.check(page(ROW).replace("</table>", "</table><table>" + ROW + "</table>"),
                   "HOLD_SESSION_TABLE_NOT_UNIQUE")
    def test_duplicate_heading_refused(self):
        self.check(page(ROW) + "<h4>場次列表</h4>", "HOLD_SESSION_HEADING_NOT_UNIQUE")
    def test_wrong_title_refused(self):
        self.check(page(ROW).replace(TITLE, "不同活動"), "HOLD_DETAIL_H1_NOT_UNIQUE")
    def test_oversized_row_refused(self):
        self.check(page("<tr><td>" + "X" * 501 + "</td></tr>"), "HOLD_REFUND_OR_OVERSIZE_ROW")
    def test_unrelated_global_table_refused(self):
        self.check(f"<h1>{TITLE}</h1><h4>場次列表</h4><h4>退票方式</h4><table>{ROW}</table>",
                   "HOLD_SESSION_TABLE_NOT_UNIQUE")

if __name__ == "__main__":
    unittest.main()

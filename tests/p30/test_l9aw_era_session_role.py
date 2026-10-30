#!/usr/bin/env python3
"""P30-L9-AW section-local fail-closed negative regressions."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9aw_era_session_role import inspect
from p30_l9av_era_source_role import DETAIL, TITLE

H = f'<a href="{DETAIL}">11/01(日) {TITLE}</a>'
D = (f'<h1>{TITLE}</h1><h4>場次列表</h4>'
     '<table><tr><th>日期</th></tr><tr><td>2026/11/01</td></tr></table>'
     '<h4>退票方式</h4><p>退票期限至2026/10/22</p>')

class Cases(unittest.TestCase):
    def check(self, home, detail, decision):
        x = inspect(home, detail, "2026-10-30T01:55:00Z")
        self.assertEqual(x["decision"], decision)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
        self.assertIsNone(x["ticketEventId"])
        self.assertEqual(x["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        return x
    def test_local_review(self):
        x = self.check(H, D, "REVIEW_SESSION_TABLE_REFUND_SEPARATED_NO_FIELD_PROMOTION")
        self.assertEqual(x["sessionDateTokensReview"], 1)
        self.assertEqual(x["refundDateTokensReview"], 1)
        self.assertEqual(x["roleProvenance"]["REFUND"]["decision"], "REFUSE_AS_EVENT_OR_SALE_DATE")
    def test_no_list_identity(self):
        self.check("<p>other</p>", D, "HOLD_PRIOR_EXACT_PRODUCT_IDENTITY")
    def test_no_table(self):
        self.check(H, D.replace("<table>", "<div>").replace("</table>", "</div>"), "HOLD_NO_SESSION_LOCAL_TABLE")
    def test_global_unrelated_date_refused(self):
        self.check(H, D.replace("2026/11/01", "TBA") + "<p>2026/11/01</p>", "HOLD_NO_LOCAL_SESSION_DATE_TOKEN")
    def test_refund_inside_session_table(self):
        self.check(H, D.replace("<td>2026/11/01</td>", "<td>退票 2026/11/01</td>"), "HOLD_SESSION_TABLE_MIXED_REFUND")
    def test_refund_heading_absent(self):
        self.check(H, D.replace("<h4>退票方式</h4>", ""), "HOLD_REFUND_HEADING_NOT_UNIQUE")
    def test_refund_duplicate(self):
        self.check(H, D + "<h4>退票方式</h4>", "HOLD_REFUND_HEADING_NOT_UNIQUE")
    def test_no_refund_local_node(self):
        self.check(H, D.replace("<p>退票期限至2026/10/22</p>", "<div>退票期限至2026/10/22</div>"), "HOLD_NO_LOCAL_REFUND_NODE")
    def test_table_after_other_heading_refused(self):
        self.check(H, D.replace("<h4>場次列表</h4>", "<h4>場次列表</h4><h4>其他</h4>"), "HOLD_NO_SESSION_LOCAL_TABLE")
    def test_session_row_bounds(self):
        self.check(H, D.replace("<tr><td>2026/11/01</td></tr>", "<tr><td>2026/11/01</td></tr>" * 49), "HOLD_SESSION_ROW_BOUNDS")

if __name__ == "__main__":
    unittest.main()

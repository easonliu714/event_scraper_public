#!/usr/bin/env python3
"""L9-AZ exact cell-level source-bound diagnostic and fail-closed negatives."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9az_era_cell_ownership import review
from p30_l9av_era_source_role import TITLE

def page(rows):
    return f"<h1>{TITLE}</h1><section><div><h4>場次列表</h4></div><div><table>{rows}</table></div><h4>退票方式</h4></section>"
class Cases(unittest.TestCase):
    def check(self,html,decision):
        x=review(html,"2026-10-30T04:55:00Z")
        self.assertEqual(x["decision"],decision)
        self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
        self.assertIsNone(x["ticketEventId"])
        return x
    def test_row_date_time_review_only(self):
        x=self.check(page("<tr><td>2026/11/01</td><td>19:30</td></tr>"),"REVIEW_ROW_CELL_TOPOLOGY_NO_ACCEPTED_FIELDS")
        self.assertEqual(x["candidateRowsWithDateAndTime"],1)
    def test_header_labels_not_accepted(self):
        x=self.check(page("<tr><th>演出日期</th><th>演出時間</th></tr><tr><td>2026/11/01</td><td>19:30</td></tr>"),"REVIEW_ROW_CELL_TOPOLOGY_NO_ACCEPTED_FIELDS")
        self.assertEqual((x["headerDateRoleCount"],x["headerTimeRoleCount"]),(1,1))
    def test_one_session_attribute_still_not_accepted(self):
        x=self.check(page('<tr data-session-id="S1"><td>2026/11/01</td><td>19:30</td></tr>'),"REVIEW_ROW_CELL_TOPOLOGY_NO_ACCEPTED_FIELDS")
        self.assertEqual(x["rowSessionAttributeHints"],1)
    def test_two_attributes_refused(self):
        self.check(page('<tr data-session-id="S1"><td data-session-id="S2">2026/11/01</td></tr>'),"HOLD_MULTIPLE_SESSION_ATTRIBUTES")
    def test_refund_in_cell_refused(self):
        self.check(page("<tr><td>退票日期 2026/11/01</td></tr>"),"HOLD_PREDECESSOR_TABLE_IDENTITY")
    def test_multiple_dates_refused(self):
        self.check(page("<tr><td>2026/11/01 2026/11/02</td></tr>"),"HOLD_PREDECESSOR_TABLE_IDENTITY")
    def test_wrong_title_refused(self):
        self.check(page("<tr><td>2026/11/01</td></tr>").replace(TITLE,"wrong"),"HOLD_PREDECESSOR_TABLE_IDENTITY")
    def test_missing_date_refused(self):
        self.check(page("<tr><td>未定</td></tr>"),"HOLD_PREDECESSOR_TABLE_IDENTITY")
    def test_oversized_cell_refused(self):
        self.check(page("<tr><td>"+("x"*501)+" 2026/11/01</td></tr>"),"HOLD_PREDECESSOR_TABLE_IDENTITY")
    def test_two_tables_refused(self):
        self.check(page("<tr><td>2026/11/01</td></tr>").replace("</table>","</table><table><tr><td>2026/11/01</td></tr></table>"),"HOLD_PREDECESSOR_TABLE_IDENTITY")
if __name__=="__main__":
    unittest.main()

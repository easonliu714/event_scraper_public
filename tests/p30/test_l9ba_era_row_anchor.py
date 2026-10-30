#!/usr/bin/env python3
"""P30-L9-BA bounded row-link identity negative regression."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9ba_era_row_anchor import inspect
from p30_l9av_era_source_role import TITLE

def page(link):
    return (f"<h1>{TITLE}</h1><section><div><h4>場次列表</h4></div>"
            f"<div><table><tr><th>日期</th><th>時間</th><th>連結</th></tr>"
            f'<tr><td>2026/11/01</td><td>19:30</td><td>{link}</td></tr>'
            "</table></div><h4>退票方式</h4></section>")

class Cases(unittest.TestCase):
    def check(self, link, decision):
        out = inspect(page(link), "2026-10-30T05:55:00Z")
        self.assertEqual(out["decision"], decision)
        self.assertEqual((out["acceptedFields"], out["goldenAccepted"], out["published"]), (0, 0, False))
        self.assertIsNone(out["ticketEventId"])
        self.assertIsNone(out["sessionId"])
        return out
    def test_same_product_link_review_only(self):
        x = self.check('<a href="/activity?PRODUCT_ID=P1GFK34F&session=123">場次</a>',
                       "REVIEW_SAME_PRODUCT_ANCHOR_NO_SESSION_ID_NO_FIELDS")
        self.assertEqual(x["sessionParameterKeyHints"], 1)
    def test_external_link_hold(self):
        self.check('<a href="https://tickets.example.org/session">訂票</a>',
                   "HOLD_EXTERNAL_ANCHOR_NOT_TICKET_SESSION")
    def test_other_product_hold(self):
        self.check('<a href="/activity?PRODUCT_ID=P1GFK34X">訂票</a>',
                   "HOLD_ROW_ANCHOR_PRODUCT_MISMATCH")
    def test_same_origin_without_product_hold(self):
        self.check('<a href="/purchase">訂票</a>', "HOLD_ROW_ANCHOR_NO_SAME_PRODUCT_ID")
    def test_javascript_hold(self):
        self.check('<a href="javascript:open()">訂票</a>', "HOLD_NON_NAVIGABLE_ANCHOR")
    def test_fragment_hold(self):
        self.check('<a href="#">訂票</a>', "HOLD_NON_NAVIGABLE_ANCHOR")
    def test_two_links_hold(self):
        self.check('<a href="/a">A</a><a href="/b">B</a>', "HOLD_ROW_ANCHOR_NOT_UNIQUE")
    def test_no_anchor_hold(self):
        self.check("未提供", "HOLD_ROW_ANCHOR_NOT_UNIQUE")
    def test_wrong_title_hold(self):
        x = inspect(page('<a href="/activity?PRODUCT_ID=P1GFK34F">訂票</a>').replace(TITLE, "WRONG"), "2026-10-30T05:55:00Z")
        self.assertEqual(x["decision"], "HOLD_PREDECESSOR_CELL_SCOPE")
    def test_no_session_date_hold(self):
        x = inspect(page('<a href="/activity?PRODUCT_ID=P1GFK34F">訂票</a>').replace("2026/11/01", "日期未定"), "2026-10-30T05:55:00Z")
        self.assertEqual(x["decision"], "HOLD_PREDECESSOR_CELL_SCOPE")
if __name__ == "__main__":
    unittest.main()

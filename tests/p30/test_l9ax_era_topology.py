#!/usr/bin/env python3
"""P30-L9-AX strict source-local topology diagnostics and negative regressions."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9ax_era_topology import topology
from p30_l9av_era_source_role import TITLE

D = f'<h1>{TITLE}</h1><section><h4>場次列表</h4><div><table><tr><td>2026/11/01</td></tr></table></div><h4>退票方式</h4><p>2026/10/22</p></section>'

class Cases(unittest.TestCase):
    def check(self, html, decision):
        x = topology(html, "2026-10-30T02:55:00Z")
        self.assertEqual(x["decision"], decision)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
        self.assertIsNone(x["ticketEventId"])
        self.assertEqual(x["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        return x
    def test_nested_table_is_diagnostic_only(self):
        x = self.check(D, "REVIEW_TABLE_SCOPE_DIAGNOSTIC_NO_FIELDS")
        self.assertTrue(any(s.get("boundedTables", 0) for s in x["scopes"]))
    def test_global_unrelated_table_refused(self):
        self.check(f'<h1>{TITLE}</h1><h4>場次列表</h4><h4>退票方式</h4><table><tr><td>2026/11/01</td></tr></table>',
                   "HOLD_NO_BOUNDED_SESSION_TABLE_TOPOLOGY")
    def test_no_session_heading(self):
        self.check(D.replace("場次列表", "其他"), "HOLD_SESSION_HEADING_NOT_UNIQUE")
    def test_duplicate_heading(self):
        self.check(D + "<h4>場次列表</h4>", "HOLD_SESSION_HEADING_NOT_UNIQUE")
    def test_wrong_h1(self):
        self.check(D.replace(TITLE, "別的活動"), "HOLD_DETAIL_H1_NOT_UNIQUE")
    def test_duplicate_h1(self):
        self.check(D + f"<h1>{TITLE}</h1>", "HOLD_DETAIL_H1_NOT_UNIQUE")
    def test_refund_in_following_sibling_refused(self):
        self.check(f'<h1>{TITLE}</h1><h4>場次列表</h4><div>退票方式<table><tr><td>2026/10/22</td></tr></table></div>',
                   "HOLD_NO_BOUNDED_SESSION_TABLE_TOPOLOGY")
    def test_large_scope_is_bounded(self):
        self.check(f'<h1>{TITLE}</h1><h4>場次列表</h4>' + '<p>x</p>' * 90,
                   "HOLD_NO_BOUNDED_SESSION_TABLE_TOPOLOGY")
    def test_no_implicit_field_acceptance(self):
        x = self.check(D + '<a href="https://ticket.com.tw/">立即訂購</a>',
                       "REVIEW_TABLE_SCOPE_DIAGNOSTIC_NO_FIELDS")
        self.assertEqual(x["acceptedFields"], 0)

if __name__ == "__main__":
    unittest.main()

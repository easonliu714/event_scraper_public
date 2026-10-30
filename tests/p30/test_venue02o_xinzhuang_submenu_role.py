#!/usr/bin/env python3
"""VENUE-02O official submenu source-role diagnostics, fail-closed."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02o_xinzhuang_submenu_role import inspect

class Cases(unittest.TestCase):
    def check(self, html, decision):
        x = inspect(html, "2026-10-30T05:55:00Z")
        self.assertEqual(x["decision"], decision)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
        self.assertIsNone(x["ticketEventId"])
        return x
    def test_official_candidate_link_review_not_list_pass(self):
        x = self.check('<h1>展演活動</h1><a href="/activity/abc">展演活動 A</a>',
                       "REVIEW_SUBMENU_DETAIL_LINK_HINTS_NO_LIST_PASS")
        self.assertEqual(x["candidateDetailLinkHints"], 1)
    def test_nav_only_hold(self):
        self.check('<h1>展演活動</h1><a href="/contact">聯絡我們</a>',
                   "HOLD_SUBMENU_NO_UNIQUE_EVENT_DETAIL_LINK")
    def test_offsite_link_rejected(self):
        self.check('<h1>展演活動</h1><a href="https://evil.example/activity/abc">展演活動 A</a>',
                   "HOLD_SUBMENU_NO_UNIQUE_EVENT_DETAIL_LINK")
    def test_no_structure_hold(self):
        self.check("<div>網站內容</div>", "HOLD_SUBMENU_NO_VISIBLE_EVENT_STRUCTURE")
    def test_generic_news_not_detail(self):
        self.check('<h1>展演活動</h1><a href="/news">最新消息</a>',
                   "HOLD_SUBMENU_NO_UNIQUE_EVENT_DETAIL_LINK")
    def test_path_without_event_label_hold(self):
        self.check('<h1>展演活動</h1><a href="/activity/abc">聯絡我們</a>',
                   "HOLD_SUBMENU_NO_UNIQUE_EVENT_DETAIL_LINK")
    def test_non_https_hold(self):
        self.check('<h1>展演活動</h1><a href="http://www.xzcac.ntpc.gov.tw/activity/abc">展演活動 A</a>',
                   "HOLD_SUBMENU_NO_UNIQUE_EVENT_DETAIL_LINK")
    def test_oversize_heading_hold(self):
        self.check("<h1>" + "X"*241 + "</h1>", "HOLD_OVERSIZE_HEADING")
    def test_duplicate_link_dedup(self):
        x = self.check('<h1>展演活動</h1><a href="/activity/abc">展演活動 A</a><a href="/activity/abc">展演活動 A</a>',
                       "REVIEW_SUBMENU_DETAIL_LINK_HINTS_NO_LIST_PASS")
        self.assertEqual(x["candidateDetailLinkHints"], 1)
if __name__ == "__main__":
    unittest.main()

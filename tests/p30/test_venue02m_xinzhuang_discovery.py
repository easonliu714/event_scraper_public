#!/usr/bin/env python3
"""P30-VENUE-02M official same-origin link discovery and refusal cases."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_venue02m_xinzhuang_discovery import inspect_home, inspect_index, same_origin

LINK = '<a href="/activity">活動資訊</a>'
class Cases(unittest.TestCase):
    def check(self, html, decision):
        x = inspect_home(html, "2026-10-30T03:55:00Z")
        self.assertEqual(x["decision"], decision)
        self.assertEqual((x["acceptedFields"], x["goldenAccepted"], x["published"]), (0, 0, False))
        self.assertIsNone(x["ticketEventId"])
        self.assertEqual(x["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        return x
    def test_single_official_index_review_only(self):
        x = self.check(LINK, "REVIEW_ONE_FIRST_PARTY_INDEX_LINK_NOT_LIST_PASS")
        self.assertEqual(x["candidateIndexURL"], "https://www.xzcac.ntpc.gov.tw/activity")
    def test_duplicate_link_deduplicated(self):
        self.check(LINK + LINK, "REVIEW_ONE_FIRST_PARTY_INDEX_LINK_NOT_LIST_PASS")
    def test_two_distinct_index_links_ambiguous(self):
        self.check(LINK + '<a href="/calendar">活動行事曆</a>',
                   "HOLD_INDEX_DISCOVERY_ZERO_OR_AMBIGUOUS")
    def test_zero_candidate(self):
        self.check('<a href="/contact">聯絡我們</a>', "HOLD_INDEX_DISCOVERY_ZERO_OR_AMBIGUOUS")
    def test_offsite_host_rejected(self):
        self.check('<a href="https://evil.example/activity">活動資訊</a>',
                   "HOLD_INDEX_DISCOVERY_ZERO_OR_AMBIGUOUS")
    def test_subdomain_trick_rejected(self):
        self.assertIsNone(same_origin("https://www.xzcac.ntpc.gov.tw.evil.example/activity"))
    def test_http_rejected(self):
        self.assertIsNone(same_origin("http://www.xzcac.ntpc.gov.tw/activity"))
    def test_credentials_rejected(self):
        self.assertIsNone(same_origin("https://user:pass@www.xzcac.ntpc.gov.tw/activity"))
    def test_homepage_not_index(self):
        self.check('<a href="/">活動資訊</a>', "HOLD_INDEX_DISCOVERY_ZERO_OR_AMBIGUOUS")
    def test_non_event_role_rejected(self):
        self.check('<a href="/hire">場地租借活動資訊</a>', "HOLD_INDEX_DISCOVERY_ZERO_OR_AMBIGUOUS")
    def test_index_is_not_event_identity(self):
        x = inspect_index('<h1>節目表</h1><a href="/event/1">演出</a>', "2026-10-30T03:55:00Z")
        self.assertEqual(x["indexDecision"], "REVIEW_INDEX_STRUCTURE_ONLY_NO_EVENT_ID")
        self.assertEqual(x["indexVisibleLinks"], 1)

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""VENUE-02N candidate URL/role provenance; no inference of event identity."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02n_xinzhuang_link_role import inspect
class Cases(unittest.TestCase):
    def check(self,html,decision):
        x=inspect(html,"2026-10-30T04:55:00Z")
        self.assertEqual(x["decision"],decision)
        self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
        self.assertIsNone(x["ticketEventId"])
        return x
    def test_two_candidate_hold_with_urls(self):
        x=self.check('<nav><a href="/a">活動資訊</a><a href="/b">活動行事曆</a></nav>',"HOLD_MULTIPLE_INDEX_ROLES_REQUIRE_SOURCE_DETAIL")
        self.assertEqual([c["path"] for c in x["candidates"]],["/a","/b"])
        self.assertEqual(x["candidates"][0]["containerRole"],"nav")
    def test_one_candidate_review_only(self):
        x=self.check('<main><a href="/events">活動資訊</a></main>',"REVIEW_SINGLE_LINK_ROLE_NOT_LIST_PASS")
        self.assertEqual(x["candidateCount"],1)
    def test_duplicate_anchor_dedup(self):
        x=self.check('<a href="/events">活動資訊</a><a href="/events">活動資訊</a>',"REVIEW_SINGLE_LINK_ROLE_NOT_LIST_PASS")
        self.assertEqual(x["candidates"][0]["occurrences"],2)
    def test_offsite_rejected(self):
        self.check('<a href="https://evil.example/a">活動資訊</a>',"HOLD_NO_OFFICIAL_INDEX_CANDIDATE")
    def test_non_https_rejected(self):
        self.check('<a href="http://www.xzcac.ntpc.gov.tw/a">活動資訊</a>',"HOLD_NO_OFFICIAL_INDEX_CANDIDATE")
    def test_credentials_rejected(self):
        self.check('<a href="https://x:y@www.xzcac.ntpc.gov.tw/a">活動資訊</a>',"HOLD_NO_OFFICIAL_INDEX_CANDIDATE")
    def test_negative_role_rejected(self):
        self.check('<a href="/rent">場地租借活動資訊</a>',"HOLD_NO_OFFICIAL_INDEX_CANDIDATE")
    def test_homepage_not_index(self):
        self.check('<a href="/">活動資訊</a>',"HOLD_NO_OFFICIAL_INDEX_CANDIDATE")
    def test_empty_rejected(self):
        self.check('<div>無活動</div>',"HOLD_NO_OFFICIAL_INDEX_CANDIDATE")
    def test_oversize_label_rejected(self):
        self.check('<a href="/events">活動資訊'+"x"*150+'</a>',"HOLD_OVERSIZE_LINK_LABEL")
    def test_label_does_not_verify_ticket_id(self):
        x=self.check('<a href="/events">展演活動</a>',"REVIEW_SINGLE_LINK_ROLE_NOT_LIST_PASS")
        self.assertIsNone(x["ticketEventId"])
if __name__=="__main__":
    unittest.main()

#!/usr/bin/env python3
"""L9-BS public-source-derived receipt boundary tests; never publish."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bs_huashan_accupass_direct_edge import audit
VURL = "https://www.huashan1914.com/exhibition/%E6%9C%97%E8%AE%80%E6%B2%99%E9%BE%8D-%E9%80%99%E6%A8%A3%E5%95%8A%EF%BC%81%E9%82%A3%E4%BA%9B%E7%86%9F%E6%82%89%E5%8F%88%E9%99%8C%E7%94%9F%E7%9A%84%E6%97%A5%E5%B8%B8"
TURL = "https://www.accupass.com/event/2609240212371623247500"
CORE = "這樣啊！那些熟悉又陌生的日常"
def samples():
    common = {"coreTitle": CORE, "eventDate": "2026-10-31",
              "dateRole": "EVENT_SESSION", "start": "16:00", "end": "17:30",
              "timezone": "Asia/Taipei", "observed_at": "2026-10-30T23:58:00Z"}
    v = dict(common, source="HUASHAN_PLATFORM_13", url=VURL,
             heading="2026華文朗讀節〖朗讀沙龍〗" + CORE,
             ticketLinks=[TURL], room="中3A館 2樓拱廳")
    t = dict(common, source="ACCUPASS_PLATFORM_02", url=TURL,
             heading="2026華文朗讀節 一粒米．好土台灣〖朗讀沙龍〗娘娘、瑞夫—" + CORE,
             room="中3館2樓拱廳")
    return v, t
class Cases(unittest.TestCase):
    def test_actual_public_room_difference_is_hold(self):
        v,t = samples()
        x = audit(v,t)
        self.assertEqual(x["decision"], "HOLD_DIRECT_LINK_SESSION_MATCH_VENUE_ROOM_CONFLICT")
        self.assertTrue(x["directLinkBound"])
        self.assertTrue(x["sameSession"])
        self.assertTrue(x["venueConflict"])
        self.assertEqual(len(x["candidateProvenance"]), 8)
        self.assertEqual(x["acceptedFields"], 0)
    def test_exact_room_only_review(self):
        v,t = samples(); t["room"] = v["room"]
        self.assertEqual(audit(v,t)["decision"], "REVIEW_DIRECT_LINK_SESSION_AND_ROOM_NO_FORMAL_FIELDS")
    def test_ticket_url_query_rejected(self):
        v,t = samples(); t["url"] += "?utm=1"; v["ticketLinks"]=[t["url"]]
        self.assertEqual(audit(v,t)["decision"], "HOLD_TICKET_URL_NOT_UNIQUE_DIRECT")
    def test_ticket_host_spoof_rejected(self):
        v,t = samples(); t["url"] = "https://www.accupass.com.evil.example/event/2609240212371623247500"
        v["ticketLinks"] = [t["url"]]
        self.assertEqual(audit(v,t)["decision"], "HOLD_TICKET_URL_NOT_UNIQUE_DIRECT")
    def test_duplicate_ticket_links_rejected(self):
        v,t = samples(); v["ticketLinks"].append(t["url"])
        self.assertEqual(audit(v,t)["decision"], "HOLD_TICKET_URL_NOT_UNIQUE_DIRECT")
    def test_date_mismatch_rejected(self):
        v,t = samples(); t["eventDate"] = "2026-11-01"
        self.assertEqual(audit(v,t)["decision"], "HOLD_SESSION_CROSS_SOURCE_MISMATCH")
    def test_time_mismatch_rejected(self):
        v,t = samples(); t["start"] = "16:30"
        self.assertEqual(audit(v,t)["decision"], "HOLD_SESSION_CROSS_SOURCE_MISMATCH")
    def test_sale_role_not_session(self):
        v,t = samples(); t["dateRole"] = "SALE"
        self.assertEqual(audit(v,t)["decision"], "HOLD_DATE_ROLE_NOT_EVENT_SESSION")
    def test_core_title_mismatch(self):
        v,t = samples(); t["coreTitle"] = "完全不同的節目與活動名稱"
        self.assertEqual(audit(v,t)["decision"], "HOLD_CROSS_SOURCE_TITLE_CORE")
    def test_missing_provenance(self):
        v,t = samples(); t.pop("observed_at")
        self.assertEqual(audit(v,t)["decision"], "HOLD_OBSERVATION_PROVENANCE")
    def test_no_formal_acceptance_even_when_review(self):
        v,t = samples(); t["room"] = v["room"]
        x = audit(v,t)
        self.assertEqual(x["goldenAccepted"], 0)
        self.assertFalse(x["published"])
        self.assertIsNone(x["ticketEventId"])
if __name__ == "__main__":
    unittest.main()

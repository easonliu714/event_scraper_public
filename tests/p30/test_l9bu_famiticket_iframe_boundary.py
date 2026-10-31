#!/usr/bin/env python3
"""P30-L9-BU: official FamiTicket index to iframe-only detail refusal."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bu_famiticket_iframe_boundary import inspect, safe_detail

URL = ("https://www.famiticket.com.tw/Home/Activity/Info/"
       "RgBhADYAOABvAGoANQBDAEYAdQB0AEIAbwBVACsAOAB0AGUAUgBkADUAMABrADUAVABiAE0AMwB4ADcAcABMAHoAUgB2AGMAVABSAFEAbQB3AG8ARQA9AA2")
def sample():
    return (dict(index_url="https://www.famiticket.com.tw/Home",
                 detail_url=URL, title="Ultra Taiwan 2026 超世代音樂節",
                 list_date="2026.11.14(六)", category="展覽 演唱會",
                 observed_at="2026-10-31"),
            dict(url=URL, iframe_only=True, heading=None))

class Cases(unittest.TestCase):
    def test_first_party_opaque_url(self):
        self.assertTrue(safe_detail(URL))
    def test_observed_mixed_category_iframe_hold(self):
        row, detail = sample()
        r = inspect(row, detail)
        self.assertEqual(r["decision"], "HOLD_MIXED_LIST_CATEGORY_AND_IFRAME_IDENTITY")
        self.assertEqual(len(r["candidateProvenance"]), 3)
        self.assertFalse(r["sameIdTitleVerified"])
        self.assertEqual(r["acceptedFields"], 0)
    def test_single_category_still_iframe_hold(self):
        row, detail = sample()
        row["category"] = "演唱會"
        self.assertEqual(inspect(row, detail)["decision"], "HOLD_IFRAME_ONLY_NO_SAME_ID_DETAIL_TITLE")
    def test_voucher_not_event(self):
        row, detail = sample()
        row["category"] = "交換票"
        self.assertEqual(inspect(row, detail)["decision"], "HOLD_VOUCHER_OR_NON_EVENT_CATEGORY")
    def test_other_origin_refused(self):
        row, detail = sample()
        row["detail_url"] = row["detail_url"].replace("www.famiticket.com.tw", "evil.example")
        self.assertEqual(inspect(row, detail)["decision"], "HOLD_SOURCE_URL_OR_OPAQUE_IDENTITY")
    def test_detail_url_mismatch_refused(self):
        row, detail = sample()
        detail["url"] += "x"
        self.assertEqual(inspect(row, detail)["decision"], "HOLD_SOURCE_URL_OR_OPAQUE_IDENTITY")
    def test_query_smuggling_refused(self):
        self.assertFalse(safe_detail(URL + "?sid=other"))
    def test_non_https_refused(self):
        self.assertFalse(safe_detail(URL.replace("https:", "http:")))
    def test_heading_cannot_be_claimed_from_iframe(self):
        row, detail = sample()
        detail["heading"] = row["title"]
        self.assertEqual(inspect(row, detail)["decision"], "HOLD_DETAIL_VIEW_NOT_INDEPENDENTLY_VERIFIED")
    def test_missing_date_provenance_refused(self):
        row, detail = sample()
        row["observed_at"] = ""
        self.assertEqual(inspect(row, detail)["decision"], "HOLD_LIST_ROLE_OR_PROVENANCE")
    def test_no_formal_publication(self):
        row, detail = sample()
        r = inspect(row, detail)
        self.assertIsNone(r["ticketEventId"])
        self.assertEqual(r["goldenAccepted"], 0)
        self.assertFalse(r["published"])
        self.assertEqual(r["releaseState"], "HARD_HOLD_NO_PUBLICATION")
if __name__ == "__main__":
    unittest.main()

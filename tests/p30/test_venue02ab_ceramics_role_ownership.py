#!/usr/bin/env python3
"""Two real source-observed Ceramics date/location layouts; fail closed."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02ab_ceramics_role_ownership import classify_field_ownership as audit
TITLE="殼之巢 — 情景之階：佐藤雅之個展"
def detail(body,heading=TITLE):
    return f"<main><h3>{heading}</h3><article>{body}</article></main>"
SEPARATE="<p>展覽日期：2026年10月13日至2026年11月10日</p><p>展覽地點：1樓陽光特展室</p>"
INLINE="<p>展覽日期:2026年10月16日至2026年11月15日/展覽地點:b1陶藝長廊</p>"
class Cases(unittest.TestCase):
    def test_official_separate_labels(self):
        r=audit(detail(SEPARATE),TITLE)
        self.assertEqual(r["decision"],"REVIEW_SINGLE_LEAF_ROLE_NOT_ACCEPTED")
        self.assertEqual((r["dateRoleNodes"],r["venueRoleNodes"]),(1,1))
        self.assertEqual(r["acceptedFields"],0)
    def test_official_inline_slash_labels(self):
        r=audit(detail(INLINE),TITLE)
        self.assertEqual(r["decision"],"REVIEW_SINGLE_LEAF_ROLE_NOT_ACCEPTED")
        self.assertEqual(r["distinctDateValues"],1)
    def test_same_venue_repeated_holds(self):
        r=audit(detail(SEPARATE+"<p>展覽地點：1樓陽光特展室</p>"),TITLE)
        self.assertEqual(r["decision"],"HOLD_DUPLICATE_SAME_VALUE_OWNERSHIP")
    def test_conflicting_venue_holds(self):
        r=audit(detail(SEPARATE+"<p>展覽地點：二樓展廳</p>"),TITLE)
        self.assertEqual(r["decision"],"HOLD_CONFLICTING_ROLE_VALUES")
    def test_duplicate_date_holds(self):
        r=audit(detail(SEPARATE+"<p>展覽日期：2026年10月13日至2026年11月10日</p>"),TITLE)
        self.assertEqual(r["decision"],"HOLD_DUPLICATE_SAME_VALUE_OWNERSHIP")
    def test_conflicting_date_holds(self):
        r=audit(detail(SEPARATE+"<p>展覽日期：2026年10月14日至2026年11月10日</p>"),TITLE)
        self.assertEqual(r["decision"],"HOLD_CONFLICTING_ROLE_VALUES")
    def test_invalid_calendar_holds(self):
        r=audit(detail(SEPARATE.replace("10月13日","2月30日")),TITLE)
        self.assertEqual(r["decision"],"HOLD_INVALID_OR_MIXED_FIELD_ROLE")
    def test_inverted_range_holds(self):
        r=audit(detail(SEPARATE.replace("10月13日","12月13日")),TITLE)
        self.assertEqual(r["decision"],"HOLD_INVALID_OR_MIXED_FIELD_ROLE")
    def test_registration_mixed_holds(self):
        r=audit(detail(SEPARATE+"<p>報名期間：2026年10月1日/展覽地點：一樓大廳</p>"),TITLE)
        self.assertEqual(r["decision"],"HOLD_INVALID_OR_MIXED_FIELD_ROLE")
    def test_wrong_heading_holds(self):
        r=audit(detail(SEPARATE,heading="不相符的展覽名稱"),TITLE)
        self.assertEqual(r["decision"],"HOLD_DETAIL_HEADING_IDENTITY")
    def test_missing_location_holds(self):
        r=audit(detail("<p>展覽日期：2026年10月13日至2026年11月10日</p>"),TITLE)
        self.assertEqual(r["decision"],"HOLD_MISSING_EXHIBITION_FIELD_ROLE")
    def test_no_ticket_id_or_publication(self):
        r=audit(detail(SEPARATE),TITLE)
        self.assertIsNone(r["ticketEventId"])
        self.assertFalse(r["published"])
        self.assertEqual(r["goldenAccepted"],0)
if __name__=="__main__":
    unittest.main()

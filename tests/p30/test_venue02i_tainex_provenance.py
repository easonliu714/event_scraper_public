#!/usr/bin/env python3
"""TAINEX venue 689/690 source identity, label and provenance refusal."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02i_tainex_provenance import inspect_detail,URL
WHEN="2026-10-30T00:00:00Z"
H="<h1>2026臺灣茶業博覽會</h1>"
L="<p>展覽活動期間 2026/11/13-16</p><p>活動地點 一樓展場</p><p>主辦單位</p>"
class Tests(unittest.TestCase):
    def check(self,html,decision,when=WHEN):
        x=inspect_detail(html,when)
        self.assertEqual(x["decision"],decision)
        self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
        self.assertIsNone(x["ticketEventId"])
        self.assertEqual(x["releaseState"],"HARD_HOLD_NO_PUBLICATION")
        return x
    def test_one_detail_provenance(self):
        x=self.check("<html>"+H+L+"</html>","REVIEW_ONE_OFFICIAL_DETAIL_ROLE_PROVENANCE_NO_PROMOTION")
        self.assertEqual(x["venueLocalIdReview"],"690")
        self.assertEqual(x["distinctFrom689"],"REVIEW_DISTINCT_SOURCE_LOCAL_IDS_NO_MERGE")
        self.assertEqual(set(x["fieldProvenance"]),{"exhibitionPeriod","venue","organizer"})
        for v in x["fieldProvenance"].values():
            self.assertEqual(v["source"],URL)
            self.assertEqual(v["observed_at"],WHEN)
            self.assertTrue(v["decision"].startswith("REVIEW_"))
    def test_missing_title(self):
        self.check(L,"HOLD_DETAIL_EXACT_TITLE_NOT_UNIQUE")
    def test_duplicate_title(self):
        self.check(H+H+L,"HOLD_DETAIL_EXACT_TITLE_NOT_UNIQUE")
    def test_missing_venue(self):
        self.check(H+"<p>展覽活動期間</p><p>主辦單位</p>","HOLD_ROLE_LABEL_NOT_UNIQUE")
    def test_duplicate_period(self):
        self.check(H+L+"<p>展覽活動期間</p>","HOLD_ROLE_LABEL_NOT_UNIQUE")
    def test_missing_organizer(self):
        self.check(H+"<p>展覽活動期間</p><p>活動地點</p>","HOLD_ROLE_LABEL_NOT_UNIQUE")
    def test_invalid_timestamp(self):
        self.check(H+L,"HOLD_INPUT",when="tomorrow")
    def test_empty(self):
        self.check("","HOLD_INPUT")
    def test_wrong_heading(self):
        self.check("<h1>2026臺灣國際咖啡展</h1>"+L,"HOLD_DETAIL_EXACT_TITLE_NOT_UNIQUE")
    def test_oversize(self):
        self.check(H+L+"x"*180001,"HOLD_INPUT")
if __name__=="__main__":unittest.main()

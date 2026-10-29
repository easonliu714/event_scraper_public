#!/usr/bin/env python3
"""Fail-closed local-ancestor regression tests; no network."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9au_famiticket_ancestry import inspect_ancestry
H='<h4>CC同人創作展</h4>'
M='<img alt="《活動資訊》">'
L='<p>活動時間 10:30</p><p>活動地點 五號倉庫</p><p>活動票價 單日票</p>'
class Tests(unittest.TestCase):
    def check(self,html,expected):
        v=inspect_ancestry(html)
        self.assertEqual(v["decision"],expected)
        self.assertEqual((v["acceptedFields"],v["goldenAccepted"],v["published"]),(0,0,False))
        self.assertEqual(v["releaseState"],"HARD_HOLD_NO_PUBLICATION")
        self.assertIsNone(v["ticketEventId"])
        return v
    def test_bounded_div(self):
        v=self.check("<div>"+H+M+L+"</div>","REVIEW_BOUNDED_COMMON_ANCESTRY_NO_FIELDS")
        self.assertEqual(v["commonAncestorTag"],"div")
    def test_unrelated_regions(self):
        self.check("<div>"+H+"</div><div>"+M+L+"</div>","HOLD_NO_COMMON_VISIBLE_CONTAINER")
    def test_other_heading(self):
        self.check("<div>"+H+M+L+"<h4>其他活動</h4></div>","HOLD_OTHER_HEADINGS_IN_REGION")
    def test_refund(self):
        self.check("<div>"+H+M+L+"<p>退票期限 11月20日</p></div>","HOLD_REFUND_MIXED_IN_REGION")
    def test_missing_label(self):
        self.check("<div>"+H+M+"<p>活動時間 10:30</p></div>","HOLD_NONUNIQUE_ROLE_LABELS")
    def test_duplicate_label(self):
        self.check("<div>"+H+M+L+"<p>活動票價 再次出現</p></div>","HOLD_NONUNIQUE_ROLE_LABELS")
    def test_hidden_title(self):
        self.check('<div><div hidden>'+H+'</div>'+M+L+'</div>',"HOLD_PRIOR_IDENTITY")
    def test_ambiguous_markers(self):
        self.check("<div>"+H+M+M+L+"</div>","HOLD_PRIOR_IDENTITY")
    def test_no_title(self):
        self.check("<div>"+M+L+"</div>","HOLD_PRIOR_IDENTITY")
    def test_large_region(self):
        self.check("<div>"+H+M+L+"a"*4600+"</div>","HOLD_REGION_SIZE_OR_GLOBAL_WRAPPER")
if __name__=="__main__":unittest.main()

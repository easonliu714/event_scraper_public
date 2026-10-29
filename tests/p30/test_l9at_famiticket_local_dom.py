#!/usr/bin/env python3
"""L9-AT negative controls: same heading/marker counts are not locality."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9at_famiticket_local_dom import inspect_local
from p30_l9as_famiticket_live_dom import inspect_html,URL,TITLE

GOOD='<section><h4>CC同人創作展</h4><img alt="《活動資訊》"><p>活動時間│10:30-16:00</p><p>活動地點│松山</p><p>活動票價│單日票200元</p></section>'
SPLIT='<main><section><h4>CC同人創作展</h4></section><aside><img alt="《活動資訊》"></aside></main>'
class LocalityTests(unittest.TestCase):
    def check(self,html,expected):
        r=inspect_local(html)
        self.assertEqual(r["decision"],expected)
        self.assertEqual((r["acceptedFields"],r["goldenAccepted"],r["published"]),(0,0,False))
        self.assertEqual(r["releaseState"],"HARD_HOLD_NO_PUBLICATION")
        self.assertIsNone(r["ticketEventId"])
        return r
    def test_same_semantic_section(self):
        r=self.check(GOOD,"REVIEW_LOCAL_ROLE_TOPOLOGY_NO_FIELD_ACCEPTANCE")
        self.assertEqual(r["roleLabelCounts"],{"活動時間":1,"活動地點":1,"活動票價":1})
    def test_prior_false_positive_now_refused(self):
        self.assertTrue(inspect_html(SPLIT,URL,TITLE)["decision"].startswith("REVIEW_"))
        self.check(SPLIT,"HOLD_NO_SHARED_SEMANTIC_EVENT_SECTION")
    def test_disjoint_sections(self):
        self.check('<section><h4>CC同人創作展</h4></section><section><img alt="《活動資訊》"></section>',"HOLD_NO_SHARED_SEMANTIC_EVENT_SECTION")
    def test_missing_local_label(self):
        self.check(GOOD.replace("活動地點","展覽地點"),"HOLD_NONUNIQUE_LOCAL_ROLE_LABELS")
    def test_duplicate_local_label(self):
        self.check(GOOD.replace("</section>","<p>活動時間│12:00</p></section>"),"HOLD_NONUNIQUE_LOCAL_ROLE_LABELS")
    def test_refund_in_section(self):
        self.check(GOOD.replace("</section>","<p>退票期限2026年11月1日</p></section>"),"HOLD_REFUND_WITHIN_EVENT_SECTION")
    def test_marker_hidden(self):
        self.check(GOOD.replace("<img","<img hidden"),"HOLD_PRIOR_IDENTITY")
    def test_heading_hidden(self):
        self.check(GOOD.replace("<h4>","<h4 hidden>"),"HOLD_PRIOR_IDENTITY")
    def test_duplicate_heading(self):
        self.check(GOOD.replace("</section>","<h2>CC同人創作展</h2></section>"),"HOLD_PRIOR_IDENTITY")
    def test_no_section(self):
        self.check(GOOD.replace("<section>","<div>").replace("</section>","</div>"),"HOLD_NO_SHARED_SEMANTIC_EVENT_SECTION")
if __name__=="__main__":
    unittest.main()

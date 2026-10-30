#!/usr/bin/env python3
"""P30-L9-AV offline refusal regressions."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9av_era_source_role import inspect,HOME,DETAIL,TITLE
H=f'<a href="{DETAIL}">11/01(日) {TITLE}</a>'
D=f'<h1>{TITLE}</h1><h4>場次列表</h4><table><tr><td>2026/11/01</td></tr></table><h4>退票方式</h4><p>退票期限至2026/10/22</p>'
class Cases(unittest.TestCase):
    def check(self,home,detail,decision):
        x=inspect(home,detail,"2026-10-30T00:00:00Z")
        self.assertEqual(x["decision"],decision)
        self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
        self.assertIsNone(x["ticketEventId"])
        self.assertEqual(x["releaseState"],"HARD_HOLD_NO_PUBLICATION")
        return x
    def test_review(self):
        x=self.check(H,D,"REVIEW_SAME_PRODUCT_LIST_DETAIL_ROLE_BOUNDARY_NO_FIELDS")
        self.assertEqual(x["roleDecisions"]["REFUND"],"REFUND_DEADLINE_NOT_EVENT_DATE")
    def test_no_list(self):self.check("<div></div>",D,"HOLD_LIST_PRODUCT_TITLE_OR_URL")
    def test_duplicate_product(self):self.check(H+H,D,"HOLD_LIST_PRODUCT_TITLE_OR_URL")
    def test_wrong_title(self):self.check(H.replace(TITLE,"其他"),D,"HOLD_LIST_PRODUCT_TITLE_OR_URL")
    def test_wrong_product(self):self.check(H.replace("P1GFK34F","P1GFK34G"),D,"HOLD_LIST_PRODUCT_TITLE_OR_URL")
    def test_missing_h1(self):self.check(H,D.replace("<h1>","<h2>").replace("</h1>","</h2>"),"HOLD_DETAIL_EXACT_H1")
    def test_duplicate_h1(self):self.check(H,D+f"<h1>{TITLE}</h1>","HOLD_DETAIL_EXACT_H1")
    def test_no_session(self):self.check(H,D.replace("<h4>場次列表</h4>",""),"HOLD_SESSION_SECTION_NOT_UNIQUE")
    def test_duplicate_session(self):self.check(H,D+"<h4>場次列表</h4>","HOLD_SESSION_SECTION_NOT_UNIQUE")
if __name__=="__main__":unittest.main()

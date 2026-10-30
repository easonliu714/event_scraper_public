#!/usr/bin/env python3
"""L9-BD role classification is exact-label and never a field acceptance."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9bd_tixfun_field_role import role_of,inspect_local
class Cases(unittest.TestCase):
    def test_performance_role(self): self.assertEqual(role_of("演出時間："),"PERFORMANCE_DATE")
    def test_sale_not_performance(self): self.assertEqual(role_of("售票時間"),"SALE_TIME")
    def test_refund_not_performance(self): self.assertEqual(role_of("退票期限"),"REFUND")
    def test_price_role(self): self.assertEqual(role_of("票價"),"PRICE")
    def test_partial_label_rejected(self): self.assertIsNone(role_of("最新演出時間與售票時間"))
    def test_value_not_label(self): self.assertIsNone(role_of("2026/10/30 19:30"))
    def test_unique_heading_local(self):
        h="<section><h1>灣聲映像館VIII</h1><p>演出時間</p><p>售票時間</p><p>退票期限</p></section>"
        x=inspect_local(h)
        self.assertEqual(x["decision"],"REVIEW_LOCAL_ROLE_COUNTS_NO_FIELD_VALUES")
        self.assertEqual(x["acceptedFields"],0)
    def test_duplicate_heading_hold(self):
        self.assertEqual(inspect_local("<h1>灣聲映像館VIII</h1><h2>灣聲映像館VIII</h2>")["decision"],"HOLD_TITLE_HEADING_NOT_UNIQUE")
    def test_no_heading_hold(self):
        self.assertEqual(inspect_local("<p>演出時間</p>")["decision"],"HOLD_TITLE_HEADING_NOT_UNIQUE")
if __name__=="__main__": unittest.main()

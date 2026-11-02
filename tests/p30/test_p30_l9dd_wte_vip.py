"""P30-L9-DD strict source/role/year contradiction regression."""
import unittest
from scripts import p30_l9dd_wte_vip as m
STAMP="2026-11-02T11:53:00+08:00"
def sample():
    return dict(standard_url=m.STANDARD,vip_url=m.VIP,vip_links_standard=m.STANDARD,title=m.TITLE,vip_title=m.TITLE,show="2026-11-24T19:30+08:00",venue="TICC",standard_price_range=[2300,6300],service_fee=200,vip_addons={"M_AND_G":4800,"SOUNDCHECK":2900},vip_requires_general=True,standard_presale="2026-05-25",vip_sale_claim="2025-05-25",vip_sale_weekday_label="一",vip_refund_purchase_examples=["2026-05-25","2026-05-26"],vip_refund_weekday_labels=["一","二"])
class RoleTest(unittest.TestCase):
    def test_review_conflict(self):
        r=m.inspect(sample(),STAMP)
        self.assertEqual(r["decision"],"HOLD_SALE_YEAR_WEEKDAY_REFUND_CONFLICT")
        self.assertEqual(len(r["candidateFields"]),11)
        self.assertEqual({x["role"] for x in r["candidateFields"] if x["field"].startswith("vip_refund")},{"REFUND_EXAMPLE_NOT_SALE"})
        self.assertEqual(r["acceptedFields"],0)
        self.assertFalse(r["published"])
        self.assertEqual({x["source"] for x in r["candidateFields"]},{m.STANDARD,m.VIP})
    def test_links_and_titles(self):
        for key,value,reason in [("vip_links_standard",m.VIP,"HOLD_VIP_LINKS_STANDARD"),("standard_url",m.STANDARD+"?other=1","HOLD_STANDARD_URL"),("vip_title","wrong","HOLD_TITLE"),("show","2026-11-25T19:30+08:00","HOLD_SHOW_VENUE")]:
            with self.subTest(key=key):
                x=sample();x[key]=value;self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_prices_and_unverified(self):
        for key,value,reason in [("service_fee",0,"HOLD_GENERAL_PRICE"),("vip_requires_general",False,"HOLD_ADDON_ROLE"),("standard_presale","2025-05-25","HOLD_SALE_EVIDENCE"),("ticket_session_id",0,"HOLD_UNVERIFIED_CLAIM"),("inventory",0,"HOLD_UNVERIFIED_CLAIM")]:
            with self.subTest(key=key):
                x=sample();x[key]=value;self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_vip_internal_calendar_and_refund_evidence(self):
        for key,value,reason in [("vip_sale_weekday_label","日","HOLD_VIP_INTERNAL_DATE_EVIDENCE"),("vip_refund_purchase_examples",["2025-05-25","2026-05-26"],"HOLD_VIP_INTERNAL_DATE_EVIDENCE"),("vip_refund_weekday_labels",["一","一"],"HOLD_VIP_INTERNAL_DATE_EVIDENCE")]:
            with self.subTest(key=key):
                x=sample();x[key]=value;self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
        r=m.inspect(sample(),STAMP)
        self.assertTrue(all(x["decision"]=="REVIEW" for x in r["candidateFields"]))
        self.assertEqual(r["acceptedFields"],0)
    def test_invalid(self):
        self.assertEqual(m.inspect(None,STAMP)["decision"],"HOLD_SOURCE")
        self.assertEqual(m.inspect(sample(),"2026-11-02T11:53:00")["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":unittest.main()

"""P30-VENUE-02BR conflict and identity negative tests."""
import unittest
from scripts import p30_venue02br_tpac_dates as m
STAMP="2026-11-02T11:53:00+08:00"
def sample():
    return dict(list_url=m.LIST,list_detail_href=m.DETAIL,detail_url=m.DETAIL,ticket_href=m.TICKET,list_title=m.TITLE,detail_title=m.TITLE,ticket_title=m.TITLE,list_period=["2026-11-10","2026-11-12"],detail_period=["2026-11-11","2026-11-13"],shows=list(m.SHOWS),price=600,venue="臺北表演藝術中心",ticket_program_month_days=["11/11","11/12","11/13"],ticket_bundle_sale_period=["2026-09-07","2026-11-13"])
class TPACDateTest(unittest.TestCase):
    def test_conflict_and_receipts(self):
        r=m.inspect(sample(),STAMP)
        self.assertEqual(r["decision"],"HOLD_LIST_DETAIL_DATE_CONFLICT_TICKET_PROGRAM_CORROBORATED")
        self.assertEqual(len(r["candidateFields"]),11)
        self.assertEqual({x["source"] for x in r["candidateFields"] if x["field"].startswith("ticket_")},{m.TICKET})
        self.assertTrue(all(x["role"]!="TICKET_SESSION" for x in r["candidateFields"]))
        self.assertEqual(r["acceptedFields"],0)
        self.assertEqual(r["ticketSessionIdsVerified"],0)
        self.assertFalse(r["published"])
    def test_identity(self):
        for key,value,reason in [("list_detail_href",m.DETAIL+"/2","HOLD_LIST_DETAIL_HREF"),("ticket_href",m.LIST,"HOLD_TICKET_HREF"),("ticket_title","another event","HOLD_TITLE_PARITY")]:
            with self.subTest(key=key):
                x=sample();x[key]=value;self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_date_price_and_ticket_claim(self):
        for key,value,reason in [("list_period",["2026-11-11","2026-11-13"],"HOLD_PERIOD_EVIDENCE"),("shows",m.SHOWS[:2],"HOLD_DETAIL_ROLES"),("price",True,"HOLD_DETAIL_ROLES"),("ticket_session_id",0,"HOLD_UNVERIFIED_TICKET_CLAIM")]:
            with self.subTest(key=key):
                x=sample();x[key]=value;self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_ticket_program_and_bundle_role_refusal(self):
        for key,value in [("ticket_program_month_days",["11/10","11/11","11/12"]),("ticket_program_month_days",["2026-11-11","2026-11-12","2026-11-13"]),("ticket_bundle_sale_period",["2026-11-11","2026-11-13"])]:
            with self.subTest(key=key,value=value):
                x=sample();x[key]=value;self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_TICKET_PROGRAM_ROLE_EVIDENCE")
        r=m.inspect(sample(),STAMP)
        self.assertEqual(r["ticketSessionIdsVerified"],0)
        self.assertEqual(r["acceptedFields"],0)
    def test_invalid(self):
        self.assertEqual(m.inspect(None,STAMP)["decision"],"HOLD_SOURCE")
        self.assertEqual(m.inspect(sample(),"2026-11-02T11:53:00")["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":unittest.main()

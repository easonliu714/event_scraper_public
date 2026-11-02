"""P30-L9-DC offline source/role negative tests."""
import unittest
from scripts import p30_l9dc_famiticket_teca as m
STAMP="2026-11-02T10:57:00+08:00"
def sample():
    return dict(list_url=m.LIST,list_detail_href=m.DETAIL,detail_url=m.DETAIL,
                list_title=m.TITLE,detail_title=m.TITLE,period_start=m.PERIOD[0],
                period_end=m.PERIOD[1],exhibition_hours="10:00-18:00",
                venue=m.VENUE,prices=dict(m.PRICES),purchase_control="我要購票")
class TECATest(unittest.TestCase):
    def test_review(self):
        r=m.inspect(sample(),STAMP)
        self.assertEqual(r["decision"],"REVIEW_WITH_HOLD")
        self.assertEqual(len(r["candidateFields"]),9)
        self.assertEqual({x["source"] for x in r["candidateFields"]},{m.DETAIL})
        self.assertEqual(r["acceptedFields"],0)
        self.assertEqual(r["ticketSessionIdsVerified"],0)
        self.assertFalse(r["published"])
    def test_source_roles(self):
        for k,v,reason in [
            ("list_detail_href",m.DETAIL+"?other=1","HOLD_LIST_DETAIL_HREF"),
            ("detail_url","https://www.famiticket.com.tw/Home","HOLD_DETAIL_URL"),
            ("detail_title","2026 ITF 台灣國際旅展","HOLD_TITLE_PARITY"),
            ("period_end","2026-11-23","HOLD_EXHIBITION_PERIOD"),
            ("exhibition_hours","19:00","HOLD_VENUE_OR_EXHIBITION_HOURS"),
            ("purchase_control","https://checkout.invalid","HOLD_BUTTON_ROLE")]:
            with self.subTest(k=k):
                x=sample();x[k]=v
                self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_price_roles_and_unverified_claims(self):
        for k,v in [("presale_single_day",250),("presale_two_day",500),
                    ("standard_single_day",True),("standard_two_day",0)]:
            x=sample();x["prices"][k]=v
            self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_PRICE_CATEGORIES")
        for k,v in [("checkout_href","https://checkout.invalid"),
                    ("ticket_session_id",0),("inventory",0),
                    ("showtime","2026-11-19T10:00"),("general_admission_price",150),
                    ("published_event",True),("golden_accepted",0)]:
            with self.subTest(k=k):
                x=sample();x[k]=v
                self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_UNVERIFIED_TICKET_CLAIM")
    def test_invalid(self):
        self.assertEqual(m.inspect(None,STAMP)["decision"],"HOLD_SOURCE")
        self.assertEqual(m.inspect(sample(),"2026-11-02T10:57:00")["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":unittest.main()

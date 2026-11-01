"""P30-L9-DB source role/identity negative tests. No network."""
import unittest
from scripts import p30_l9db_famiticket_itf as m
STAMP = "2026-11-02T07:53:00+08:00"
def sample():
    return dict(list_url=m.LIST, list_detail_href=m.DETAIL, detail_url=m.DETAIL,
                venue_detail_url=m.VENUE_DETAIL, list_title=m.TITLE,
                detail_title=m.TITLE, venue_title=m.VENUE_TITLE,
                period_start=m.PERIOD[0], period_end=m.PERIOD[1],
                detail_venue="台北南港展覽館一館1、4樓",
                purchase_control="我要購票")
class FamiTicketITF(unittest.TestCase):
    def test_review_not_cross_source_merge(self):
        r=m.inspect(sample(),STAMP)
        self.assertEqual(r["decision"],"REVIEW_WITH_HOLD")
        self.assertEqual(len(r["candidateFields"]),4)
        self.assertEqual({x["source"] for x in r["candidateFields"]},{m.DETAIL})
        self.assertFalse(r["crossSourceIdentityVerified"])
        self.assertEqual(r["acceptedFields"],0)
        self.assertEqual(r["ticketSessionIdsVerified"],0)
        self.assertFalse(r["published"])
    def test_source_and_title_guards(self):
        for key,value,reason in [
            ("list_detail_href",m.DETAIL+"?different=1","HOLD_LIST_DETAIL_EDGE"),
            ("detail_url","https://[bad/","HOLD_DETAIL_URL"),
            ("venue_detail_url","https://www.tainex.com.tw/event/691","HOLD_VENUE_URL"),
            ("detail_title","旅展","HOLD_TICKET_TITLE_PARITY"),
            ("venue_title",m.TITLE,"HOLD_VENUE_TITLE_ROLE"),
            ("period_end","2026-11-10","HOLD_EXHIBITION_PERIOD"),
            ("detail_venue","南港展覽館2館","HOLD_TICKET_DETAIL_VENUE"),
            ("purchase_control","https://checkout.example/","HOLD_BUTTON_ROLE"),
        ]:
            with self.subTest(key=key):
                x=sample();x[key]=value
                self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_cross_source_and_ticket_claims_quarantined(self):
        for key,value in [("ticket_href","https://www.famiticket.com.tw/cart"),
                          ("ticket_session_id","709"),("showtime","2026-11-06T10:00"),
                          ("inventory",5),("admission_price",100),
                          ("cross_source_event_id","709"),("cross_source_verified",True),
                          ("published_event",True)]:
            with self.subTest(key=key):
                x=sample();x[key]=value
                self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_UNVERIFIED_TICKET_OR_CROSS_SOURCE")
    def test_invalid_input(self):
        self.assertEqual(m.inspect(None,STAMP)["decision"],"HOLD_SOURCE")
        self.assertEqual(m.inspect(sample(),"2026-11-02T07:53:00")["decision"],"HOLD_OBSERVATION")
if __name__=="__main__": unittest.main()

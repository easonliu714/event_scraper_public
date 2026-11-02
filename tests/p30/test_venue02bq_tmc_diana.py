"""P30-VENUE-02BQ venue show vs ticket session role tests; no GET."""
import unittest
from scripts import p30_venue02bq_tmc_diana as m
STAMP="2026-11-02T10:57:00+08:00"
def sample():
    return dict(list_url=m.LIST,list_detail_href=m.DETAIL,detail_url=m.DETAIL,
                list_title=m.TITLE,detail_title=m.TITLE,venue=m.VENUE,
                organizer="MNA牛耳藝術",showtimes=list(m.SHOWS),
                sale_start="2026-09-17T12:00:00+08:00",published_date="2026-09-09",
                price_bands=list(m.PRICE_BANDS),advertised_ticket_host="ticket.mna.com.tw")
class DianaTest(unittest.TestCase):
    def test_review(self):
        r=m.inspect(sample(),STAMP)
        self.assertEqual(r["decision"],"REVIEW_WITH_HOLD")
        self.assertEqual(len(r["candidateFields"]),8)
        self.assertEqual({x["source"] for x in r["candidateFields"]},{m.DETAIL})
        self.assertEqual(r["acceptedFields"],0)
        self.assertEqual(r["ticketSessionIdsVerified"],0)
        self.assertFalse(r["crossSourceIdentityVerified"])
    def test_identity_roles(self):
        for k,v,reason in [
            ("list_detail_href",m.DETAIL+"?x=1","HOLD_LIST_DETAIL_HREF"),
            ("detail_url",m.LIST,"HOLD_DETAIL_URL"),
            ("detail_title","Diana Krall","HOLD_TITLE_PARITY"),
            ("venue","臺北大巨蛋","HOLD_VENUE_OR_ORGANIZER"),
            ("showtimes",[m.SHOWS[0],m.SHOWS[0]],"HOLD_TWO_VENUE_SHOWS"),
            ("sale_start",m.SHOWS[0],"HOLD_SALE_VS_PUBLICATION_ROLE"),
            ("published_date","2026-11-28","HOLD_SALE_VS_PUBLICATION_ROLE"),
            ("advertised_ticket_host","tixcraft.com","HOLD_ADVERTISED_PLATFORM")]:
            with self.subTest(k=k):
                x=sample();x[k]=v
                self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_price_and_ticket_claims(self):
        for v in [0,True,2581]:
            x=sample();x["price_bands"][0]=v
            self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_PRICE_BANDS")
        for k,v in [("ticket_event_id","MNA"),("ticket_session_id",0),
                    ("checkout_href","https://ticket.mna.com.tw/UTK0102_"),
                    ("inventory",0),("cross_source_verified",True),("published_event",True)]:
            with self.subTest(k=k):
                x=sample();x[k]=v
                self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_UNVERIFIED_TICKET_CLAIM")
    def test_invalid(self):
        self.assertEqual(m.inspect(None,STAMP)["decision"],"HOLD_SOURCE")
        self.assertEqual(m.inspect(sample(),"2026-11-02T10:57:00")["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":unittest.main()

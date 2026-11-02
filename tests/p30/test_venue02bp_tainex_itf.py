"""P30-VENUE-02BP generic title and cross-source role refusal; offline."""
import unittest
from scripts import p30_venue02bp_tainex_itf as m
STAMP="2026-11-02T07:53:00+08:00"
def sample():
    return dict(list_url=m.LIST,list_detail_href=m.DETAIL,detail_url=m.DETAIL,
                ticket_detail_url=m.TICKET_DETAIL,list_title=m.TITLE,detail_title=m.TITLE,
                ticket_detail_title=m.TICKET_TITLE,period_start=m.PERIOD[0],
                period_end=m.PERIOD[1],venue_hall="南港展覽館1館",
                floors=list(m.FLOORS),organizer=m.ORGANIZER,organizer_site=m.ORGANIZER_SITE)
class TaiNEXITF(unittest.TestCase):
    def test_review_no_cross_source_merge(self):
        r=m.inspect(sample(),STAMP)
        self.assertEqual(r["decision"],"REVIEW_WITH_HOLD")
        self.assertEqual(len(r["candidateFields"]),6)
        self.assertEqual({x["source"] for x in r["candidateFields"]},{m.DETAIL})
        self.assertFalse(r["crossSourceIdentityVerified"])
        self.assertEqual(r["acceptedFields"],0)
        self.assertTrue(all(z["observed_at"]=="2026-11-02T08:58:00+08:00" for z in r["candidateFields"] if z["source"]==m.ORGANIZER_VISIT))
        self.assertEqual(r["ticketSessionIdsVerified"],0)
        self.assertFalse(r["published"])
    def test_identity_and_role_guards(self):
        for key,value,reason in [
            ("list_detail_href",m.DETAIL+"?other=1","HOLD_LIST_DETAIL_EDGE"),
            ("detail_url","https://[bad/","HOLD_DETAIL_URL"),
            ("ticket_detail_url","https://www.famiticket.com.tw/Home","HOLD_TICKET_SOURCE_URL"),
            ("detail_title",m.TICKET_TITLE,"HOLD_VENUE_TITLE_PARITY"),
            ("ticket_detail_title",m.TITLE,"HOLD_CROSS_SOURCE_TITLE_ROLE"),
            ("period_start","2026-11-07","HOLD_PERIOD_ROLE"),
            ("floors",["一樓展場"],"HOLD_VENUE_ROLE"),
            ("organizer","售票平台","HOLD_ORGANIZER_ROLE"),
        ]:
            with self.subTest(key=key):
                x=sample();x[key]=value
                self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_unverified_ticket_claims(self):
        for key,value in [("ticket_event_id","709"),("ticket_session_id","709"),
                          ("ticket_href",m.TICKET_DETAIL),("showtime","2026-11-06T10:00"),
                          ("admission_price",100),("inventory",10),
                          ("cross_source_verified",True),("published_event",True),
                          ("admission_price",0),("inventory",0),("published_event",0),
                          ("admission_price",False),("inventory",False),
                          ("ticket_href",False),("ticket_session_id",False)]:
            with self.subTest(key=key):
                x=sample();x[key]=value
                self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_UNVERIFIED_TICKET_OR_CROSS_SOURCE")
    def test_independent_organizer_roles_review_only(self):
        x=sample()
        x["organizer_visit"]=dict(url=m.ORGANIZER_VISIT,observed_at="2026-11-02T08:58:00+08:00",date_start="2026-11-06",
            date_end="2026-11-09",day1_hours="12:00-18:00",
            later_hours="10:00-18:00",general_admission=200,
            presale=180,early_bird=150,online_ticket_url=None)
        r=m.inspect(x,STAMP)
        self.assertEqual(r["decision"],"REVIEW_WITH_HOLD")
        self.assertEqual(len(r["candidateFields"]),11)
        self.assertEqual(len([z for z in r["candidateFields"] if z["source"]==m.ORGANIZER_VISIT]),5)
        self.assertEqual(r["acceptedFields"],0)
        self.assertFalse(r["crossSourceIdentityVerified"])
        for key,value,reason in [
            ("url","https://www.taiwanitf.org.tw/Other","HOLD_ORGANIZER_DETAIL_SOURCE"),
            ("general_admission",0,"HOLD_ORGANIZER_DETAIL_ROLES"),
            ("general_admission",True,"HOLD_ORGANIZER_DETAIL_ROLES"),
            ("day1_hours","10:00-18:00","HOLD_ORGANIZER_DETAIL_ROLES"),
            ("observed_at","2026-11-02T08:58:00","HOLD_ORGANIZER_OBSERVATION"),
            ("online_ticket_url","https://checkout.example/","HOLD_ORGANIZER_UNVERIFIED_TICKET_URL"),
        ]:
            with self.subTest(key=key,value=value):
                y=sample();y["organizer_visit"]=dict(x["organizer_visit"])
                y["organizer_visit"][key]=value
                z=m.inspect(y,STAMP)
                self.assertEqual(z["decision"],reason)
                self.assertEqual(z["candidateFields"],[])
    def test_bad_timestamp(self):
        self.assertEqual(m.inspect(None,STAMP)["decision"],"HOLD_SOURCE")
        self.assertEqual(m.inspect(sample(),"2026-11-02T07:53:00")["decision"],"HOLD_OBSERVATION")
if __name__=="__main__": unittest.main()

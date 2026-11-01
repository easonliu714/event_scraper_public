"""P30-VENUE-02BH Zepp two distinct rids vs KKTIX bundle role."""
import importlib.util
import pathlib
import unittest

p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02bh_zepp_two_shows_bundle.py"
s=importlib.util.spec_from_file_location("gate",p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture():
    return dict(venue_list_url=m.LIST,detail_urls=(m.D1,m.D2),
        detail_titles=(m.TITLE,m.TITLE),venue_shows=m.SHOWS,venue_opens=m.OPENS,
        venue_ticket_href=m.TICKET,ticket_event_url=m.TICKET,
        ticket_event_title=m.TITLE,ticket_event_id="takasetoya202611",
        ticket_event_dates=[
            {"role":"BUNDLE","start":m.SHOWS[0],"end":m.SHOWS[1],"label":"兩日通票"},
            {"role":"SHOW","start":m.SHOWS[0],"end":None,"label":"11/07場"},
            {"role":"SHOW","start":m.SHOWS[1],"end":None,"label":"11/08場"}],
        single_day_vvip_price=5880,two_day_vvip_price=10800,
        bundle_is_single_day_price=False,sale_is_show=False,
        general_sale_start="2026-09-23T20:00",ticket_session_ids=None,
        inventory=None,checkout=None,published_event=None)

class Gate(unittest.TestCase):
    def check(self,k=None,v=None):
        x=fixture()
        if k is not None:x[k]=v
        return m.inspect(x,"2026-11-01")
    def test_review_source_provenance(self):
        y=self.check()
        self.assertEqual(y["decision"],"REVIEW_ZEPP_TWO_SHOWS_KKTIX_BUNDLE_HOLD_SESSIONS")
        self.assertEqual(len(y["candidateFields"]),6)
        self.assertEqual({z["source"] for z in y["candidateFields"]},{"ZEPP_NEW_TAIPEI_OFFICIAL","KKTIX_01"})
        self.assertTrue(all(z["decision"]=="REVIEW" and z["observed_at"]=="2026-11-01" for z in y["candidateFields"]))
        self.assertEqual(y["acceptedFields"],0)
        self.assertEqual(y["ticketSessionIdsVerified"],0)
        self.assertFalse(y["published"])
    def test_exact_identity(self):
        for k,v,d in [
            ("venue_list_url",m.LIST+"?other=1","HOLD_VENUE_LIST"),
            ("detail_urls",(m.D1,m.D1),"HOLD_TWO_DISTINCT_RIDS"),
            ("detail_urls",(m.D2,m.D1),"HOLD_TWO_DISTINCT_RIDS"),
            ("detail_titles",(m.TITLE,"different"),"HOLD_TITLE_PARITY"),
            ("venue_ticket_href",m.TICKET+"#ticket","HOLD_DIRECT_TICKET_EVENT_LINK"),
            ("ticket_event_url","https://evil.test/events/takasetoya202611","HOLD_DIRECT_TICKET_EVENT_LINK"),
            ("ticket_event_id","guessed","HOLD_TICKET_EVENT_ID_TITLE")]:
            with self.subTest(k=k):self.assertEqual(self.check(k,v)["decision"],d)
    def test_two_shows_and_bundle(self):
        for k,v,d in [
            ("venue_shows",(m.SHOWS[1],m.SHOWS[0]),"HOLD_TWO_SHOW_OPEN_ROLES"),
            ("venue_opens",m.SHOWS,"HOLD_TWO_SHOW_OPEN_ROLES"),
            ("ticket_event_dates",fixture()["ticket_event_dates"][1:],"HOLD_BUNDLE_NOT_THIRD_SHOW"),
            ("single_day_vvip_price",10800,"HOLD_PRICE_CATEGORY_SCOPE"),
            ("bundle_is_single_day_price",True,"HOLD_BUNDLE_SALE_ROLES"),
            ("sale_is_show",True,"HOLD_BUNDLE_SALE_ROLES")]:
            with self.subTest(k=k):self.assertEqual(self.check(k,v)["decision"],d)
        x=fixture();x["ticket_event_dates"][0]["role"]="SHOW"
        self.assertEqual(m.inspect(x,"2026-11-01")["decision"],"HOLD_BUNDLE_NOT_THIRD_SHOW")
    def test_prohibited_and_missing(self):
        self.assertEqual(m.inspect(fixture(),"bad")["decision"],"HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None,"2026-11-01")["decision"],"HOLD_VENUE_LIST")
        for k,v in [("ticket_session_ids",["guess"]),("inventory",1),("checkout",m.TICKET),("published_event",True)]:
            with self.subTest(k=k):self.assertEqual(self.check(k,v)["decision"],"HOLD_UNVERIFIED_TICKET_SESSION")

if __name__=="__main__":unittest.main()

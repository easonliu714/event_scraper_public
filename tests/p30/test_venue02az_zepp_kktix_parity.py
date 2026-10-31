"""P30-VENUE-02AZ Zepp official rid and KKTIX direct event parity."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02az_zepp_kktix_parity.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"venue_list_url":m.VENUE_HOME,"venue_detail_urls":m.VENUE_URLS,"venue_rids":m.RID,
      "dates":m.SHOW_DATES,"open_times":m.OPEN,"start_times":m.START,
      "title":'TAKASE TOYA 5th Album “♾️” Release Live in Taipei',"venue":"Zepp New Taipei",
      "ticket_edge":m.KKTIX,"kktix_title":'TAKASE TOYA 5th Album “∞” Release Live in Taipei',
      "kktix_roles":("TWO_DAY_PASS","NOV07_SINGLE_DAY","NOV08_SINGLE_DAY"),
      "single_day_price_band":(900,5880),"two_day_pass_price_band":(2600,10800),
      "ticket_session_id":None,"inventory":None,"ticket_event_id":None,"confirmed_ticket_session_price":None,"published_event":None}
class Gate(unittest.TestCase):
    def check(self,k=None,v=None):
        x=fixture()
        if k is not None:x[k]=v
        return m.inspect(x,"2026-11-01")
    def reject(self,d,k,v):
        z=self.check(k,v);self.assertEqual(z["decision"],d);self.assertEqual(z["acceptedFields"],0);self.assertFalse(z["published"])
    def test_exact(self):
        z=self.check();self.assertEqual(z["decision"],"HOLD_CROSS_SOURCE_NO_TICKET_SESSION_ID");self.assertEqual(len(z["provenance"]),3)
    def test_observation(self):self.assertEqual(m.inspect(fixture(),"bad")["decision"],"HOLD_OBSERVATION")
    def test_list(self):self.reject("HOLD_VENUE_LIST_DETAIL_EDGE","venue_list_url","https://example.com")
    def test_detail(self):self.reject("HOLD_VENUE_LIST_DETAIL_EDGE","venue_detail_urls",(m.VENUE_URLS[0],))
    def test_rid(self):self.reject("HOLD_VENUE_PERFORMANCE_IDENTITY","venue_rids",("160668","160668"))
    def test_date(self):self.reject("HOLD_VENUE_PERFORMANCE_IDENTITY","dates",("2026-11-07","2026-11-07"))
    def test_open(self):self.reject("HOLD_VENUE_PERFORMANCE_IDENTITY","open_times",("18:00","16:00"))
    def test_start(self):self.reject("HOLD_VENUE_PERFORMANCE_IDENTITY","start_times",("17:00","17:00"))
    def test_title(self):self.reject("HOLD_EXACT_VENUE_TITLE","title","other")
    def test_venue(self):self.reject("HOLD_EXACT_VENUE_TITLE","venue","Tokyo")
    def test_link(self):self.reject("HOLD_KKTIX_DIRECT_EDGE","ticket_edge","https://kktix.com")
    def test_link_title(self):self.reject("HOLD_KKTIX_DIRECT_EDGE","kktix_title","other")
    def test_bundle(self):self.reject("HOLD_BUNDLE_NOT_THIRD_SHOW","kktix_roles",("THREE_SHOWS",))
    def test_single_price(self):self.reject("HOLD_DISTINCT_PRICE_ROLES","single_day_price_band",(2600,10800))
    def test_pass_price(self):self.reject("HOLD_DISTINCT_PRICE_ROLES","two_day_pass_price_band",(900,5880))
    def test_session(self):self.reject("HOLD_UNVERIFIED_TICKET_ID","ticket_session_id","fake")
    def test_inventory(self):self.reject("HOLD_UNVERIFIED_TICKET_ID","inventory",10)
    def test_ticket_id(self):self.reject("HOLD_UNVERIFIED_TICKET_ID","ticket_event_id","160668")
    def test_price(self):self.reject("HOLD_UNVERIFIED_TICKET_ID","confirmed_ticket_session_price",1480)
    def test_publish(self):self.reject("HOLD_UNVERIFIED_TICKET_ID","published_event",True)
if __name__=="__main__":unittest.main()

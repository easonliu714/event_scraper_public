"""P30-L9-CM KKTIX public event versus forbidden purchase endpoints."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9cm_kktix_three_edges.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"source_url":m.LIST_URL,"event_title":'TAKASE TOYA 5th Album “∞” Release Live in Taipei',"venue":"Zepp New Taipei",
      "registration_urls":m.REG_URLS,"registration_roles":m.ROLES,"date_roles":m.DATES,"start_times":m.TIMES,
      "registration_http_status":(403,403,403),"registration_decision":"HOLD_FORBIDDEN_NO_BYPASS",
      "ticket_session_id":None,"inventory":None,"available_for_purchase":None,"verified_ticket_session_price":None,"canonical_published_event_id":None}
class Gate(unittest.TestCase):
    def check(self,k=None,v=None):
        x=fixture()
        if k is not None:x[k]=v
        return m.inspect(x,"2026-11-01")
    def reject(self,d,k,v):
        z=self.check(k,v);self.assertEqual(z["decision"],d);self.assertEqual(z["acceptedFields"],0);self.assertFalse(z["published"])
    def test_exact(self):
        z=self.check();self.assertEqual(z["decision"],"HOLD_REGISTRATION_403_NOT_SESSION_ID");self.assertEqual(len(z["provenance"]),4)
    def test_bad_date(self):self.assertEqual(m.inspect(fixture(),"invalid")["decision"],"HOLD_OBSERVATION")
    def test_source(self):self.reject("HOLD_KKTIX_SOURCE","source_url","https://fake.kktix.cc/events/takasetoya202611")
    def test_title(self):self.reject("HOLD_TITLE_VENUE_IDENTITY","event_title","different")
    def test_venue(self):self.reject("HOLD_TITLE_VENUE_IDENTITY","venue","Tokyo")
    def test_registration_count(self):self.reject("HOLD_THREE_EXACT_EDGES","registration_urls",m.REG_URLS[:2])
    def test_registration_host(self):self.reject("HOLD_THREE_EXACT_EDGES","registration_urls",("https://evil.example",)+m.REG_URLS[1:])
    def test_registration_roles(self):self.reject("HOLD_THREE_EXACT_EDGES","registration_roles",("NOV07_SINGLE_DAY",)+m.ROLES[1:])
    def test_bundle(self):self.reject("HOLD_DAY_BUNDLE_ROLE","date_roles",("2026-11-07",)+m.DATES[1:])
    def test_time(self):self.reject("HOLD_DAY_BUNDLE_ROLE","start_times",("17:00",)+m.TIMES[1:])
    def test_status(self):self.reject("HOLD_REGISTRATION_ACCESS","registration_http_status",(200,403,403))
    def test_bypass(self):self.reject("HOLD_REGISTRATION_ACCESS","registration_decision","TRY_LOGIN")
    def test_session(self):self.reject("HOLD_UNVERIFIED_PROMOTION","ticket_session_id","fake")
    def test_inventory(self):self.reject("HOLD_UNVERIFIED_PROMOTION","inventory",100)
    def test_sale(self):self.reject("HOLD_UNVERIFIED_PROMOTION","available_for_purchase",True)
    def test_price(self):self.reject("HOLD_UNVERIFIED_PROMOTION","verified_ticket_session_price",1480)
    def test_publish(self):self.reject("HOLD_UNVERIFIED_PROMOTION","canonical_published_event_id","123")
if __name__=="__main__":unittest.main()

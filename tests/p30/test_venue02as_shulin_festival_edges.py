import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02as_shulin_festival_edges.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
 return {"url":m.VENUE_URL,"rows":{k:{"kind":v[0],"ticket_url":v[1],"claimed_platform":v[2],"descriptive_times":list(v[3]),"ticket_session_id":None,"inventory":None,"canonical_ticket_event_id":None} for k,v in m.ROWS.items()}}
class TestGate(unittest.TestCase):
 def check(self,mut=None):
  v=fixture()
  if mut:mut(v)
  return m.inspect(v,"2026-10-31")
 def reject(self,reason,mut):
  x=self.check(mut);self.assertEqual(x["decision"],reason);self.assertEqual(x["acceptedFields"],0)
 def test_review(self):
  x=self.check();self.assertEqual(x["decision"],"HOLD_MIXED_EVENT_TYPES_AND_SHORTLINK_IDENTITY");self.assertEqual(len(x["provenance"]),5)
 def test_bad_date(self):self.assertEqual(m.inspect(fixture(),"2026-02-30")["decision"],"HOLD_OBSERVED_AT")
 def test_missing_market(self):self.reject("HOLD_FESTIVAL_IS_NOT_SINGLE_EVENT",lambda v:v["rows"].pop("MARKET"))
 def test_shortlink_host(self):self.reject("HOLD_DIRECT_LINK_IDENTITY",lambda v:v["rows"]["BEL"].update(ticket_url="https://evil.test/p/P5fece325"))
 def test_shortlink_id(self):self.reject("HOLD_DIRECT_LINK_IDENTITY",lambda v:v["rows"]["BODY"].update(ticket_url="https://s.opentix.life/p/other"))
 def test_accupass_event(self):self.reject("HOLD_DIRECT_LINK_IDENTITY",lambda v:v["rows"]["FAMILY"].update(ticket_url="https://www.accupass.com/event/other"))
 def test_market_ticket(self):self.reject("HOLD_DIRECT_LINK_IDENTITY",lambda v:v["rows"]["MARKET"].update(ticket_url="https://www.accupass.com/event/1"))
 def test_kind(self):self.reject("HOLD_CATEGORY_SCOPE",lambda v:v["rows"]["DANCE"].update(kind="PERFORMANCE"))
 def test_time(self):self.reject("HOLD_LOCAL_TIME_ROLE",lambda v:v["rows"]["BODY"]["descriptive_times"].pop())
 def test_claim(self):self.reject("HOLD_PLATFORM_ROLE",lambda v:v["rows"]["FAMILY"].update(claimed_platform="OPENTIX_CLAIMED"))
 def test_session(self):self.reject("HOLD_NO_SESSION_INVENTORY",lambda v:v["rows"]["FAMILY"].update(ticket_session_id="invented"))
 def test_inventory(self):self.reject("HOLD_NO_SESSION_INVENTORY",lambda v:v["rows"]["MARKET"].update(inventory=100))
 def test_unresolved_shortlink(self):self.reject("HOLD_OPENTIX_SHORTLINK_UNRESOLVED",lambda v:v["rows"]["BEL"].update(canonical_ticket_event_id="invented"))
if __name__=="__main__":unittest.main()

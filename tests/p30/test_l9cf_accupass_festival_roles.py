import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9cf_accupass_festival_roles.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
 venue={"url":m.VENUE_URL,"links":{k:"https://www.accupass.com/event/"+v[0] for k,v in m.EVENTS.items()}}
 rec={}
 for k,(eid,title,shows,fee) in m.EVENTS.items():
  rec[k]={"url":"https://www.accupass.com/event/"+eid,"title":title,"venue":"樹林藝文中心3F排練室","listed_fee":fee,"registration_unit":"PARENT_CHILD_PAIR" if k=="PARENT_CHILD" else "PER_WORKSHOP","ticket_session_ids":None,"inventory":None}
  if k=="PARENT_CHILD":rec[k]["description_sessions"]=[list(x) for x in shows]
  else:rec[k].update(description_session_count=16,range=["2026-11-16","2026-11-27"])
 return venue,rec
class TestGate(unittest.TestCase):
 def check(self,mut=None):
  v,r=fixture()
  if mut:mut(v,r)
  return m.inspect(v,r,"2026-10-31")
 def reject(self,reason,mut):
  x=self.check(mut);self.assertEqual(x["decision"],reason);self.assertEqual(x["acceptedFields"],0)
 def test_source_review(self):
  x=self.check();self.assertEqual(x["decision"],"HOLD_EVENT_ID_NOT_TICKET_SESSION_ID_AND_FEE_UNIT");self.assertEqual(len(x["provenance"]),2)
 def test_bad_date(self):self.assertEqual(m.inspect(*fixture(),"2026-02-30")["decision"],"HOLD_OBSERVED_AT")
 def test_cross_host(self):self.reject("HOLD_DIRECT_SOURCE_LINK",lambda v,r:v["links"].update(PARENT_CHILD="https://evil.test/event/2609151410103172453460"))
 def test_query(self):self.reject("HOLD_DIRECT_SOURCE_LINK",lambda v,r:r["PARENT_CHILD"].update(url=r["PARENT_CHILD"]["url"]+"?ticket=1"))
 def test_title(self):self.reject("HOLD_EVENT_TITLE",lambda v,r:r["PARENT_CHILD"].update(title="other"))
 def test_venue(self):self.reject("HOLD_VENUE",lambda v,r:r["PARENT_CHILD"].update(venue="other"))
 def test_session_date(self):self.reject("HOLD_TWO_DESCRIPTION_SESSIONS",lambda v,r:r["PARENT_CHILD"]["description_sessions"][0].__setitem__(0,"2026-11-20"))
 def test_16_not_event(self):self.reject("HOLD_16_WORKSHOP_UMBRELLA",lambda v,r:r["DANCE_WORKSHOPS"].update(description_session_count=2))
 def test_price_unit(self):self.reject("HOLD_FEE_UNIT",lambda v,r:r["PARENT_CHILD"].update(registration_unit="PER_PERSON"))
 def test_ticket_id(self):self.reject("HOLD_NO_TICKET_SESSION_ID",lambda v,r:r["PARENT_CHILD"].update(ticket_session_ids=["invented"]))
 def test_inventory(self):self.reject("HOLD_NO_TICKET_SESSION_ID",lambda v,r:r["DANCE_WORKSHOPS"].update(inventory=20))
 def test_collapsed_event(self):self.reject("HOLD_DISTINCT_EVENT_SCOPE",lambda v,r:r.pop("DANCE_WORKSHOPS"))
if __name__=="__main__":unittest.main()

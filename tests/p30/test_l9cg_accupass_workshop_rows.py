import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9cg_accupass_workshop_rows.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
 return {"url":m.SOURCE,"event_id":"2609041147021848655729","fee_unit":"PER_WORKSHOP","listed_fee":100,"ticket_session_ids":None,"inventory":None,"description_rows":[dict(zip(("title","date","start","end"),r),role="DESCRIPTION_WORKSHOP_TIME") for r in m.ROWS]}
class TestGate(unittest.TestCase):
 def check(self,mut=None):
  x=fixture()
  if mut:mut(x)
  return m.inspect(x,"2026-10-31")
 def reject(self,reason,mut):
  x=self.check(mut);self.assertEqual(x["decision"],reason);self.assertEqual(x["acceptedFields"],0)
 def test_source_16_description_rows(self):
  x=self.check();self.assertEqual(x["decision"],"HOLD_16_DESCRIPTION_ROWS_NOT_16_TICKET_SESSIONS");self.assertEqual(len(x["provenance"]),16)
 def test_bad_observation_date(self):self.assertEqual(m.inspect(fixture(),"2026-02-30")["decision"],"HOLD_OBSERVED_AT")
 def test_cross_host(self):self.reject("HOLD_SAME_EVENT_ID",lambda x:x.update(url="https://evil.test/event/2609041147021848655729"))
 def test_query(self):self.reject("HOLD_SAME_EVENT_ID",lambda x:x.update(url=m.SOURCE+"?q=1"))
 def test_event_id(self):self.reject("HOLD_SAME_EVENT_ID",lambda x:x.update(event_id="2609151410103172453460"))
 def test_ticket_session_invention(self):self.reject("HOLD_NO_PUBLIC_TICKET_SESSION_IDS",lambda x:x.update(ticket_session_ids=["invented"]))
 def test_inventory_invention(self):self.reject("HOLD_NO_PUBLIC_TICKET_SESSION_IDS",lambda x:x.update(inventory=20))
 def test_fee_unit(self):self.reject("HOLD_FEE_UNIT",lambda x:x.update(fee_unit="PER_PARENT_CHILD_PAIR"))
 def test_missing_row(self):self.reject("HOLD_DESCRIPTION_ROW_COUNT",lambda x:x["description_rows"].pop())
 def test_duplicate(self):self.reject("HOLD_DUPLICATE_DESCRIPTION_ROW",lambda x:x["description_rows"].__setitem__(1,x["description_rows"][0].copy()))
 def test_wrong_local_date(self):self.reject("HOLD_TITLE_DATE_LOCAL_BINDING",lambda x:x["description_rows"][0].update(date="2026-11-17"))
 def test_swapped_title(self):self.reject("HOLD_TITLE_DATE_LOCAL_BINDING",lambda x:x["description_rows"][0].update(title=x["description_rows"][1]["title"]))
 def test_undated_role(self):self.reject("HOLD_TITLE_DATE_LOCAL_BINDING",lambda x:x["description_rows"][0].update(role="TICKET_SESSION"))
if __name__=="__main__":unittest.main()

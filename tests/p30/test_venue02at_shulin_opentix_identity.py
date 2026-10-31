import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02at_shulin_opentix_identity.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
 v={"url":m.VENUE,"shows":{k:{"shortlink":r["shortlink"],"title":r["title"],"venue":"樹林藝文中心演藝廳","descriptive_shows":[list(x) for x in r["shows"]]} for k,r in m.EVENTS.items()}}
 o={k:{"url":"https://www.opentix.life/event/"+r["event_id"],"event_id":r["event_id"],"title":r["title"],"venue":"樹林藝文中心演藝廳","description_shows":[list(x) for x in r["shows"]],"face_price":r["face_price"],"price_role":"ORIGINAL_FACE_PRICE","ticket_session_ids":None,"inventory":None,"shortlink_redirect_verified":False} for k,r in m.EVENTS.items()}
 p={"url":m.PACKAGE,"role":"SALE_PACKAGE","sale_window":["2026-09-28","2026-11-21"],"bundle_original_pair":["BEL","BODY"],"bundle_fee":1000,"ticket_session_ids":None}
 return v,o,p
class TestGate(unittest.TestCase):
 def check(self,mut=None):
  v,o,p=fixture()
  if mut:mut(v,o,p)
  return m.inspect(v,o,p,"2026-10-31")
 def reject(self,reason,mut):
  x=self.check(mut);self.assertEqual(x["decision"],reason);self.assertEqual(x["acceptedFields"],0)
 def test_independent_pages_review(self):
  x=self.check();self.assertEqual(x["decision"],"HOLD_SHORTLINK_MAPPING_AND_TICKET_SESSION_IDS");self.assertEqual(len(x["provenance"]),3)
 def test_bad_date(self):self.assertEqual(m.inspect(*fixture(),"2026-02-30")["decision"],"HOLD_OBSERVED_AT")
 def test_venue_host(self):self.reject("HOLD_VENUE_SOURCE",lambda v,o,p:v.update(url="https://evil.test/"))
 def test_missing_show(self):self.reject("HOLD_VENUE_SOURCE",lambda v,o,p:v["shows"].pop("BODY"))
 def test_shortlink_unverified(self):self.reject("HOLD_VENUE_SHORTLINK",lambda v,o,p:v["shows"]["BEL"].update(shortlink="https://evil.test/p/P5fece325"))
 def test_event_host(self):self.reject("HOLD_OPENTIX_CANONICAL_ID",lambda v,o,p:o["BEL"].update(url="https://evil.test/event/2099700588990402561"))
 def test_swapped_id(self):self.reject("HOLD_OPENTIX_CANONICAL_ID",lambda v,o,p:o["BODY"].update(event_id="2099700588990402561"))
 def test_title(self):self.reject("HOLD_INDEPENDENT_TITLE_PARITY",lambda v,o,p:o["BODY"].update(title="another"))
 def test_venue(self):self.reject("HOLD_VENUE_PARITY",lambda v,o,p:o["BEL"].update(venue="other"))
 def test_showtime(self):self.reject("HOLD_DESCRIPTIVE_TIME_PARITY",lambda v,o,p:o["BODY"]["description_shows"][0].__setitem__(1,"14:00"))
 def test_price_role(self):self.reject("HOLD_PRICE_ROLE",lambda v,o,p:o["BEL"].update(price_role="PER_SESSION_TICKET_PRICE"))
 def test_session_id(self):self.reject("HOLD_TICKET_SESSION_UNVERIFIED",lambda v,o,p:o["BEL"].update(ticket_session_ids=["invented"]))
 def test_claim_redirect(self):self.reject("HOLD_SHORTLINK_REDIRECT_UNVERIFIED",lambda v,o,p:o["BODY"].update(shortlink_redirect_verified=True))
 def test_package_event_conflation(self):self.reject("HOLD_PACKAGE_ID",lambda v,o,p:p.update(url="https://www.opentix.life/event/2102208181225205761"))
 def test_package_date_role(self):self.reject("HOLD_PACKAGE_SALE_VS_SHOWTIME",lambda v,o,p:p.update(role="SHOWTIME"))
 def test_package_ticket_id(self):self.reject("HOLD_PACKAGE_NOT_TICKET_SESSION",lambda v,o,p:p.update(ticket_session_ids=["invented"]))
if __name__=="__main__":unittest.main()

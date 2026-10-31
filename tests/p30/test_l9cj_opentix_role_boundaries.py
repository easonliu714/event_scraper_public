"""Offline source-derived negative tests; no network requests."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_l9cj_opentix_role_boundaries.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"url":m.EVENT_URL,"event_id":m.EVENT_ID,"venue":m.VENUE,"venue_count":9,"venue_count_role":"CHOOSER_NOT_SESSIONS",
    "sale_windows":list(m.SALE),"sale_role":"DISCOUNT_ELIGIBILITY_NOT_SHOW",
    "shows":list(m.SHOWS),"show_role":"VENUE_DESCRIPTIVE_NOT_TICKET_SESSION",
    "admission_minutes_before":30,"admission_role":"DOOR_OPEN_RELATIVE_NOT_SHOWTIME",
    "duration_minutes":95,"stage_minutes":80,"intermission_minutes":15,"duration_role":"DURATION_NOT_SESSION",
    "refund_days_before":10,"refund_excludes_show_date":True,"refund_fee_percent":10,"refund_role":"RELATIVE_POLICY_NOT_DEADLINE",
    "ticket_session_ids":None,"session_price":None,"inventory":None,"absolute_refund_deadline":None}
class Gate(unittest.TestCase):
    def check(self,field=None,value=None):
        x=fixture()
        if field is not None:x[field]=value
        return m.inspect(x,"2026-11-01")
    def reject(self,decision,field,value):
        r=self.check(field,value);self.assertEqual(r["decision"],decision);self.assertEqual(r["acceptedFields"],0);self.assertFalse(r["published"])
    def test_source_roles(self):
        r=self.check();self.assertEqual(r["decision"],"HOLD_ROLE_EVIDENCE_NO_TICKET_SESSION_ID");self.assertEqual(len(r["provenance"]),3)
    def test_invalid_observation(self):self.assertEqual(m.inspect(fixture(),"2026-02-30")["decision"],"HOLD_OBSERVATION")
    def test_event_path(self):self.reject("HOLD_EVENT_ID","url",m.EVENT_URL+"?ref=1")
    def test_event_id(self):self.reject("HOLD_EVENT_ID","event_id","other")
    def test_venue(self):self.reject("HOLD_VENUE_ROLE","venue","wrong")
    def test_venue_count(self):self.reject("HOLD_VENUE_ROLE","venue_count",3)
    def test_venue_is_session(self):self.reject("HOLD_VENUE_ROLE","venue_count_role","SESSIONS")
    def test_sale_is_show(self):self.reject("HOLD_SALE_WINDOW","sale_role","SHOWTIME")
    def test_sale_date(self):self.reject("HOLD_SALE_WINDOW","sale_windows",[])
    def test_show_as_ticket_session(self):self.reject("HOLD_SHOW_ROLE","show_role","TICKET_SESSION")
    def test_door_open_as_start(self):self.reject("HOLD_ADMISSION_ROLE","admission_role","SHOWTIME")
    def test_duration_as_show(self):self.reject("HOLD_DURATION_ROLE","duration_role","SHOWTIME")
    def test_refund_absolute(self):self.reject("HOLD_REFUND_POLICY","refund_role","ABSOLUTE_DEADLINE")
    def test_refund_fee(self):self.reject("HOLD_REFUND_POLICY","refund_fee_percent",0)
    def test_fake_session(self):self.reject("HOLD_UNVERIFIED_TICKET_FIELD","ticket_session_ids",["invented"])
    def test_fake_inventory(self):self.reject("HOLD_UNVERIFIED_TICKET_FIELD","inventory",9)
    def test_fake_session_price(self):self.reject("HOLD_UNVERIFIED_TICKET_FIELD","session_price",1000)
    def test_fake_refund_date(self):self.reject("HOLD_UNVERIFIED_TICKET_FIELD","absolute_refund_deadline","2026-10-28")
if __name__=="__main__":unittest.main()

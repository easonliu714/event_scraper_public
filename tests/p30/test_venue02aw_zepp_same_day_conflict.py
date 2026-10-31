"""Offline regression of exact official list/detail rids and status scoping."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02aw_zepp_same_day_conflict.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"index_url":m.INDEX,"rows":[
      {"rid":"160673","url":m.CANCEL_URL,"title":'AKASAKI 1st WORLD TOUR "ONIGIRI"',"date":m.DATE,"start":"18:00","door":"17:00","status":"CANCELLED_SOURCE_LABEL","ticket_event_id":None,"ticket_url":None},
      {"rid":"169301","url":m.ACTIVE_URL,"title":"ALL PIECES, ONE PERSES","date":m.DATE,"start":"18:00","door":None,"status":"NOT_MARKED_CANCELLED","declared_platform":"KKTIX","ticket_text":"Link in Bio","ticket_event_id":None,"ticket_url":None}],
      "auto_resolve_schedule_conflict":False,"assume_other_event_cancelled":False}
class Gate(unittest.TestCase):
    def check(self,change=None):
        x=fixture()
        if change:change(x)
        return m.inspect(x,"2026-11-01")
    def reject(self,decision,change):
        r=self.check(change);self.assertEqual(r["decision"],decision);self.assertEqual(r["acceptedFields"],0);self.assertFalse(r["published"])
    def test_same_day_two_rids(self):
        r=self.check();self.assertEqual(r["decision"],"HOLD_TWO_DISTINCT_RIDS_SAME_DAY_VENUE_CONFLICT");self.assertEqual(len(r["provenance"]),2)
    def test_invalid_observation(self):self.assertEqual(m.inspect(fixture(),"bad")["decision"],"HOLD_OBSERVATION")
    def test_index(self):self.reject("HOLD_LIST_URL",lambda x:x.update(index_url="https://evil.example"))
    def test_row_count(self):self.reject("HOLD_LIST_ROW_COUNT",lambda x:x["rows"].pop())
    def test_cancel_rid(self):self.reject("HOLD_CANCEL_IDENTITY",lambda x:x["rows"][0].update(rid="169301"))
    def test_cancel_url(self):self.reject("HOLD_CANCEL_IDENTITY",lambda x:x["rows"][0].update(url=m.ACTIVE_URL))
    def test_cancel_title(self):self.reject("HOLD_CANCEL_IDENTITY",lambda x:x["rows"][0].update(title="other"))
    def test_other_rid(self):self.reject("HOLD_OTHER_IDENTITY",lambda x:x["rows"][1].update(rid="160673"))
    def test_other_title(self):self.reject("HOLD_OTHER_IDENTITY",lambda x:x["rows"][1].update(title="other"))
    def test_start(self):self.reject("HOLD_SAME_DAY_START",lambda x:x["rows"][1].update(start="19:00"))
    def test_cancel_status(self):self.reject("HOLD_STATUS_SCOPE",lambda x:x["rows"][0].update(status="ACTIVE"))
    def test_other_cancelled(self):self.reject("HOLD_STATUS_SCOPE",lambda x:x["rows"][1].update(status="CANCELLED_SOURCE_LABEL"))
    def test_fake_door(self):self.reject("HOLD_DOOR_ROLE",lambda x:x["rows"][1].update(door="17:00"))
    def test_declared_platform(self):self.reject("HOLD_PLATFORM_DECLARATION",lambda x:x["rows"][1].update(declared_platform="OPENTIX"))
    def test_bio_as_url(self):self.reject("HOLD_PLATFORM_DECLARATION",lambda x:x["rows"][1].update(ticket_text="https://kktix.com/fake"))
    def test_fabricated_ticket_id(self):self.reject("HOLD_UNVERIFIED_TICKET_LINK",lambda x:x["rows"][1].update(ticket_event_id="invented"))
    def test_fabricated_ticket_url(self):self.reject("HOLD_UNVERIFIED_TICKET_LINK",lambda x:x["rows"][1].update(ticket_url="https://kktix.com/fake"))
    def test_auto_resolution(self):self.reject("HOLD_SHARED_VENUE_CONFLICT",lambda x:x.update(auto_resolve_schedule_conflict=True))
    def test_cascade_cancellation(self):self.reject("HOLD_SHARED_VENUE_CONFLICT",lambda x:x.update(assume_other_event_cancelled=True))
if __name__=="__main__":unittest.main()

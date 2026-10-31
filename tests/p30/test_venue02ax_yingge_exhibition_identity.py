"""Offline source-derived tests of two independent Yingge official sid detail pages."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02ax_yingge_exhibition_identity.py"
s=importlib.util.spec_from_file_location("gate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"index_url":m.INDEX,"rows":[{"sid":sid,"list_title":title,"detail_url":m.detail_url(sid),
      "detail_title":title,"date_start":start,"date_end":end,"room":room,
      "date_role":"EXHIBITION_DATE_RANGE_NOT_TICKET_SESSION",
      "ticket_platform_id":None,"ticket_event_url":None,"ticket_session_id":None,"price":None,"inventory":None}
      for sid,title,start,end,room in m.RECORDS]}
class Gate(unittest.TestCase):
    def check(self,fn=None):
        x=fixture()
        if fn:fn(x)
        return m.inspect(x,"2026-11-01")
    def reject(self,d,fn):
        r=self.check(fn);self.assertEqual(r["decision"],d);self.assertEqual(r["acceptedFields"],0);self.assertFalse(r["published"])
    def test_two_official_sids(self):
        r=self.check();self.assertEqual(r["decision"],"HOLD_TWO_EXHIBITIONS_SOURCE_BOUND_NOT_TICKET_EVENTS");self.assertEqual(len(r["provenance"]),2)
    def test_invalid_observation(self):self.assertEqual(m.inspect(fixture(),"bad")["decision"],"HOLD_OBSERVATION")
    def test_index(self):self.reject("HOLD_INDEX_URL",lambda x:x.update(index_url="https://evil.example"))
    def test_count(self):self.reject("HOLD_ROW_COUNT",lambda x:x["rows"].pop())
    def test_sid(self):self.reject("HOLD_LIST_DETAIL_IDENTITY",lambda x:x["rows"][0].update(sid=m.RECORDS[1][0]))
    def test_list_title(self):self.reject("HOLD_LIST_DETAIL_IDENTITY",lambda x:x["rows"][0].update(list_title="similar"))
    def test_detail_link(self):self.reject("HOLD_LIST_DETAIL_IDENTITY",lambda x:x["rows"][1].update(detail_url=m.detail_url(m.RECORDS[0][0])))
    def test_detail_title(self):self.reject("HOLD_DETAIL_TITLE_DATE",lambda x:x["rows"][1].update(detail_title="wrong"))
    def test_date_start(self):self.reject("HOLD_DETAIL_TITLE_DATE",lambda x:x["rows"][0].update(date_start="2026-11-20"))
    def test_date_end(self):self.reject("HOLD_DETAIL_TITLE_DATE",lambda x:x["rows"][0].update(date_end="2026-12-20"))
    def test_room(self):self.reject("HOLD_EXHIBITION_ROLE",lambda x:x["rows"][0].update(room="b1陶藝長廊"))
    def test_role(self):self.reject("HOLD_EXHIBITION_ROLE",lambda x:x["rows"][0].update(date_role="PERFORMANCE_SESSION"))
    def test_ticket_id(self):self.reject("HOLD_UNVERIFIED_TICKET_FIELDS",lambda x:x["rows"][1].update(ticket_platform_id="fake"))
    def test_ticket_url(self):self.reject("HOLD_UNVERIFIED_TICKET_FIELDS",lambda x:x["rows"][1].update(ticket_event_url="https://example.com"))
    def test_ticket_session(self):self.reject("HOLD_UNVERIFIED_TICKET_FIELDS",lambda x:x["rows"][1].update(ticket_session_id="invented"))
    def test_inventory(self):self.reject("HOLD_UNVERIFIED_TICKET_FIELDS",lambda x:x["rows"][0].update(inventory=5))
if __name__=="__main__":unittest.main()

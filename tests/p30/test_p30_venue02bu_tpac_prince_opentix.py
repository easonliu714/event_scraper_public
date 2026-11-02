"""P30-VENUE-02BU exact cross-source identity and conflict regression."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02bu_tpac_prince_opentix.py"
s=importlib.util.spec_from_file_location("venue02bu",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
NOW="2026-11-02T09:17:00Z"
def sample():
    return {"list_url":m.LIST,"venue_detail_url":m.DETAIL,"direct_ticket_url":m.TICKET,
            "list_title":m.TITLE,"venue_title":m.TITLE,"ticket_title":m.TITLE,
            "venue_room":"藍盒子","ticket_venue":"臺北表演藝術中心 藍盒子",
            "list_advertised_range":["2026-11-04","2026-11-14"],
            "detail_advertised_range":["2026-11-05","2026-11-15"],
            "ticket_advertised_range":["2026-11-05","2026-11-15"],
            "show_times":list(m.SHOWS),"venue_advertised_price_range":[1200,2200],
            "venue_age_min":6,"ticket_age_min":7,"ticket_notice_city":"嘉義市",
            "ticket_notice_date":"2026-11-01",
            "ticket_reader_heading":"選擇場次","ticket_reader_session_rows_exposed":False}
class Gate(unittest.TestCase):
    def test_twelve_source_bound_receipts_and_one_event_edge(self):
        x=m.inspect(sample(),NOW)
        self.assertEqual(x["decision"],"REVIEW_EXACT_TICKET_EVENT_EDGE_AGE_CONFLICT_SESSION_HOLD")
        self.assertEqual(len(x["candidateFields"]),12)
        self.assertTrue(x["listDetailRangeConflict"])
        self.assertEqual({f["source"] for f in x["candidateFields"]},{m.LIST,m.DETAIL,m.TICKET})
        self.assertEqual({f["decision"] for f in x["candidateFields"]},{"REVIEW"})
        self.assertEqual((x["ticketEventIdsVerified"],x["ticketSessionIdsVerified"],x["acceptedFields"],x["goldenAccepted"],x["published"]),(1,0,0,0,False))
    def test_url_title_identity(self):
        for key,value in (("direct_ticket_url",m.TICKET+"?session=1"),
                          ("direct_ticket_url","https://www.opentix.life.evil.example/event/2072516129034670080"),
                          ("venue_detail_url",m.DETAIL+"#other"),("list_title","小王子"),
                          ("ticket_title","另一個小王子"),("venue_room","大劇院")):
            with self.subTest(key=key):
                a=sample();a[key]=value;self.assertEqual(m.inspect(a,NOW)["candidateFields"],[])
    def test_index_detail_ticket_range_conflict_fail_closed(self):
        for key,value,reason in (
            ("list_advertised_range",["2026-11-05","2026-11-15"],"HOLD_LIST_DATE_RANGE_UNVERIFIED"),
            ("list_advertised_range",None,"HOLD_LIST_DATE_RANGE_UNVERIFIED"),
            ("detail_advertised_range",["2026-11-04","2026-11-14"],"HOLD_DETAIL_TICKET_DATE_RANGE_PARITY"),
            ("ticket_advertised_range",["2026-11-04","2026-11-14"],"HOLD_DETAIL_TICKET_DATE_RANGE_PARITY")):
            with self.subTest(key=key,value=value):
                a=sample();a[key]=value;x=m.inspect(a,NOW)
                self.assertEqual(x["decision"],reason)
                self.assertEqual(x["candidateFields"],[])
                self.assertEqual((x["acceptedFields"],x["published"]),(0,False))
    def test_session_list_and_advertised_price_roles(self):
        for key,value in (("show_times",list(m.SHOWS[:-1])),
                          ("show_times",list(m.SHOWS[:-1])+[m.SHOWS[0]]),
                          ("venue_advertised_price_range",[1000,2200]),
                          ("venue_age_min",7),("ticket_age_min",6),
                          ("ticket_notice_city","臺北市"),("ticket_notice_date","2026-11-05"),
                          ("ticket_reader_heading","購票去"),("ticket_reader_session_rows_exposed",True),
                          ("ticket_reader_session_rows_exposed",None)):
            with self.subTest(key=key):
                a=sample();a[key]=value;self.assertEqual(m.inspect(a,NOW)["candidateFields"],[])
    def test_unverified_ticket_session_and_conflict_override(self):
        for key,value in (("ticket_session_ids",[]),("checkout_url",m.TICKET),
                          ("stock",0),("inventory",False),("formal_age_min",6),
                          ("ticket_prices_verified",False),("golden_accepted",False)):
            a=sample();a[key]=value
            self.assertEqual(m.inspect(a,NOW)["decision"],"HOLD_UNVERIFIED_SESSION_OR_CONFLICT_OVERRIDE")
    def test_observation_timestamp(self):
        for t in ("bad","2026-11-02T17:17:00",None):
            self.assertEqual(m.inspect(sample(),t)["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":unittest.main()

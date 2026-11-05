"""VENUE-02BS strict same-event source and field-role regression."""
import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02bs_tmc_kham_edge.py"
spec=importlib.util.spec_from_file_location("venue02bs",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
NOW="2026-11-02T06:55:00Z"
def sample():
    return dict(list_url=m.LIST,list_detail_href=m.DETAIL,detail_url=m.DETAIL,
                ticket_href=m.TICKET,list_title=m.TITLE,detail_title=m.TITLE,
                list_date="2026-11-07",show="2026-11-07T19:30+08:00",
                venue="臺北流行音樂中心 表演廳",
                prices=[4280,3880,3480,2880,2480,1880],published_at="2026-08-11",
                ticket_session_list_url=m.TICKET_SESSION_LIST,
                ticket_session_list_title="2026 小宇 宋念宇《不，完美的人》演唱會",
                ticket_standard_row={"show":"2026-11-07T19:30+08:00",
                                     "venue":"臺北流行音樂中心 表演廳","label":"",
                                     "displayed_prices":[1880,2480,2880,3480,3880,4280],
                                     "struck_through":True},
                ticket_wheelchair_row={"show":"2026-11-07T19:30+08:00",
                                       "venue":"臺北流行音樂中心 表演廳","label":"輪椅席",
                                       "displayed_prices":[3480,4280],"struck_through":False})
class StrictVenueEvidence(unittest.TestCase):
    def test_review_receipts_not_accepted(self):
        r=m.inspect(sample(),NOW)
        self.assertEqual(r["decision"],"REVIEW_EXACT_LIST_DETAIL_HOLD_TICKET_SESSION")
        self.assertEqual(len(r["candidateFields"]),9)
        self.assertEqual({f["decision"] for f in r["candidateFields"]},{"REVIEW"})
        self.assertEqual(r["acceptedFields"],0)
        self.assertEqual(r["goldenAccepted"],0)
        self.assertFalse(r["published"])
        self.assertEqual(r["releaseState"],"HARD_HOLD_NO_PUBLICATION")
    def test_identity_fail_closed(self):
        for field,value in [("list_url","http://www.tmc.taipei/tw/blog/show"),
                            ("list_detail_href",m.DETAIL+"#other"),
                            ("detail_url",m.DETAIL+"/wrong"),
                            ("ticket_href",m.TICKET.replace("P1DF32E2","OTHER")),
                            ("list_title","unrelated"),("detail_title","similar title")]:
            with self.subTest(field=field):
                x=sample();x[field]=value
                self.assertEqual(m.inspect(x,NOW)["candidateFields"],[])
    def test_role_and_price_fail_closed(self):
        for field,value in [("list_date","2026-08-11"),
                            ("show","2026-08-22T12:00+08:00"),
                            ("venue","other venue"),("prices",[1880]),
                            ("prices",[False,3880,3480,2880,2480,1880]),
                            ("published_at","2026-11-07")]:
            with self.subTest(field=field):
                x=sample();x[field]=value
                self.assertEqual(m.inspect(x,NOW)["candidateFields"],[])
    def test_ticket_selection_row_separation(self):
        for field,value in [
            ("ticket_session_list_url",m.TICKET_SESSION_LIST+"#cart"),
            ("ticket_session_list_title","similar unrelated event"),
            ("ticket_standard_row",{"show":"2026-11-07T19:30+08:00","venue":"臺北流行音樂中心 表演廳","label":"","displayed_prices":[1880,2480,2880,3480,3880,4280],"struck_through":False}),
            ("ticket_wheelchair_row",{"show":"2026-11-07T19:30+08:00","venue":"臺北流行音樂中心 表演廳","label":"輪椅席","displayed_prices":[1880,4280],"struck_through":False}),
        ]:
            with self.subTest(field=field):
                x=sample();x[field]=value
                self.assertEqual(m.inspect(x,NOW)["candidateFields"],[])
        x=sample();x["inventory"]="AVAILABLE"
        self.assertEqual(m.inspect(x,NOW)["decision"],"HOLD_UNVERIFIED_CLAIM")

    def test_no_unverified_session_or_inventory(self):
        for field,value in [("ticket_session_id",0),("ticket_session_id",False),
                            ("checkout_url",m.TICKET),("inventory",0),
                            ("golden_accepted",False)]:
            with self.subTest(field=field):
                x=sample();x[field]=value
                self.assertEqual(m.inspect(x,NOW)["decision"],"HOLD_UNVERIFIED_CLAIM")
    def test_timestamp(self):
        for stamp in [None,"invalid","2026-11-02T13:55:00"]:
            self.assertEqual(m.inspect(sample(),stamp)["decision"],"HOLD_TIME")
if __name__=="__main__":
    unittest.main()

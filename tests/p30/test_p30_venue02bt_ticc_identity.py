"""TICC source ID, generic title, conference setup and multi-room fail-closed tests."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02bt_ticc_identity.py"
spec=importlib.util.spec_from_file_location("venue02bt",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
NOW="2026-11-02T08:05:00Z"
def sample():
    return dict(list_url=m.LIST,generic_detail_url=m.DETAIL_GENERIC,topbs_detail_url=m.DETAIL_TOPBS,
      generic_list_title="寬宏演唱會",generic_detail_title="寬宏演唱會",
      generic_date="2026-11-14",generic_room="大會堂",generic_organizer="寬宏藝術經紀股份有限公司",
      topbs_list_title="TOPBS 2026年會",topbs_detail_title="TOPBS 2026年會",
      topbs_period=["2026-11-14","2026-11-15"],topbs_setup_date="2026-11-13",
      topbs_rooms=["101","102","105","106(會前會議室)"])
class Gate(unittest.TestCase):
    def test_exact_two_detail_receipts(self):
        r=m.inspect(sample(),NOW)
        self.assertEqual(r["decision"],"REVIEW_TWO_VENUE_DETAILS_HOLD_GENERIC_TICKET_IDENTITY")
        self.assertEqual(len(r["candidateFields"]),8)
        self.assertEqual({x["decision"] for x in r["candidateFields"]},{"REVIEW"})
        self.assertEqual({x["source"] for x in r["candidateFields"]},{m.LIST,m.DETAIL_GENERIC,m.DETAIL_TOPBS})
        self.assertEqual((r["acceptedFields"],r["ticketSessionIdsVerified"],r["goldenAccepted"],r["published"]),(0,0,0,False))
    def test_detail_id_not_ticket_id(self):
        for key,val in [("generic_detail_url",m.DETAIL_TOPBS),("topbs_detail_url",m.DETAIL_GENERIC),
                        ("generic_detail_url",m.DETAIL_GENERIC+"#show"),
                        ("generic_detail_url",m.DETAIL_GENERIC.replace("www.ticc.com.tw","www.ticc.com.tw.evil.example")),
                        ("generic_list_title","某位歌手演唱會")]:
            x=sample();x[key]=val
            self.assertEqual(m.inspect(x,NOW)["candidateFields"],[])
    def test_setup_and_multi_room_are_not_show_sessions(self):
        for key,val in [("generic_date","2026-11-13"),("topbs_setup_date","2026-11-14"),
                        ("topbs_period",["2026-11-13","2026-11-15"]),
                        ("topbs_rooms",["101"]),("generic_room","101")]:
            x=sample();x[key]=val
            self.assertEqual(m.inspect(x,NOW)["candidateFields"],[])
    def test_unknown_ticket_identity_never_promoted(self):
        for key,val in [("ticket_url","https://kham.com.tw/"),("ticket_event_id","7416"),
                        ("session_id",0),("ticket_price",False),("show_time","19:30"),
                        ("golden_accepted",False)]:
            x=sample();x[key]=val
            self.assertEqual(m.inspect(x,NOW)["decision"],"HOLD_UNVERIFIED_TICKET_CLAIM")
    def test_timestamp(self):
        for stamp in [None,"bad","2026-11-02T16:05:00"]:
            self.assertEqual(m.inspect(sample(),stamp)["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":unittest.main()

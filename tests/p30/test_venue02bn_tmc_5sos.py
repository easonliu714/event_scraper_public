"""TMC 5SOS official LIST/detail to canonical tixCraft event URL, role tests."""
import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02bn_tmc_5sos.py"
s=importlib.util.spec_from_file_location("venue02bn",p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    return {"venue_list":m.LIST,"list_detail_href":m.VENUE_DETAIL,
            "venue_detail":m.VENUE_DETAIL,"venue_title":m.VENUE_TITLE,
            "venue_show":m.SHOW,"venue":m.VENUE,
            "venue_ticket_href":m.TICKET_DETAIL,"ticket_detail":m.TICKET_DETAIL,
            "ticket_title":m.TICKET_TITLE,"ticket_show":m.SHOW,
            "venue_min_general_price":3380,"venue_vip_seat_package":8680,
            "ticket_vip_standing_package":7380,
            "vip_upgrade_role":"BENEFIT_ONLY_REQUIRES_VALID_CONCERT_TICKET",
            "vip_package_role":"INCLUDES_ADMISSION","ticket_service_fee":200,
            "service_fee_role":"ADDITIONAL_PER_TICKET",
            "ticket_session_id":None,"inventory_count":None,
            "upgrade_is_admission":None,"published_event":None}
class TMC5SOSGate(unittest.TestCase):
    def check(self,key=None,value=None):
        row=fixture()
        if key is not None: row[key]=value
        return m.inspect(row,"2026-11-02")
    def test_review_two_distinct_provenances(self):
        r=self.check()
        self.assertEqual(r["decision"],"REVIEW_DIRECT_TICKET_EVENT_HOLD_SESSION")
        self.assertEqual(r["acceptedFields"],0)
        self.assertEqual(r["ticketSessionIdsVerified"],0)
        self.assertFalse(r["published"])
        self.assertEqual(len(r["candidateFields"]),5)
        self.assertEqual({x["source"] for x in r["candidateFields"]},{"TMC_VENUE_OFFICIAL","TIXCRAFT_03"})
        self.assertTrue(all(x["decision"]=="REVIEW" and x["source_url"].startswith("https://") for x in r["candidateFields"]))
    def test_exact_official_list_detail_and_ticket(self):
        for key,value,decision in [
            ("venue_list",m.LIST+"?p=1","HOLD_VENUE_LIST"),
            ("list_detail_href",m.VENUE_DETAIL+"#show","HOLD_VENUE_DETAIL_IDENTITY"),
            ("venue_detail",m.TICKET_DETAIL,"HOLD_VENUE_DETAIL_IDENTITY"),
            ("venue_title","unrelated","HOLD_VENUE_SHOW_TITLE"),
            ("venue_show","2026-10-25T20:00","HOLD_VENUE_SHOW_TITLE"),
            ("venue_ticket_href",m.TICKET_DETAIL.replace("26_5sos","26_5sos_v"),"HOLD_DIRECT_TICKET_LINK"),
            ("ticket_detail","https://evil.example/activity/detail/26_5sos","HOLD_DIRECT_TICKET_LINK"),
            ("ticket_title","different","HOLD_TICKET_EVENT_PARITY"),
            ("ticket_show","2026-11-26T20:00","HOLD_TICKET_EVENT_PARITY")]:
            with self.subTest(key=key): self.assertEqual(self.check(key,value)["decision"],decision)
    def test_vip_upgrade_is_not_admission(self):
        for key,value,decision in [
            ("venue_min_general_price",8680,"HOLD_PRICE_CATEGORY"),
            ("venue_vip_seat_package",7380,"HOLD_PRICE_CATEGORY"),
            ("ticket_vip_standing_package",8680,"HOLD_PRICE_CATEGORY"),
            ("vip_upgrade_role","INCLUDES_ADMISSION","HOLD_UPGRADE_NOT_ADMISSION"),
            ("vip_package_role","BENEFIT_ONLY","HOLD_UPGRADE_NOT_ADMISSION"),
            ("ticket_service_fee",2200,"HOLD_FEE_NOT_FACE_VALUE"),
            ("service_fee_role","FACE_VALUE","HOLD_FEE_NOT_FACE_VALUE")]:
            with self.subTest(key=key): self.assertEqual(self.check(key,value)["decision"],decision)
    def test_no_unverified_ticket_session_or_publication(self):
        for key,value in [("ticket_session_id","26_5sos"),("inventory_count",5),
                          ("upgrade_is_admission",True),("published_event",True)]:
            with self.subTest(key=key): self.assertEqual(self.check(key,value)["decision"],"HOLD_UNVERIFIED_SESSION_OR_PUBLICATION")
    def test_observation(self):
        self.assertEqual(m.inspect(fixture(),"bad")["decision"],"HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None,"2026-11-02")["decision"],"HOLD_VENUE_LIST")
if __name__=="__main__": unittest.main()

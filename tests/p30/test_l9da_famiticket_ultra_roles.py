"""FamiTicket #07 source-bound REVIEW role negatives; no network in CI."""
import unittest
from scripts import p30_l9da_famiticket_ultra_roles as m

STAMP="2026-11-02T07:01:00+08:00"

def sample():
    return dict(list_url=m.LIST,list_detail_href=m.DETAIL,detail_url=m.DETAIL,
                list_title=m.TITLE,detail_title=m.TITLE,event_date=m.EVENT_DATE,
                venue=m.VENUE,ee_ga_cutoff=m.ENTRY_CUTOFF,
                late_upgrade_surcharge=m.LATE_UPGRADE_SURCHARGE,
                hsr_discount_from=m.HSR_DISCOUNT_FROM,
                ee_ga_role="CONDITIONAL_ENTRY_DEADLINE",
                upgrade_role="LATE_ENTRY_UPGRADE_SURCHARGE",
                hsr_role="TRANSPORT_BUNDLE_DISCOUNT")

class FamiTicketUltraRoles(unittest.TestCase):
    def test_source_bound_review(self):
        r=m.inspect(sample(),STAMP)
        self.assertEqual(r["decision"],"REVIEW")
        self.assertEqual(len(r["candidateFields"]),6)
        self.assertEqual({x["source"] for x in r["candidateFields"]},{m.DETAIL})
        self.assertEqual({x["decision"] for x in r["candidateFields"]},{"REVIEW"})
        self.assertEqual(r["acceptedFields"],0)
        self.assertEqual(r["ticketSessionIdsVerified"],0)
        self.assertEqual(r["goldenAccepted"],0)
        self.assertFalse(r["published"])
    def test_exact_list_to_detail_identity(self):
        for key,bad,reason in [
            ("list_url","https://www.famiticket.com.tw/Info","HOLD_LIST_URL"),
            ("list_detail_href",m.DETAIL+"?event=other","HOLD_LIST_DETAIL_EDGE"),
            ("detail_url","https://[bad/Home/Activity/Info","HOLD_DETAIL_URL"),
            ("detail_url","https://www.famiticket.com.tw@fake.test/Home","HOLD_DETAIL_URL"),
            ("list_title","別的活動","HOLD_TITLE_IDENTITY"),
            ("detail_title","Ultra Taiwan 2025","HOLD_TITLE_IDENTITY"),
        ]:
            with self.subTest(key=key):
                x=sample();x[key]=bad
                self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_no_promotion_of_cutoff_surcharge_or_discount(self):
        for key,bad,reason in [
            ("event_date","2026-11-15","HOLD_EVENT_DATE_VENUE"),
            ("venue","台北小巨蛋","HOLD_EVENT_DATE_VENUE"),
            ("ee_ga_cutoff","19:30","HOLD_ENTRY_CONDITION"),
            ("late_upgrade_surcharge",0,"HOLD_ENTRY_CONDITION"),
            ("hsr_discount_from",100,"HOLD_HSR_DISCOUNT_ROLE"),
            ("ee_ga_role","PERFORMANCE_START","HOLD_ROLE_CONFUSION"),
            ("upgrade_role","ADMISSION_PRICE","HOLD_ROLE_CONFUSION"),
            ("hsr_role","GENERAL_TICKET_DISCOUNT","HOLD_ROLE_CONFUSION"),
        ]:
            with self.subTest(key=key):
                x=sample();x[key]=bad
                self.assertEqual(m.inspect(x,STAMP)["decision"],reason)
    def test_unverified_fields_fail_closed(self):
        for key,value in [("showtime","2026-11-14T15:30"),("admission_price",1000),
                          ("ticket_session_id","ULTRA2026"),("inventory",100),
                          ("published_event",True)]:
            with self.subTest(key=key):
                x=sample();x[key]=value
                self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_UNVERIFIED_SESSION_PRICE_OR_PUBLICATION")
    def test_malformed_input(self):
        for x in (None,[],0,"raw"):
            self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_SOURCE")
        for stamp in (None,"2026-11-02T07:01:00","bad"):
            self.assertEqual(m.inspect(sample(),stamp)["decision"],"HOLD_OBSERVATION")
if __name__=="__main__": unittest.main()

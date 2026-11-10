"""Offline regressions for source-reader evidence; no official GET in CI."""
import copy
import unittest
from scripts import p30_venue02bo_tainex_exhibition as m

STAMP = "2026-11-02T06:57:00+08:00"

def sample():
    return dict(list_url=m.LIST, list_detail_href=m.DETAIL,
                detail_url=m.DETAIL, list_title=m.TITLE, detail_title=m.TITLE,
                period_label="展覽活動期間", period_start=m.START, period_end=m.END,
                venue_label="活動地點", venue_hall=m.HALL, floors=list(m.FLOORS),
                organizer_label="主辦單位", organizer=m.ORGANIZER,
                external_website_label="官方網站", external_website=m.ORGANIZER_SITE)

class TaiNEXSourceReview(unittest.TestCase):
    def test_review_source_bound_period_not_ticket_session(self):
        r = m.inspect(sample(), STAMP)
        self.assertEqual(r["decision"], "REVIEW")
        self.assertEqual(len(r["candidateFields"]), 6)
        self.assertEqual({x["source"] for x in r["candidateFields"]}, {m.DETAIL})
        self.assertEqual({x["decision"] for x in r["candidateFields"]}, {"REVIEW"})
        self.assertEqual(r["acceptedFields"], 0)
        self.assertEqual(r["goldenAccepted"], 0)
        self.assertEqual(r["ticketSessionIdsVerified"], 0)
        self.assertFalse(r["published"])
    def test_exact_list_detail_edge(self):
        for key, bad, decision in [
            ("list_url", "https://www.tainex.com.tw/en/event", "HOLD_LIST_URL"),
            ("list_detail_href", "https://www.tainex.com.tw/event/690", "HOLD_LIST_DETAIL_EDGE"),
            ("detail_url", "https://www.tainex.com.tw/event/691?x=1", "HOLD_DETAIL_URL"),
            ("detail_url", "https://www.tainex.com.tw@other.test/event/691", "HOLD_DETAIL_URL"),
            ("detail_url", "https://[invalid/event/691", "HOLD_DETAIL_URL"),
        ]:
            with self.subTest(key=key, bad=bad):
                x=sample();x[key]=bad
                self.assertEqual(m.inspect(x, STAMP)["decision"],decision)
    def test_title_date_and_venue_role_refusals(self):
        for key,bad,decision in [
            ("list_title","2026臺灣國際咖啡展","HOLD_LIST_DETAIL_TITLE"),
            ("detail_title","2026臺灣茶業博覽會","HOLD_LIST_DETAIL_TITLE"),
            ("period_label","公告日期","HOLD_PERIOD_ROLE"),
            ("period_start","2026-11-12","HOLD_PERIOD_RANGE"),
            ("period_end","2026-11-17","HOLD_PERIOD_RANGE"),
            ("venue_label","售票地點","HOLD_VENUE_ROLE"),
            ("venue_hall","南港展覽館2館","HOLD_VENUE_ROLE"),
            ("floors",["一樓展場"],"HOLD_FLOOR_AMBIGUITY"),
            ("organizer_label","售票平台","HOLD_ORGANIZER_ROLE"),
            ("organizer","別的主辦單位","HOLD_ORGANIZER_ROLE"),
            ("external_website_label","售票連結","HOLD_EXTERNAL_WEBSITE_ROLE"),
        ]:
            with self.subTest(key=key):
                x=sample();x[key]=bad
                self.assertEqual(m.inspect(x, STAMP)["decision"],decision)
    def test_organizer_link_not_ticket_id(self):
        for key,value in [("ticket_event_id","691"),("ticket_url","https://www.chanchao.com.tw/food/"),
                          ("ticket_session_id","691"),("showtime","2026-11-13T10:00"),
                          ("admission_price",100),("inventory",100),("published_event",True)]:
            with self.subTest(key=key):
                x=sample();x[key]=value
                self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_UNVERIFIED_TICKET_OR_PUBLICATION")
    def test_invalid_inputs_fail_closed(self):
        for x in (None,[],3,"detail"):
            self.assertEqual(m.inspect(x,STAMP)["decision"],"HOLD_SOURCE_EVIDENCE")
        for stamp in (None,"2026-11-02T06:57:00","invalid"):
            self.assertEqual(m.inspect(sample(),stamp)["decision"],"HOLD_OBSERVATION")
if __name__=="__main__":
    unittest.main()

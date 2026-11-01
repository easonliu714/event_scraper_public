"""P30-VENUE-02BG fail-closed postponement and ticket-identity tests."""
import importlib.util
import pathlib
import unittest

p=pathlib.Path(__file__).resolve().parents[2]/"scripts/p30_venue02bg_cloudgate_postponement.py"
spec=importlib.util.spec_from_file_location("gate",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return dict(list_url=m.LIST,list_detail_href=m.DETAIL,detail_url=m.DETAIL,
                detail_id="1680",title=m.TITLE,original_shows=m.ORIGINAL,
                revised_shows=m.REVISED,october_shows=m.OCTOBER,
                notice_date="2026-09-24",notice_is_show=False,
                original_november_still_current=False,
                venue_unchanged=True,venue="雲門劇場",
                refund_grace_deadline="2026-11-14",refund_is_show=False,
                claimed_platform="OPENTIX",opentix_event_url=None,
                descriptive_price=400,discount_is_session_price=False,
                ticket_session_id=None,inventory=None,checkout=None,published_event=None)

class Gate(unittest.TestCase):
    def check(self,k=None,v=None):
        x=fixture()
        if k is not None:x[k]=v
        return m.inspect(x,"2026-11-01")
    def test_review_only(self):
        x=self.check()
        self.assertEqual(x["decision"],"REVIEW_CLOUDGATE_POSTPONEMENT_HOLD_OPENTIX_SESSION")
        self.assertEqual(len(x["candidateFields"]),6)
        self.assertTrue(all(c["decision"]=="REVIEW" and c["source_url"]==m.DETAIL for c in x["candidateFields"]))
        self.assertEqual(x["acceptedFields"],0)
        self.assertEqual(x["ticketSessionIdsVerified"],0)
        self.assertFalse(x["published"])
    def test_missing(self):
        self.assertEqual(m.inspect(fixture(),"bad")["decision"],"HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None,"2026-11-01")["decision"],"HOLD_OFFICIAL_LIST")
    def test_exact_identity(self):
        for k,v,d in [
            ("list_url",m.LIST+"?page=1","HOLD_OFFICIAL_LIST"),
            ("list_detail_href",m.DETAIL.replace("1680","1606"),"HOLD_LIST_DETAIL_ID"),
            ("detail_url",m.DETAIL+"#old","HOLD_LIST_DETAIL_ID"),
            ("detail_id","1606","HOLD_DETAIL_ID_TITLE"),
            ("title","other","HOLD_DETAIL_ID_TITLE")]:
            with self.subTest(k=k):self.assertEqual(self.check(k,v)["decision"],d)
    def test_revision_semantics(self):
        for k,v,d in [
            ("revised_shows",m.ORIGINAL,"HOLD_DATE_REVISION_PAIRING"),
            ("original_shows",m.REVISED,"HOLD_DATE_REVISION_PAIRING"),
            ("notice_date","2026-11-14","HOLD_NOTICE_ROLE"),
            ("original_november_still_current",True,"HOLD_SUPERSEDED_NOVEMBER"),
            ("venue_unchanged",False,"HOLD_VENUE_SCOPE"),
            ("refund_is_show",True,"HOLD_REFUND_ROLE"),
            ("claimed_platform","KKTIX","HOLD_PLATFORM_CLAIM_NO_DIRECT_ID"),
            ("opentix_event_url","https://www.opentix.life/event/guess","HOLD_PLATFORM_CLAIM_NO_DIRECT_ID"),
            ("discount_is_session_price",True,"HOLD_DESCRIPTIVE_PRICE_DISCOUNT")]:
            with self.subTest(k=k):self.assertEqual(self.check(k,v)["decision"],d)
    def test_unverified_ticket(self):
        for k,v in [("ticket_session_id","1680"),("inventory",10),
                    ("checkout",m.DETAIL),("published_event",True)]:
            with self.subTest(k=k):
                x=self.check(k,v)
                self.assertEqual(x["decision"],"HOLD_TICKET_SESSION")
                self.assertEqual(x["acceptedFields"],0)

if __name__=="__main__":unittest.main()

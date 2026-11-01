"""P30-L9-CT negative tests for KKTIX direct registration href and 403."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9ct_kktix_registration_guard.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return dict(event_url=m.EVENT, event_id="fdef73bb", event_title=m.TITLE,
                registration_href=m.REGISTRATION, registration_http=403,
                registration_accessible=False, show=m.SHOW, venue=m.VENUE,
                sale_start=m.SALE, sale_is_show=False, standard_price=980,
                accessible_price=490, accessible_is_standard=False,
                pickup_fee=30, pickup_fee_is_ticket_price=False,
                ticket_session_id=None, inventory=None, checkout=None,
                published_event=None, registration_response_body=None)

class Gate(unittest.TestCase):
    def check(self, k=None, v=None):
        x = fixture()
        if k is not None: x[k] = v
        return m.inspect(x, "2026-11-01")
    def test_review_only(self):
        x = self.check()
        self.assertEqual(x["decision"], "REVIEW_KKTIX_DIRECT_REGISTRATION_HREF_403_HOLD_SESSION")
        self.assertEqual(len(x["candidateFields"]), 6)
        self.assertEqual({y["source"] for y in x["candidateFields"]}, {"KKTIX_01"})
        self.assertTrue(all(y["decision"] == "REVIEW" for y in x["candidateFields"]))
        self.assertEqual(x["acceptedFields"], 0)
        self.assertEqual(x["ticketSessionIdsVerified"], 0)
        self.assertFalse(x["published"])
    def test_observation(self):
        self.assertEqual(m.inspect(fixture(), "invalid")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_EVENT_URL")
    def test_identity_url(self):
        for k,v,decision in [
            ("event_url", m.EVENT+"?id=1", "HOLD_EVENT_URL"),
            ("event_url", "https://evil.example/events/fdef73bb", "HOLD_EVENT_URL"),
            ("event_id", "fdef73bc", "HOLD_EVENT_ID_TITLE"),
            ("event_title", "other", "HOLD_EVENT_ID_TITLE"),
            ("registration_href", m.REGISTRATION+"#session", "HOLD_REGISTRATION_HREF"),
            ("registration_href", m.REGISTRATION.replace("kktix.com","kktix.com.evil.example"), "HOLD_REGISTRATION_HREF")]:
            with self.subTest(k=k): self.assertEqual(self.check(k,v)["decision"],decision)
    def test_403_not_session(self):
        for k,v,decision in [
            ("registration_http", 200, "HOLD_REGISTRATION_HTTP_ROLE"),
            ("registration_accessible", True, "HOLD_REGISTRATION_HTTP_ROLE"),
            ("show", m.SALE, "HOLD_SHOW_SALE_ROLE"),
            ("sale_is_show", True, "HOLD_SHOW_SALE_ROLE"),
            ("accessible_is_standard", True, "HOLD_PRICE_ELIGIBILITY"),
            ("standard_price", 490, "HOLD_PRICE_ELIGIBILITY"),
            ("pickup_fee_is_ticket_price", True, "HOLD_PICKUP_FEE_ROLE")]:
            with self.subTest(k=k): self.assertEqual(self.check(k,v)["decision"],decision)
    def test_prohibited_promotions(self):
        for k,v in [("ticket_session_id","fdef73bb"),("inventory",50),
                    ("checkout",m.REGISTRATION),("published_event",True),
                    ("registration_response_body","guessed")]:
            with self.subTest(k=k):
                x=self.check(k,v)
                self.assertEqual(x["decision"],"HOLD_UNVERIFIED_REGISTRATION_SESSION")
                self.assertEqual(x["acceptedFields"],0)

if __name__ == "__main__": unittest.main()

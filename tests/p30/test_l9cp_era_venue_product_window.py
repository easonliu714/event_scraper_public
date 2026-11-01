"""P30-L9-CP source-role fail-closed regression."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cp_era_venue_product_window.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"venue_bulletin": m.VENUE, "venue_ticket_href": m.TICKET,
            "ticket_detail": m.TICKET, "venue_title": m.VENUE_TITLE,
            "ticket_title": m.TICKET_TITLE, "ticket_product_id": "P1FKLQFW",
            "venue_show": m.VENUE_SHOW, "ticket_header_start": m.TICKET_HEADER_START,
            "ticket_header_end": m.TICKET_HEADER_END, "ticket_header_is_session": False,
            "ticket_session_id": None, "ticket_session_price": None, "inventory": None,
            "ticket_button_href": None, "published_event": None}

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def reject(self, reason, key, value):
        result = self.check(key, value)
        self.assertEqual(result["decision"], reason)
        self.assertEqual(result["acceptedFields"], 0)
        self.assertFalse(result["published"])
    def test_source_bound_review(self):
        result = self.check()
        self.assertEqual(result["decision"], "REVIEW_CROSS_SOURCE_PRODUCT_HOLD_SESSION_AND_HEADER_ROLE")
        self.assertEqual(len(result["candidateFields"]), 3)
        self.assertEqual(result["candidateFields"][2]["role"], "PRODUCT_HEADER_WINDOW_NOT_PERFORMANCE_OR_SALE")
        self.assertNotEqual(m.VENUE_SHOW, m.TICKET_HEADER_START)
    def test_invalid_observation(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
    def test_missing_object(self):
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_VENUE_BULLETIN")
    def test_wrong_venue_host(self): self.reject("HOLD_VENUE_BULLETIN", "venue_bulletin", m.VENUE.replace("www.culture.ntpc.gov.tw", "evil.example"))
    def test_wrong_venue_sid(self): self.reject("HOLD_VENUE_BULLETIN", "venue_bulletin", m.VENUE.replace("0Q152372523738311866", "wrong"))
    def test_ticket_host(self): self.reject("HOLD_DIRECT_ERA_PRODUCT_LINK", "venue_ticket_href", m.TICKET.replace("ticket.com.tw", "evil.example"))
    def test_ticket_query(self): self.reject("HOLD_DIRECT_ERA_PRODUCT_LINK", "venue_ticket_href", m.TICKET + "&PRODUCT_ID=BAD")
    def test_detail_fragment(self): self.reject("HOLD_DIRECT_ERA_PRODUCT_LINK", "ticket_detail", m.TICKET + "#x")
    def test_venue_title(self): self.reject("HOLD_EXPLICIT_TITLE_PRODUCT_ID", "venue_title", "different")
    def test_ticket_title(self): self.reject("HOLD_EXPLICIT_TITLE_PRODUCT_ID", "ticket_title", "different")
    def test_product_id(self): self.reject("HOLD_EXPLICIT_TITLE_PRODUCT_ID", "ticket_product_id", "OTHER")
    def test_showtime_role(self): self.reject("HOLD_TIME_ROLE_SOURCE_MISMATCH", "venue_show", m.TICKET_HEADER_START)
    def test_header_start(self): self.reject("HOLD_TIME_ROLE_SOURCE_MISMATCH", "ticket_header_start", m.VENUE_SHOW)
    def test_header_end(self): self.reject("HOLD_TIME_ROLE_SOURCE_MISMATCH", "ticket_header_end", m.VENUE_SHOW)
    def test_header_as_session(self): self.reject("HOLD_PRODUCT_HEADER_NOT_SESSION", "ticket_header_is_session", True)
    def test_session_id(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_id", "P1FKLQFW")
    def test_session_price(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_price", 1000)
    def test_inventory(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "inventory", 12)
    def test_button_href(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_button_href", m.TICKET)
    def test_publication(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "published_event", True)

if __name__ == "__main__":
    unittest.main()

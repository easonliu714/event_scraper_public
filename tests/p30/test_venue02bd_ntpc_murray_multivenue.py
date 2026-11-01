"""P30-VENUE-02BD multi-venue identity and venue-showtime refusal tests."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02bd_ntpc_murray_multivenue.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"venue_bulletin": m.BULLETIN, "venue_ticket_href": m.OPENTIX,
            "ticket_detail": m.OPENTIX, "venue_title": m.VENUE_TITLE,
            "ticket_title": m.TICKET_TITLE, "ticket_event_id": "2087017782302437377",
            "venue_showtimes": m.SHOWS, "venue_name": m.TICKET_VENUES[0],
            "ticket_page_venue_choices": m.TICKET_VENUES,
            "venue_showtimes_are_ticket_sessions": False,
            "ticket_session_ids": None, "session_prices": None,
            "inventory": None, "published_event": None, "ticket_button_href": None}

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def reject(self, reason, key, value):
        r = self.check(key, value)
        self.assertEqual(r["decision"], reason)
        self.assertEqual(r["acceptedFields"], 0)
        self.assertFalse(r["published"])
    def test_review(self):
        r = self.check()
        self.assertEqual(r["decision"], "REVIEW_NTPC_SHOWS_OPENTIX_MULTIVENUE_HOLD_SESSION_MAPPING")
        self.assertEqual(len(r["candidateFields"]), 3)
        self.assertEqual(len(r["candidateFields"][0]["value"]), 4)
        self.assertEqual(len(r["candidateFields"][2]["value"]), 3)
        self.assertTrue(all(f["decision"] == "REVIEW" for f in r["candidateFields"]))
    def test_bad_date(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
    def test_bad_object(self):
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_VENUE_BULLETIN")
    def test_bulletin_sid(self): self.reject("HOLD_VENUE_BULLETIN", "venue_bulletin", m.BULLETIN.replace("0Q152372523738311866", "wrong"))
    def test_ticket_host(self): self.reject("HOLD_DIRECT_OPENTIX_EVENT_URL", "venue_ticket_href", m.OPENTIX.replace("www.opentix.life", "evil.example"))
    def test_ticket_query(self): self.reject("HOLD_DIRECT_OPENTIX_EVENT_URL", "ticket_detail", m.OPENTIX + "?session=1")
    def test_ticket_id(self): self.reject("HOLD_TITLE_EVENT_ID", "ticket_event_id", "2086734015886159873")
    def test_ticket_title(self): self.reject("HOLD_TITLE_EVENT_ID", "ticket_title", "different")
    def test_venue_title(self): self.reject("HOLD_TITLE_EVENT_ID", "venue_title", "different")
    def test_venue_show(self): self.reject("HOLD_LOCAL_VENUE_SHOWTIMES", "venue_showtimes", m.SHOWS[:2])
    def test_venue_name(self): self.reject("HOLD_LOCAL_VENUE_SHOWTIMES", "venue_name", m.TICKET_VENUES[1])
    def test_venue_choice(self): self.reject("HOLD_MULTIVENUE_EVENT_SCOPE", "ticket_page_venue_choices", (m.TICKET_VENUES[0],))
    def test_session_mapping(self): self.reject("HOLD_UNVERIFIED_SESSION_MAPPING", "venue_showtimes_are_ticket_sessions", True)
    def test_session_ids(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_ids", ["guess"])
    def test_session_price(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "session_prices", [1000])
    def test_inventory(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "inventory", 20)
    def test_publish(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "published_event", True)
    def test_button(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_button_href", m.OPENTIX)

if __name__ == "__main__":
    unittest.main()

"""P30-VENUE-02BI source identity and ticket role negative tests."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02bi_xinzhuang_direct_opentix.py"
s = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def fixture():
    return dict(venue_list_url=m.LIST, venue_detail_url=m.DETAIL,
                venue_sid="0Q252550255605202263", venue_title=m.TITLE,
                venue_show=m.SHOW, venue_price_bands=[400, 500],
                venue_ticket_href=m.TICKET, ticket_event_url=m.TICKET,
                ticket_event_id="2089995501384269825", ticket_title=m.TITLE,
                ticket_venue=m.VENUE, ticket_show=m.SHOW,
                ticket_open="2026-12-05T13:30",
                earlybird_end="2026-10-11T23:59",
                earlybird_is_regular_price=False, past_event_href=m.PAST,
                past_event_off_shelf=True, ticket_session_id=None,
                inventory=None, checkout=None, published_event=None,
                past_event_as_future=None)

class Gate(unittest.TestCase):
    def check(self, k=None, v=None):
        x = fixture()
        if k is not None:
            x[k] = v
        return m.inspect(x, "2026-11-01")
    def test_source_bound_review(self):
        y = self.check()
        self.assertEqual(y["decision"], "REVIEW_XINZHUANG_DIRECT_OPENTIX_EVENT_HOLD_SESSION")
        self.assertEqual(len(y["candidateFields"]), 7)
        self.assertEqual({z["source"] for z in y["candidateFields"]},
                         {"XINZHUANG_OFFICIAL", "OPENTIX_05"})
        self.assertTrue(all(z["decision"] == "REVIEW" and z["observed_at"] == "2026-11-01"
                            for z in y["candidateFields"]))
        self.assertEqual(y["acceptedFields"], 0)
        self.assertEqual(y["ticketSessionIdsVerified"], 0)
        self.assertFalse(y["published"])
    def test_exact_source_and_event_id(self):
        for k, v, d in [
            ("venue_list_url", m.LIST + "#list", "HOLD_VENUE_LIST"),
            ("venue_detail_url", m.DETAIL.replace("0Q252550255605202263", "0Q252550255605202264"), "HOLD_VENUE_DETAIL"),
            ("venue_sid", "other", "HOLD_VENUE_ID_TITLE"),
            ("venue_title", "different", "HOLD_VENUE_ID_TITLE"),
            ("venue_ticket_href", m.TICKET + "?foo=1", "HOLD_DIRECT_OPENTIX_EVENT_EDGE"),
            ("ticket_event_url", "https://evil.example/event/2089995501384269825", "HOLD_DIRECT_OPENTIX_EVENT_EDGE"),
            ("ticket_event_id", "2071939794940801025", "HOLD_TICKET_EVENT_ID_TITLE")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], d)
    def test_show_open_price_roles(self):
        for k, v, d in [
            ("venue_show", "2026-12-05T13:30", "HOLD_VENUE_SHOW_PRICE_SCOPE"),
            ("venue_price_bands", [360, 400], "HOLD_VENUE_SHOW_PRICE_SCOPE"),
            ("ticket_show", "2026-12-05T13:30", "HOLD_TICKET_VENUE_SHOW_OPEN"),
            ("ticket_open", m.SHOW, "HOLD_TICKET_VENUE_SHOW_OPEN"),
            ("earlybird_is_regular_price", True, "HOLD_DISCOUNT_NOT_GENERAL_PRICE"),
            ("past_event_off_shelf", False, "HOLD_PAST_EVENT_OFF_SHELF")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], d)
    def test_no_past_or_session_promotion(self):
        for k, v in [("ticket_session_id", "guessed"), ("inventory", 1),
                     ("checkout", m.TICKET), ("published_event", True),
                     ("past_event_as_future", True)]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], "HOLD_UNVERIFIED_SESSION_OR_PAST_PROMOTION")
    def test_invalid_observation(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_VENUE_LIST")

if __name__ == "__main__":
    unittest.main()

"""Source-derived offline regression. CI never fetches official websites."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9ci_opentix_multi_venue_identity.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"venue_url": m.VENUE_URL, "opentix_url": m.OPENTIX_URL,
            "event_id": m.EVENT_ID, "linked_event_canonical_url": m.OPENTIX_URL,
            "venue_title": m.VENUE_TITLE, "opentix_title": m.TITLE,
            "venue": m.VENUE, "opentix_venue": m.VENUE,
            "opentix_venues": list(m.VENUES),
            "shows": [{"date": d, "time": t, "weekday": w,
                       "role": "VENUE_DESCRIPTIVE_PERFORMANCE", "ticket_session_id": None}
                      for d, t, w in m.SHOWS],
            "ticket_session_ids": None, "inventory": None, "session_price": None,
            "venues_are_sessions": False, "sale_is_showtime": False}

class Gate(unittest.TestCase):
    def check(self, change=None):
        x = fixture()
        if change:
            change(x)
        return m.inspect(x, "2026-11-01")
    def reject(self, decision, change):
        r = self.check(change)
        self.assertEqual(r["decision"], decision)
        self.assertEqual(r["acceptedFields"], 0)
        self.assertFalse(r["published"])
    def test_source_bound(self):
        r = self.check()
        self.assertEqual(r["decision"], "HOLD_EVENT_PARITY_NO_TICKET_SESSION_IDS")
        self.assertEqual(len(r["provenance"]), 4)
        self.assertEqual(r["goldenAccepted"], 0)
    def test_bad_observation(self):
        self.assertEqual(m.inspect(fixture(), "2026-02-30")["decision"], "HOLD_OBSERVED_AT")
    def test_wrong_venue_host(self):
        self.reject("HOLD_VENUE_SOURCE", lambda x: x.update(venue_url="https://evil.example"))
    def test_wrong_sid(self):
        self.reject("HOLD_VENUE_SOURCE", lambda x: x.update(venue_url=m.VENUE_URL.replace("0Q152372523738311866", "other")))
    def test_event_id(self):
        self.reject("HOLD_CANONICAL_EVENT_ID", lambda x: x.update(event_id="other"))
    def test_tracking_query(self):
        self.reject("HOLD_CANONICAL_EVENT_ID", lambda x: x.update(opentix_url=m.OPENTIX_URL + "?q=1"))
    def test_direct_link(self):
        self.reject("HOLD_DIRECT_LINK_PARITY", lambda x: x.update(linked_event_canonical_url="other"))
    def test_title(self):
        self.reject("HOLD_CROSS_SOURCE_TITLE", lambda x: x.update(opentix_title="other"))
    def test_venue(self):
        self.reject("HOLD_CROSS_SOURCE_VENUE", lambda x: x.update(opentix_venue="other"))
    def test_unverified_venue_label(self):
        self.reject("HOLD_NINE_DISTINCT_VENUES", lambda x: x["opentix_venues"].__setitem__(1, "invented venue"))
    def test_venue_count(self):
        self.reject("HOLD_NINE_DISTINCT_VENUES", lambda x: x["opentix_venues"].pop())
    def test_duplicate_venue(self):
        self.reject("HOLD_NINE_DISTINCT_VENUES", lambda x: x["opentix_venues"].__setitem__(1, m.VENUE))
    def test_session_id(self):
        self.reject("HOLD_NO_STATIC_TICKET_SESSION", lambda x: x.update(ticket_session_ids=["invented"]))
    def test_inventory(self):
        self.reject("HOLD_NO_STATIC_TICKET_SESSION", lambda x: x.update(inventory=9))
    def test_session_price(self):
        self.reject("HOLD_NO_STATIC_TICKET_SESSION", lambda x: x.update(session_price=1000))
    def test_venues_are_not_sessions(self):
        self.reject("HOLD_VENUE_SALE_ROLE", lambda x: x.update(venues_are_sessions=True))
    def test_sale_is_not_show(self):
        self.reject("HOLD_VENUE_SALE_ROLE", lambda x: x.update(sale_is_showtime=True))
    def test_missing_show(self):
        self.reject("HOLD_SHOW_COUNT", lambda x: x["shows"].pop())
    def test_changed_show(self):
        self.reject("HOLD_SHOW_LOCAL_TEXT", lambda x: x["shows"][0].update(time="15:30"))
    def test_fabricated_show_session(self):
        self.reject("HOLD_SHOW_NOT_TICKET_SESSION", lambda x: x["shows"][0].update(ticket_session_id="fake"))

if __name__ == "__main__":
    unittest.main()

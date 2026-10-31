"""Official bulletin evidence, offline negative tests, no live CI GET."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02av_ntpc_bulletin_weekday.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"venue_url": m.VENUE_URL, "venue_sid": "0Q152372523738311866",
            "updated_at": "2026-10-28", "update_role": "BULLETIN_UPDATE_NOT_SHOW",
            "opentix_url": m.OPENTIX_URL, "event_id": m.EVENT_ID,
            "linked_event_canonical_url": m.OPENTIX_URL,
            "venue_title": m.TITLE, "opentix_title": m.TITLE,
            "venue": m.VENUE, "opentix_venue": m.VENUE,
            "opentix_date_range": ("2026-11-21", "2026-11-22"),
            "ticket_session_ids": None, "inventory": None, "per_session_price": None,
            "shows": [{"date": d, "time": t, "weekday": w,
                       "role": "VENUE_DESCRIPTIVE_PERFORMANCE", "ticket_session_id": None}
                      for d, t, w in m.SHOWS],
            "conflicts": [{"title": t, "date": d, "weekday": w}
                          for t, d, w in m.CONFLICTS]}

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
    def test_two_source_weekday_conflicts_quarantined(self):
        r = self.check()
        self.assertEqual(r["decision"], "HOLD_EVENT_ID_AND_TWO_WEEKDAY_CONFLICTS_NO_TICKET_SESSIONS")
        self.assertEqual(len(r["provenance"]), 4)
        self.assertEqual([(q["calendar_weekday"], q["raw_weekday"]) for q in r["quarantined"]],
                         [("二", "日"), ("五", "六")])
        self.assertEqual(r["goldenAccepted"], 0)
    def test_bad_observation(self):
        self.assertEqual(m.inspect(fixture(), "2026-02-30")["decision"], "HOLD_OBSERVED_AT")
    def test_host(self):
        self.reject("HOLD_BULLETIN_SID", lambda x: x.update(venue_url="https://evil.example"))
    def test_sid(self):
        self.reject("HOLD_BULLETIN_SID", lambda x: x.update(venue_sid="other"))
    def test_update_date_role(self):
        self.reject("HOLD_UPDATE_DATE_ROLE", lambda x: x.update(update_role="SHOWTIME"))
    def test_event_id(self):
        self.reject("HOLD_DIRECT_OPENTIX_EVENT_ID", lambda x: x.update(event_id="other"))
    def test_query(self):
        self.reject("HOLD_DIRECT_OPENTIX_EVENT_ID", lambda x: x.update(opentix_url=m.OPENTIX_URL + "?q=1"))
    def test_direct_link(self):
        self.reject("HOLD_DIRECT_OPENTIX_EVENT_ID", lambda x: x.update(linked_event_canonical_url="other"))
    def test_title(self):
        self.reject("HOLD_TITLE_VENUE", lambda x: x.update(venue_title="other"))
    def test_venue(self):
        self.reject("HOLD_TITLE_VENUE", lambda x: x.update(opentix_venue="other"))
    def test_range(self):
        self.reject("HOLD_EVENT_DATE_RANGE", lambda x: x.update(opentix_date_range=("2026-11-21", "2026-11-23")))
    def test_inventory(self):
        self.reject("HOLD_NO_TICKET_SESSION_OR_PRICE", lambda x: x.update(inventory=5))
    def test_session(self):
        self.reject("HOLD_NO_TICKET_SESSION_OR_PRICE", lambda x: x.update(ticket_session_ids=["fake"]))
    def test_price(self):
        self.reject("HOLD_NO_TICKET_SESSION_OR_PRICE", lambda x: x.update(per_session_price=1000))
    def test_missing_show(self):
        self.reject("HOLD_THREE_SHOWS", lambda x: x["shows"].pop())
    def test_changed_show(self):
        self.reject("HOLD_SHOW_TEXT", lambda x: x["shows"][0].update(time="15:30"))
    def test_fabricated_show_session(self):
        self.reject("HOLD_SHOW_NOT_SESSION", lambda x: x["shows"][0].update(ticket_session_id="fake"))
    def test_missing_conflict(self):
        self.reject("HOLD_CONFLICT_ROW_COUNT", lambda x: x["conflicts"].pop())
    def test_unsupported_autocorrection(self):
        self.reject("HOLD_CONFLICT_SOURCE_TEXT", lambda x: x["conflicts"][0].update(weekday="二"))
    def test_mutated_conflict_date(self):
        self.reject("HOLD_CONFLICT_SOURCE_TEXT", lambda x: x["conflicts"][1].update(date="2026-11-21"))

if __name__ == "__main__":
    unittest.main()

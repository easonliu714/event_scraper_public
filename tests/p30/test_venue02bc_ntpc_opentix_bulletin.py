"""P30-VENUE-02BC official venue bulletin direct OPENTIX link and weekday conflict."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02bc_ntpc_opentix_bulletin.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"index_url": m.INDEX, "index_bulletin_href": m.BULLETIN,
            "bulletin_url": m.BULLETIN, "venue_title": m.VENUE_TITLE,
            "opentix_title": m.OPENTIX_TITLE, "venue_ticket_href": m.OPENTIX,
            "opentix_detail_url": m.OPENTIX, "venue_name": "新北市藝文中心演藝廳",
            "opentix_venue": "新北市藝文中心演藝廳", "venue_showtimes": m.SHOWS,
            "conflict_date": m.CONFLICT_DATE, "conflict_weekday": m.CONFLICT_LABEL,
            "ticket_session_ids": None, "ticket_session_prices": None,
            "inventory": None, "published_event": None}

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
        self.assertEqual(result["decision"], "REVIEW_EVENT_LINK_HOLD_TICKET_SESSIONS_AND_OTHER_ROW_WEEKDAY")
        self.assertEqual(len(result["candidateFields"]), 3)
        self.assertEqual(result["candidateFields"][2]["value"], "2086734015886159873")
        self.assertEqual(result["conflicts"][0]["decision"], "HOLD_WEEKDAY_CONFLICT")
        self.assertEqual(result["ticketSessionIdsVerified"], 0)
    def test_invalid_observation(self):
        self.assertEqual(m.inspect(fixture(), "wrong")["decision"], "HOLD_OBSERVATION")
    def test_index_host(self): self.reject("HOLD_VENUE_INDEX", "index_url", "https://evil.example/sitesearch")
    def test_index_query(self): self.reject("HOLD_VENUE_INDEX", "index_url", m.INDEX + "?x=1")
    def test_bulletin_sid(self): self.reject("HOLD_SAME_SID_BULLETIN", "index_bulletin_href", m.BULLETIN.replace("0Q152372523738311866", "OTHER"))
    def test_bulletin_host(self): self.reject("HOLD_SAME_SID_BULLETIN", "bulletin_url", m.BULLETIN.replace("www.culture.ntpc.gov.tw", "evil.example"))
    def test_title(self): self.reject("HOLD_EXPLICIT_CROSS_SOURCE_TITLE", "venue_title", "different")
    def test_opentix_title(self): self.reject("HOLD_EXPLICIT_CROSS_SOURCE_TITLE", "opentix_title", m.VENUE_TITLE)
    def test_opentix_host(self): self.reject("HOLD_CANONICAL_OPENTIX_EVENT_URL", "venue_ticket_href", m.OPENTIX.replace("www.opentix.life", "evil.example"))
    def test_opentix_id(self): self.reject("HOLD_CANONICAL_OPENTIX_EVENT_URL", "opentix_detail_url", m.OPENTIX.replace("2086734015886159873", "OTHER"))
    def test_opentix_tracking_query(self): self.reject("HOLD_CANONICAL_OPENTIX_EVENT_URL", "opentix_detail_url", m.OPENTIX + "?srsltid=tracking")
    def test_venue(self): self.reject("HOLD_VENUE_MATCH", "venue_name", "another")
    def test_ticket_venue(self): self.reject("HOLD_VENUE_MATCH", "opentix_venue", "another")
    def test_show_set(self): self.reject("HOLD_VENUE_SHOWTIME_SET", "venue_showtimes", m.SHOWS[:2])
    def test_show_not_ticket_sessions(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_ids", m.SHOWS)
    def test_conflict_date(self): self.reject("HOLD_BULLETIN_CONFLICT_EVIDENCE", "conflict_date", "2026-11-11")
    def test_conflict_label(self): self.reject("HOLD_BULLETIN_CONFLICT_EVIDENCE", "conflict_weekday", "二")
    def test_ticket_session_prices(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_prices", (1000,))
    def test_inventory(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "inventory", 2)
    def test_publication(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "published_event", True)

if __name__ == "__main__":
    unittest.main()

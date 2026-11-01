"""P30-VENUE-02BJ: direct venue Event edge, multi-venue and weekday quarantine."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02bj_ntpc_multivenue_weekday.py"
s = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def fixture():
    return dict(venue_list_url=m.LIST, venue_detail_url=m.DETAIL,
                venue_bulletin_sid="0Q152372523738311866",
                venue_title=m.VENUE_TITLE, show_rows=list(m.SHOWS),
                venue=m.VENUE, ticket_venue=m.VENUE, ticket_title=m.TICKET_TITLE,
                venue_ticket_href=m.TICKET, ticket_event_url=m.TICKET,
                ticket_event_id="2086734015886159873", ticket_is_multivenue=True,
                ticket_venue_count=9, weekday_conflicts=[list(x) for x in m.CONFLICTS],
                quarantine_weekday_mismatches=True, bulk_accept_all_bulletin_rows=False,
                ticket_show_rows_verified=False, ticket_session_ids=None,
                inventory=None, checkout=None, published_event=None,
                other_venue_as_same_session=None)

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def test_source_bound_review_and_quarantine(self):
        y = self.check()
        self.assertEqual(y["decision"], "REVIEW_NTPC_MULTIVENUE_EVENT_HOLD_WEEKDAY_AND_SESSIONS")
        self.assertEqual(len(y["candidateFields"]), 5)
        self.assertEqual(y["acceptedFields"], 0)
        self.assertEqual(y["ticketSessionIdsVerified"], 0)
        self.assertFalse(y["published"])
        self.assertEqual(y["quarantinedRows"], [{"date":"2026-11-10","printed":"日","calendar":"二"},
                                                 {"date":"2026-11-20","printed":"六","calendar":"五"}])
        self.assertTrue(all(z["decision"] == "REVIEW" and z["observed_at"] == "2026-11-01"
                            for z in y["candidateFields"]))
    def test_exact_source_and_ticket_identity(self):
        for k, v, d in [
            ("venue_list_url", m.LIST+"#fake", "HOLD_VENUE_LIST"),
            ("venue_detail_url", m.DETAIL.replace("0Q152372523738311866","other"), "HOLD_VENUE_DETAIL"),
            ("venue_bulletin_sid", "other", "HOLD_BULLETIN_ID_TITLE"),
            ("venue_title", "another", "HOLD_BULLETIN_ID_TITLE"),
            ("venue_ticket_href", "https://evil.example/event/2086734015886159873", "HOLD_DIRECT_OPENTIX_EDGE"),
            ("ticket_event_url", m.TICKET+"?fake=1", "HOLD_DIRECT_OPENTIX_EDGE"),
            ("ticket_event_id", "2089995501384269825", "HOLD_OPENTIX_EVENT_ID")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], d)
    def test_show_title_and_multivenue_scope(self):
        for k, v, d in [
            ("show_rows", list(m.SHOWS[:2]), "HOLD_THREE_VENUE_SHOW_ROWS"),
            ("show_rows", [*m.SHOWS,"2026-11-10T19:30"], "HOLD_THREE_VENUE_SHOW_ROWS"),
            ("ticket_title", m.VENUE_TITLE, "HOLD_VENUE_TICKET_TITLE"),
            ("ticket_venue", "臺北市政大樓親子劇場", "HOLD_VENUE_TICKET_TITLE"),
            ("ticket_is_multivenue", False, "HOLD_MULTIVENUE_EVENT_SCOPE"),
            ("ticket_venue_count", 1, "HOLD_MULTIVENUE_EVENT_SCOPE")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], d)
    def test_weekday_conflicts_fail_closed(self):
        for k, v, d in [
            ("weekday_conflicts", [["2026-11-10","二"]], "HOLD_WEEKDAY_EVIDENCE"),
            ("quarantine_weekday_mismatches", False, "HOLD_WEEKDAY_QUARANTINE"),
            ("bulk_accept_all_bulletin_rows", True, "HOLD_WEEKDAY_QUARANTINE"),
            ("ticket_show_rows_verified", True, "HOLD_TICKET_SHOW_NOT_VERIFIED")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], d)
    def test_no_session_inventory_or_cross_venue_promotion(self):
        for k, v in [("ticket_session_ids", ["guessed"]), ("inventory", 1),
                     ("checkout", m.TICKET), ("published_event", True),
                     ("other_venue_as_same_session", True)]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], "HOLD_UNVERIFIED_SESSION_OR_CROSS_VENUE")
    def test_bad_observation(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_VENUE_LIST")

if __name__ == "__main__":
    unittest.main()

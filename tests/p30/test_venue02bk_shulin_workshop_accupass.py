"""P30-VENUE-02BK source-bound Shulin→ACCUPASS workshop role guard."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02bk_shulin_workshop_accupass.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return dict(list_url=m.LIST, list_detail_href=m.DETAIL, detail_url=m.DETAIL,
                bulletin_sid=m.BULLETIN_SID, bulletin_date="2026-09-30",
                venue_ticket_href=m.TICKET, ticket_event_url=m.TICKET,
                ticket_event_id="2609151410103172453460",
                venue_title=m.TITLE, ticket_title=m.TITLE, venue=m.VENUE,
                venue_occurrences=list(m.OCCURRENCES), ticket_occurrences=list(m.OCCURRENCES),
                fee_amount=100, fee_unit="one_parent_child_pair",
                bulletin_date_is_show=False, festival_range_is_one_show=False,
                ticket_event_is_session=False, ticket_session_ids=None,
                inventory=None, checkout=None, published_event=None,
                cross_event_id=None, other_workshop_as_same_event=None)

class ShulinGate(unittest.TestCase):
    def inspect(self, field=None, value=None):
        x = fixture()
        if field is not None:
            x[field] = value
        return m.inspect(x, "2026-11-01")

    def test_candidate_provenance_review_only(self):
        y = self.inspect()
        self.assertEqual(y["decision"], "REVIEW_SHULIN_WORKSHOP_HOLD_TICKET_SESSIONS")
        self.assertEqual(len(y["candidateFields"]), 6)
        self.assertEqual(y["acceptedFields"], 0)
        self.assertEqual(y["ticketSessionIdsVerified"], 0)
        self.assertFalse(y["published"])
        self.assertEqual({c["source"] for c in y["candidateFields"]}, {"NTPC_SHULIN_OFFICIAL", "ACCUPASS_02"})
        self.assertTrue(all(c["decision"] == "REVIEW" and c["observed_at"] == "2026-11-01" for c in y["candidateFields"]))

    def test_source_list_detail_and_direct_ticket_identity(self):
        for k, v, expected in [
            ("list_url", m.LIST+"#fake", "HOLD_SHULIN_LIST"),
            ("list_detail_href", m.DETAIL+"?other=1", "HOLD_SAME_SOURCE_DETAIL"),
            ("detail_url", "https://evil.example/shulin", "HOLD_SAME_SOURCE_DETAIL"),
            ("bulletin_sid", "other", "HOLD_BULLETIN_ID_OR_PUBLISH_DATE"),
            ("bulletin_date", "2026-11-21", "HOLD_BULLETIN_ID_OR_PUBLISH_DATE"),
            ("venue_ticket_href", "https://www.accupass.com.evil.test/event/2609151410103172453460", "HOLD_DIRECT_ACCUPASS_EDGE"),
            ("ticket_event_url", m.TICKET+"?fake=1", "HOLD_DIRECT_ACCUPASS_EDGE"),
            ("ticket_event_id", "another", "HOLD_TICKET_EVENT_ID"),
            ("venue_title", "other", "HOLD_TITLE_OR_VENUE"),
            ("ticket_title", "other", "HOLD_TITLE_OR_VENUE"),
            ("venue", "other hall", "HOLD_TITLE_OR_VENUE"),
        ]:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k, v)["decision"], expected)

    def test_two_occurrences_and_fee_unit(self):
        for k, v, expected in [
            ("venue_occurrences", list(m.OCCURRENCES[:1]), "HOLD_TWO_OCCURRENCE_PARITY"),
            ("ticket_occurrences", [m.OCCURRENCES[0], "2026-11-23T10:30/11:30"], "HOLD_TWO_OCCURRENCE_PARITY"),
            ("fee_amount", 200, "HOLD_FEE_PER_PAIR_NOT_PERSON"),
            ("fee_unit", "per_person", "HOLD_FEE_PER_PAIR_NOT_PERSON"),
        ]:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k, v)["decision"], expected)

    def test_date_and_id_role_guards(self):
        for k in ("bulletin_date_is_show", "festival_range_is_one_show", "ticket_event_is_session"):
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k, True)["decision"], "HOLD_DATE_AND_ID_ROLES")

    def test_no_fabricated_ticket_sessions_or_cross_event(self):
        for k, v in [("ticket_session_ids", ["guessed"]), ("inventory", 10),
                     ("checkout", m.TICKET), ("published_event", True),
                     ("cross_event_id", "another"), ("other_workshop_as_same_event", True)]:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k, v)["decision"], "HOLD_UNVERIFIED_SESSION_OR_CROSS_EVENT")

    def test_invalid_observation(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_SHULIN_LIST")

if __name__ == "__main__":
    unittest.main()

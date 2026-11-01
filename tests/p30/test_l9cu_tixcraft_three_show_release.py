"""P30-L9-CU exact source identity, date roles and fail-closed negatives."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cu_tixcraft_three_show_release.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return dict(detail_url=m.DETAIL, game_url=m.GAME,
                detail_activity_id="26_aftp", game_activity_id="26_aftp",
                detail_title=m.TITLE, game_title=m.TITLE,
                game_show_rows=list(m.SHOWS), release_at=m.RELEASE,
                release_is_show=False, descriptive_prices=list(m.PRICES),
                accessible_price=400, accessible_is_general=False,
                price_is_inventory=False, ticket_session_ids=None,
                inventory=None, checkout=None, published_event=None,
                game_response_private=None)

class Gate(unittest.TestCase):
    def check(self, k=None, v=None):
        x = fixture()
        if k is not None:
            x[k] = v
        return m.inspect(x, "2026-11-01")
    def test_review_only(self):
        y = self.check()
        self.assertEqual(y["decision"], "REVIEW_TIXCRAFT_THREE_SHOWS_RELEASE_HOLD_SESSIONS")
        self.assertEqual(len(y["candidateFields"]), 5)
        self.assertEqual({z["role"] for z in y["candidateFields"]},
                         {"EVENT_NOT_SESSION", "THREE_PERFORMANCES",
                          "RELEASE_NOT_SHOW", "PRICE_BANDS_NOT_INVENTORY",
                          "ELIGIBILITY_ONLY_NOT_GENERAL"})
        self.assertTrue(all(z["decision"] == "REVIEW" and z["source"] == "TIXCRAFT_03"
                            for z in y["candidateFields"]))
        self.assertEqual(y["acceptedFields"], 0)
        self.assertEqual(y["ticketSessionIdsVerified"], 0)
        self.assertFalse(y["published"])
    def test_strict_url_identity(self):
        for k, v, d in [
            ("detail_url", m.DETAIL + "#buy", "HOLD_DETAIL_URL"),
            ("game_url", "https://tixcraft.com.evil.test/activity/game/26_aftp", "HOLD_GAME_URL"),
            ("game_activity_id", "26_other", "HOLD_SAME_ACTIVITY_ID"),
            ("detail_title", "unmatched", "HOLD_TITLE_PARITY")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], d)
    def test_three_shows_and_release(self):
        for k, v, d in [
            ("game_show_rows", list(m.SHOWS[:2]), "HOLD_THREE_DISTINCT_SHOW_ROWS"),
            ("game_show_rows", [*m.SHOWS, m.RELEASE], "HOLD_THREE_DISTINCT_SHOW_ROWS"),
            ("release_at", m.SHOWS[0], "HOLD_RELEASE_NOT_SHOW"),
            ("release_is_show", True, "HOLD_RELEASE_NOT_SHOW"),
            ("descriptive_prices", [400], "HOLD_PRICE_SCOPE"),
            ("accessible_is_general", True, "HOLD_PRICE_ELIGIBILITY_OR_INVENTORY"),
            ("price_is_inventory", True, "HOLD_PRICE_ELIGIBILITY_OR_INVENTORY")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], d)
    def test_no_ticket_session_promotion(self):
        for k, v in [("ticket_session_ids", ["guessed"]), ("inventory", 1),
                     ("checkout", m.GAME), ("published_event", True),
                     ("game_response_private", "raw")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], "HOLD_UNVERIFIED_TICKET_SESSION")
    def test_invalid_observation(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_DETAIL_URL")

if __name__ == "__main__":
    unittest.main()

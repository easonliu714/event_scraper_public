"""P30-L9-CR source-bound iNDIEVOX #18 negative contract tests."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cr_indievox_game_refund.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"list_url": m.LIST, "list_detail_href": m.DETAIL,
            "detail_url": m.DETAIL, "detail_game_href": m.GAME, "game_url": m.GAME,
            "event_path_id": "26_iv04215c4", "list_title": m.TITLE,
            "detail_title": m.TITLE, "game_title": m.TITLE,
            "detail_show": m.SHOW, "game_row_show": m.SHOW,
            "detail_venue": "LIVE WAREHOUSE 小庫", "game_row_venue": "LIVE WAREHOUSE",
            "refund_deadline": m.REFUND_CUTOFF, "refund_is_showtime": False,
            "pickup_fee_ibon": 30, "pickup_fee_e_ticket": 10,
            "fees_are_ticket_prices": False, "game_button_is_availability": False,
            "ticket_session_id": None, "ticket_session_price": None, "inventory": None,
            "checkout_url": None, "published_event": None}

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None: x[key] = value
        return m.inspect(x, "2026-11-01")
    def reject(self, decision, key, value):
        r = self.check(key, value)
        self.assertEqual(r["decision"], decision)
        self.assertEqual(r["acceptedFields"], 0)
        self.assertFalse(r["published"])
    def test_review(self):
        r = self.check()
        self.assertEqual(r["decision"], "REVIEW_SAME_ID_GAME_ROW_REFUND_ROLE_HOLD_TICKET_SESSION")
        self.assertEqual(len(r["candidateFields"]), 4)
        self.assertEqual({f["source"] for f in r["candidateFields"]}, {"INDIEVOX_18"})
        self.assertTrue(all(f["decision"] == "REVIEW" and f["observed_at"] == "2026-11-01" for f in r["candidateFields"]))
        self.assertEqual(r["ticketSessionIdsVerified"], 0)
    def test_observation(self): self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
    def test_missing(self): self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_CANONICAL_LIST")
    def test_list_host(self): self.reject("HOLD_CANONICAL_LIST", "list_url", "https://evil.example/activity")
    def test_list_query(self): self.reject("HOLD_CANONICAL_LIST", "list_url", m.LIST + "?p=2")
    def test_list_detail(self): self.reject("HOLD_LIST_TO_DETAIL_LINK", "list_detail_href", m.DETAIL + "#fake")
    def test_detail_id(self): self.reject("HOLD_LIST_TO_DETAIL_LINK", "detail_url", m.DETAIL.replace("04215c4", "0424581"))
    def test_game_href(self): self.reject("HOLD_DETAIL_TO_GAME_LINK", "detail_game_href", m.GAME + "?session=1")
    def test_game_host(self): self.reject("HOLD_DETAIL_TO_GAME_LINK", "game_url", m.GAME.replace("www.indievox.com", "evil.example"))
    def test_id(self): self.reject("HOLD_SAME_ID_TITLE_PARITY", "event_path_id", "26_iv0424581")
    def test_list_title(self): self.reject("HOLD_SAME_ID_TITLE_PARITY", "list_title", "different")
    def test_detail_title(self): self.reject("HOLD_SAME_ID_TITLE_PARITY", "detail_title", "different")
    def test_game_title(self): self.reject("HOLD_SAME_ID_TITLE_PARITY", "game_title", "different")
    def test_show(self): self.reject("HOLD_SHOWTIME_VENUE_LOCAL_PARITY", "game_row_show", "2026-11-08T18:30")
    def test_venue(self): self.reject("HOLD_SHOWTIME_VENUE_LOCAL_PARITY", "game_row_venue", "another")
    def test_refund(self): self.reject("HOLD_REFUND_DATE_ROLE", "refund_deadline", m.SHOW)
    def test_refund_as_show(self): self.reject("HOLD_REFUND_DATE_ROLE", "refund_is_showtime", True)
    def test_fee(self): self.reject("HOLD_PICKUP_FEE_ROLE", "pickup_fee_ibon", 800)
    def test_fee_as_price(self): self.reject("HOLD_PICKUP_FEE_ROLE", "fees_are_ticket_prices", True)
    def test_button(self): self.reject("HOLD_GAME_BUTTON_ROLE", "game_button_is_availability", True)
    def test_session_id(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_id", "26_iv04215c4")
    def test_session_price(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_price", 800)
    def test_inventory(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "inventory", 10)
    def test_checkout(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "checkout_url", m.GAME)
    def test_publish(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "published_event", True)

if __name__ == "__main__":
    unittest.main()

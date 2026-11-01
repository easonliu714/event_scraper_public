"""P30-L9-CS strict official-source candidate semantics, no ticket session promotion."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cs_indievox_bridge_dog_roles.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return dict(list_url=m.LIST, list_detail_href=m.DETAIL, detail_url=m.DETAIL,
                detail_game_href=m.GAME, game_url=m.GAME, event_path_id="26_iv0425761",
                list_title=m.TITLE, detail_title=m.TITLE, game_title=m.TITLE,
                detail_show=m.SHOW, game_show=m.SHOW,
                detail_venue=m.VENUE, game_venue="野地方",
                admission_open=m.ADMISSION, admission_is_show=False,
                presale_price=1250, door_price=1500, door_price_is_inventory=False,
                sale_start=m.SALE_START, sale_is_show=False,
                refund_deadline=m.REFUND, refund_is_show=False,
                presale_end_exact=None, door_sales_guaranteed=False,
                game_button_is_inventory=False, ticket_session_id=None,
                ticket_inventory=None, verified_checkout_url=None, published_event=None)

class Gate(unittest.TestCase):
    def inspect(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def test_review_with_provenance(self):
        r = self.inspect()
        self.assertEqual(r["decision"], "REVIEW_BRIDGE_DOG_PRICE_ADMISSION_SALE_REFUND_HOLD_SESSION")
        self.assertEqual(len(r["candidateFields"]), 6)
        self.assertEqual({v["source"] for v in r["candidateFields"]}, {"INDIEVOX_18"})
        self.assertEqual({v["observed_at"] for v in r["candidateFields"]}, {"2026-11-01"})
        self.assertEqual({v["decision"] for v in r["candidateFields"]}, {"REVIEW"})
        self.assertEqual(r["acceptedFields"], 0)
        self.assertEqual(r["ticketSessionIdsVerified"], 0)
        self.assertFalse(r["published"])
    def test_observation_and_missing(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_CANONICAL_LIST")
    def test_source_identity_fail_closed(self):
        cases = [
            ("list_url", m.LIST+"?page=2", "HOLD_CANONICAL_LIST"),
            ("list_detail_href", m.DETAIL+"#foo", "HOLD_LIST_DETAIL_ID"),
            ("detail_url", m.DETAIL.replace("0425761", "04215c4"), "HOLD_LIST_DETAIL_ID"),
            ("detail_game_href", m.GAME+"?session=1", "HOLD_DETAIL_GAME_ID"),
            ("game_url", m.GAME.replace("www.indievox.com", "evil.example"), "HOLD_DETAIL_GAME_ID"),
            ("event_path_id", "26_iv04215c4", "HOLD_SAME_ID_TITLE"),
            ("list_title", "another", "HOLD_SAME_ID_TITLE"),
            ("detail_title", "another", "HOLD_SAME_ID_TITLE"),
            ("game_title", "another", "HOLD_SAME_ID_TITLE"),
        ]
        for k, v, expected in cases:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k,v)["decision"], expected)
    def test_show_admission_and_prices(self):
        cases = [
            ("game_show", "2026-11-12T19:00", "HOLD_GAME_SHOW_VENUE"),
            ("game_venue", "野地方 2F", "HOLD_GAME_SHOW_VENUE"),
            ("admission_open", m.SHOW, "HOLD_ADMISSION_SHOW_ROLE"),
            ("admission_is_show", True, "HOLD_ADMISSION_SHOW_ROLE"),
            ("presale_price", 1500, "HOLD_PRESALE_DOOR_PRICE_ROLE"),
            ("door_price", 1250, "HOLD_PRESALE_DOOR_PRICE_ROLE"),
            ("door_price_is_inventory", True, "HOLD_PRESALE_DOOR_PRICE_ROLE"),
        ]
        for k,v,expected in cases:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k,v)["decision"], expected)
    def test_sale_refund_policy(self):
        cases = [
            ("sale_start", m.SHOW, "HOLD_SALE_ROLE"),
            ("sale_is_show", True, "HOLD_SALE_ROLE"),
            ("refund_deadline", "2026-11-12", "HOLD_REFUND_ROLE"),
            ("refund_is_show", True, "HOLD_REFUND_ROLE"),
            ("presale_end_exact", "2026-11-11T23:59", "HOLD_CONDITIONAL_SALE_POLICY"),
            ("door_sales_guaranteed", True, "HOLD_CONDITIONAL_SALE_POLICY"),
            ("game_button_is_inventory", True, "HOLD_GAME_BUTTON_ROLE"),
        ]
        for k,v,expected in cases:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k,v)["decision"], expected)
    def test_unverified_ticket_promotions(self):
        for k,v in (("ticket_session_id", "26_iv0425761"), ("ticket_inventory", 10),
                    ("verified_checkout_url", m.GAME), ("published_event", True)):
            with self.subTest(k=k):
                r = self.inspect(k,v)
                self.assertEqual(r["decision"], "HOLD_UNVERIFIED_TICKET_SESSION")
                self.assertEqual(r["acceptedFields"], 0)
                self.assertFalse(r["published"])

if __name__ == "__main__":
    unittest.main()

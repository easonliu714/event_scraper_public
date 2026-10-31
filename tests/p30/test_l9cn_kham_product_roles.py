"""P30-L9-CN KHAM #04 field role and same-product fail-closed regression."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cn_kham_product_roles.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"detail_url": m.DETAIL, "order_url": m.ORDER, "title": m.TITLE,
            "product_id": "P1FRRCZ9", "show_datetime": m.SHOW, "sale_start": m.SALE,
            "venue": m.VENUE, "price_tiers": m.TIERS,
            "sale_start_role": "TICKET_SALE_START_NOT_PERFORMANCE",
            "price_role": "PRODUCT_ROW_TIERS_NOT_VERIFIED_SESSION_PRICE",
            "order_button_present": True, "direct_detail_to_order_href_verified": False,
            "ticket_session_id": None, "inventory": None, "available_for_purchase": None,
            "confirmed_ticket_session_price": None, "canonical_published_event_id": None}

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def reject(self, expected, key, value):
        result = self.check(key, value)
        self.assertEqual(result["decision"], expected)
        self.assertEqual(result["acceptedFields"], 0)
        self.assertFalse(result["published"])
    def test_source_bound_review(self):
        result = self.check()
        self.assertEqual(result["decision"], "REVIEW_PRODUCT_FIELDS_HOLD_SESSION_AND_DIRECT_LINK")
        self.assertEqual(len(result["candidateFields"]), 5)
        self.assertTrue(all(f["decision"] == "REVIEW" for f in result["candidateFields"]))
    def test_observed_at(self):
        self.assertEqual(m.inspect(fixture(), "not-a-date")["decision"], "HOLD_OBSERVATION")
    def test_detail_host(self): self.reject("HOLD_KHAM_DETAIL_ID", "detail_url", "https://evil.example/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1FRRCZ9")
    def test_detail_duplicate_id(self): self.reject("HOLD_KHAM_DETAIL_ID", "detail_url", m.DETAIL + "&PRODUCT_ID=P1FRRCZ9")
    def test_detail_fragment(self): self.reject("HOLD_KHAM_DETAIL_ID", "detail_url", m.DETAIL + "#other")
    def test_order_product_mismatch(self): self.reject("HOLD_KHAM_ORDER_ID", "order_url", m.ORDER.replace("P1FRRCZ9", "OTHER"))
    def test_order_path_mismatch(self): self.reject("HOLD_KHAM_ORDER_ID", "order_url", m.DETAIL)
    def test_title(self): self.reject("HOLD_PRODUCT_TITLE_ID", "title", "another show")
    def test_product_id(self): self.reject("HOLD_PRODUCT_TITLE_ID", "product_id", "P0000000")
    def test_show_date(self): self.reject("HOLD_SHOW_DATE_VENUE_ROLE", "show_datetime", m.SALE)
    def test_venue(self): self.reject("HOLD_SHOW_DATE_VENUE_ROLE", "venue", "unknown")
    def test_sale_date(self): self.reject("HOLD_SALE_DATE_ROLE", "sale_start", m.SHOW)
    def test_sale_role(self): self.reject("HOLD_SALE_DATE_ROLE", "sale_start_role", "PERFORMANCE")
    def test_price_tiers(self): self.reject("HOLD_PRICE_ROLE", "price_tiers", (3280, 3880))
    def test_price_role(self): self.reject("HOLD_PRICE_ROLE", "price_role", "VERIFIED_SESSION_PRICE")
    def test_button(self): self.reject("HOLD_ORDER_LINK_UNVERIFIED", "order_button_present", False)
    def test_direct_href(self): self.reject("HOLD_ORDER_LINK_UNVERIFIED", "direct_detail_to_order_href_verified", True)
    def test_session(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "ticket_session_id", "P1FRRCZ9")
    def test_inventory(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "inventory", 200)
    def test_sale_status(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "available_for_purchase", True)
    def test_session_price(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "confirmed_ticket_session_price", 3280)
    def test_publication(self): self.reject("HOLD_UNVERIFIED_PROMOTION", "canonical_published_event_id", "123")

if __name__ == "__main__":
    unittest.main()

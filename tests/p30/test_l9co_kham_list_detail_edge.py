"""P30-L9-CO: KHAM observed category list direct product link negative gates."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9co_kham_list_detail_edge.py"
spec = importlib.util.spec_from_file_location("gate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"list_url": m.LIST, "list_detail_href": m.DETAIL, "detail_url": m.DETAIL,
            "order_url": m.ORDER, "list_title": m.TITLE, "detail_title": m.TITLE,
            "product_id": "P1FRRCZ9", "purchase_button_present": True,
            "purchase_button_href": None, "ticket_session_id": None, "session_price": None,
            "inventory": None, "canonical_event_id": None, "published_event": None}

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def reject(self, expected, key, value):
        out = self.check(key, value)
        self.assertEqual(out["decision"], expected)
        self.assertEqual(out["acceptedFields"], 0)
        self.assertFalse(out["published"])
    def test_list_to_detail_review(self):
        x = self.check()
        self.assertEqual(x["decision"], "REVIEW_LIST_TO_PRODUCT_DETAIL_HOLD_TICKET_SESSION")
        self.assertEqual(len(x["candidateFields"]), 2)
        self.assertEqual(x["candidateFields"][0]["value"], m.DETAIL)
        self.assertEqual(x["provenance"][1]["decision"], "HOLD_BUTTON_HREF_UNVERIFIED")
        self.assertEqual(x["provenance"][0]["role"], "PUBLIC_PARTNER_CHANNEL_CATEGORY_LIST_NOT_GENERAL_INDEX")
    def test_observed_at(self):
        self.assertEqual(m.inspect(fixture(), "wrong")["decision"], "HOLD_OBSERVATION")
    def test_missing_object(self):
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_LIST_URL")
    def test_list_host(self): self.reject("HOLD_LIST_URL", "list_url", m.LIST.replace("kham.com.tw", "evil.example"))
    def test_list_query(self): self.reject("HOLD_LIST_URL", "list_url", m.LIST + "&TYPE=1")
    def test_list_fragment(self): self.reject("HOLD_LIST_URL", "list_url", m.LIST + "#top")
    def test_list_detail_other_id(self): self.reject("HOLD_LIST_DETAIL_HREF", "list_detail_href", m.DETAIL.replace("P1FRRCZ9", "OTHER"))
    def test_list_detail_query_duplicate(self): self.reject("HOLD_LIST_DETAIL_HREF", "list_detail_href", m.DETAIL + "&PRODUCT_ID=P1FRRCZ9")
    def test_list_detail_external(self): self.reject("HOLD_LIST_DETAIL_HREF", "list_detail_href", m.DETAIL.replace("kham.com.tw", "evil.example"))
    def test_detail_mismatch(self): self.reject("HOLD_DETAIL_URL", "detail_url", m.ORDER)
    def test_order_mismatch(self): self.reject("HOLD_ORDER_URL", "order_url", m.DETAIL)
    def test_list_title(self): self.reject("HOLD_LIST_DETAIL_TITLE_IDENTITY", "list_title", "different event")
    def test_detail_title(self): self.reject("HOLD_LIST_DETAIL_TITLE_IDENTITY", "detail_title", "different event")
    def test_product_id(self): self.reject("HOLD_LIST_DETAIL_TITLE_IDENTITY", "product_id", "P0000")
    def test_button_missing(self): self.reject("HOLD_BUTTON_HREF_UNVERIFIED", "purchase_button_present", False)
    def test_button_unverified_link(self): self.reject("HOLD_BUTTON_HREF_UNVERIFIED", "purchase_button_href", m.ORDER)
    def test_session(self): self.reject("HOLD_UNVERIFIED_SESSION_OR_PUBLICATION", "ticket_session_id", "P1FRRCZ9")
    def test_session_price(self): self.reject("HOLD_UNVERIFIED_SESSION_OR_PUBLICATION", "session_price", 3280)
    def test_inventory(self): self.reject("HOLD_UNVERIFIED_SESSION_OR_PUBLICATION", "inventory", 100)
    def test_publish(self): self.reject("HOLD_UNVERIFIED_SESSION_OR_PUBLICATION", "published_event", True)

if __name__ == "__main__":
    unittest.main()

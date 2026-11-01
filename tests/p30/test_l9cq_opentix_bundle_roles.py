"""P30-L9-CQ fail-closed source identity, package role and sale boundary tests."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cq_opentix_bundle_roles.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"event_url": m.EVENT, "event_title": m.TITLE, "event_id": "2087017782302437377",
            "package20_href": m.PACKAGE20, "package20_detail": m.PACKAGE20,
            "package50_href": m.PACKAGE50, "package50_detail": m.PACKAGE50,
            "package20_threshold": 20, "package20_discount": 75,
            "package50_threshold": 50, "package50_discount": 70,
            "event_page_sale_start": m.SALE_START, "event_page_sale_end": m.SALE_END,
            "package_is_ticket_session": False, "sale_window_is_showtime": False,
            "ticket_session_id": None, "ticket_session_price": None,
            "inventory": None, "published_event": None, "ticket_button_href": None}

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def reject(self, reason, key, value):
        r = self.check(key, value)
        self.assertEqual(r["decision"], reason)
        self.assertEqual(r["acceptedFields"], 0)
        self.assertFalse(r["published"])
    def test_review(self):
        r = self.check()
        self.assertEqual(r["decision"], "REVIEW_EVENT_AND_TWO_PACKAGE_IDS_HOLD_TICKET_SESSIONS")
        self.assertEqual(len(r["candidateFields"]), 4)
        self.assertEqual({f["role"] for f in r["candidateFields"]}, {
            "EVENT_ID_NOT_SESSION", "PACKAGE_20_NOT_EVENT_OR_SESSION",
            "PACKAGE_50_NOT_EVENT_OR_SESSION", "EVENT_PAGE_PACKAGE_SALE_NOT_SHOWTIME"})
        self.assertEqual(len({f["source_url"] for f in r["candidateFields"]}), 3)
        self.assertTrue(all(f["decision"] == "REVIEW" for f in r["candidateFields"]))
    def test_bad_date(self):
        self.assertEqual(m.inspect(fixture(), "invalid")["decision"], "HOLD_OBSERVATION")
    def test_bad_object(self):
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_CANONICAL_EVENT_URL")
    def test_event_host(self): self.reject("HOLD_CANONICAL_EVENT_URL", "event_url", m.EVENT.replace("www.opentix.life", "evil.example"))
    def test_event_id(self): self.reject("HOLD_EVENT_ID_TITLE", "event_id", "2095777341620084737")
    def test_event_title(self): self.reject("HOLD_EVENT_ID_TITLE", "event_title", "different")
    def test_package20_url(self): self.reject("HOLD_TWO_DISTINCT_DIRECT_PACKAGE_LINKS", "package20_href", m.PACKAGE50)
    def test_package50_url(self): self.reject("HOLD_TWO_DISTINCT_DIRECT_PACKAGE_LINKS", "package50_detail", m.PACKAGE50 + "#session")
    def test_package_query(self): self.reject("HOLD_TWO_DISTINCT_DIRECT_PACKAGE_LINKS", "package20_detail", m.PACKAGE20 + "?id=1")
    def test_threshold(self): self.reject("HOLD_PACKAGE_THRESHOLD_DISCOUNT", "package20_threshold", 1)
    def test_discount(self): self.reject("HOLD_PACKAGE_THRESHOLD_DISCOUNT", "package50_discount", 75)
    def test_sale_start(self): self.reject("HOLD_EVENT_PAGE_SALE_ROLE", "event_page_sale_start", "2026-11-14")
    def test_sale_end(self): self.reject("HOLD_EVENT_PAGE_SALE_ROLE", "event_page_sale_end", "2026-11-15")
    def test_package_as_session(self): self.reject("HOLD_PACKAGE_OR_SALE_ROLE_PROMOTION", "package_is_ticket_session", True)
    def test_sale_as_show(self): self.reject("HOLD_PACKAGE_OR_SALE_ROLE_PROMOTION", "sale_window_is_showtime", True)
    def test_session_id(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_id", "2095777341620084737")
    def test_session_price(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_price", 800)
    def test_inventory(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "inventory", 20)
    def test_publish(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "published_event", True)
    def test_button(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_button_href", m.EVENT)

if __name__ == "__main__":
    unittest.main()

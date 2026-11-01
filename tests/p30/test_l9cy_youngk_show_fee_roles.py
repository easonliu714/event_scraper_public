"""P30-L9-CY observed first-party tixCraft LIST/detail role regression."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cy_youngk_show_fee_roles.py"
spec = importlib.util.spec_from_file_location("youngk", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return dict(list_url=m.LIST, list_title=m.TITLE, list_detail_href=m.DETAIL,
                detail_url=m.DETAIL, detail_title=m.TITLE, venue=m.VENUE,
                showtimes=list(m.SHOWS), general_prices=list(m.GENERAL),
                vip_package_prices=list(m.VIP), service_fee=200,
                service_fee_role="ADDITIONAL_PER_TICKET",
                original_general_sale="2026-08-27T11:00",
                added_show_general_sale="2026-09-01T15:00",
                added_show_date="2026-11-28",
                sale_is_show=False, pickup_is_show=False,
                ticket_session_id=None, inventory=None, checkout_url=None,
                published_event=None)

class YoungKGate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-02")

    def test_source_bound_review_not_formal(self):
        x = self.check()
        self.assertEqual(x["decision"], "REVIEW_YOUNGK_HOLD_TICKET_SESSION")
        self.assertEqual(len(x["candidateFields"]), 6)
        self.assertEqual(x["acceptedFields"], 0)
        self.assertEqual(x["ticketSessionIdsVerified"], 0)
        self.assertFalse(x["published"])
        self.assertTrue(all(f["source"] == "TIXCRAFT_03" and
                            f["source_url"] == m.DETAIL and
                            f["decision"] == "REVIEW" for f in x["candidateFields"]))

    def test_exact_list_detail_edge(self):
        for key, value, expected in [
            ("list_url", m.LIST+"?q=youngk", "HOLD_LIST_SOURCE"),
            ("list_title", "another", "HOLD_LIST_DETAIL_IDENTITY"),
            ("list_detail_href", "https://evil.example/activity/detail/26_youngk", "HOLD_LIST_DETAIL_IDENTITY"),
            ("detail_url", m.DETAIL+"#game", "HOLD_DETAIL_IDENTITY"),
            ("detail_title", "Young K VIP add-on", "HOLD_DETAIL_IDENTITY")]:
            with self.subTest(key=key):
                self.assertEqual(self.check(key, value)["decision"], expected)

    def test_show_and_price_categories(self):
        for key, value, expected in [
            ("venue", "Zepp New Taipei", "HOLD_TWO_SHOWS_OR_VENUE"),
            ("showtimes", [m.SHOWS[0]], "HOLD_TWO_SHOWS_OR_VENUE"),
            ("general_prices", [6880, 5880], "HOLD_PRICE_CATEGORY"),
            ("vip_package_prices", [4880, 3880], "HOLD_PRICE_CATEGORY"),
            ("service_fee", 2200, "HOLD_SERVICE_FEE_NOT_ADMISSION"),
            ("service_fee_role", "GENERAL_ADMISSION", "HOLD_SERVICE_FEE_NOT_ADMISSION")]:
            with self.subTest(key=key):
                self.assertEqual(self.check(key, value)["decision"], expected)

    def test_added_show_sale_not_showtime(self):
        for key, value, expected in [
            ("original_general_sale", "2026-09-01T15:00", "HOLD_SHOW_SPECIFIC_SALE_ROLE"),
            ("added_show_general_sale", "2026-11-28T19:00", "HOLD_SHOW_SPECIFIC_SALE_ROLE"),
            ("added_show_date", "2026-11-29", "HOLD_SHOW_SPECIFIC_SALE_ROLE"),
            ("sale_is_show", True, "HOLD_DATE_ROLE"),
            ("pickup_is_show", True, "HOLD_DATE_ROLE")]:
            with self.subTest(key=key):
                self.assertEqual(self.check(key, value)["decision"], expected)

    def test_no_fabricated_session_or_publication(self):
        for key, value in [("ticket_session_id", "26_youngk"),
                           ("inventory", 2), ("checkout_url", m.DETAIL),
                           ("published_event", True)]:
            with self.subTest(key=key):
                self.assertEqual(self.check(key, value)["decision"], "HOLD_UNVERIFIED_SESSION_OR_PUBLICATION")

    def test_invalid_observation(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-02")["decision"], "HOLD_LIST_SOURCE")

if __name__ == "__main__":
    unittest.main()

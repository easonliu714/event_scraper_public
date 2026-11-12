"""P30-VENUE-02BM source-backed Zepp rid/ibon redirect and VIP role negatives."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02bm_earendel_ibon_edge.py"
spec = importlib.util.spec_from_file_location("earendel", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return dict(venue_list=m.LIST, list_detail_href=m.DETAIL,
                venue_detail=m.DETAIL, rid="160667", title=m.TITLE,
                show=m.SHOW, venue=m.VENUE,
                ticket_href=m.VENUE_LINK, redirect_destination=m.REDIRECT,
                sale="2026-09-19T13:00", sale_is_show=False,
                vip_total=3200, vip_admission=3180, vip_benefit=20,
                vip_benefit_role="BUNDLE_COMPONENT_NOT_STANDALONE_ADMISSION",
                other_prices=[2600, 2000, 1600],
                ticket_detail_title_verified=False, ticket_detail_title=None,
                ticket_session_id=None, ticket_inventory=None,
                checkout_url=None, published_event=None,
                ticket_price_from_ibon=None)

class ZeppIbonGate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-02")

    def test_venue_source_review_not_ticket_acceptance(self):
        r = self.check()
        self.assertEqual(r["decision"], "REVIEW_ZEPP_TO_IBON_HOLD_TICKET_DETAIL_SESSION")
        self.assertEqual(len(r["candidateFields"]), 5)
        self.assertEqual(r["acceptedFields"], 0)
        self.assertEqual(r["ticketSessionIdsVerified"], 0)
        self.assertFalse(r["ticketDetailTitleVerified"])
        self.assertFalse(r["published"])
        self.assertTrue(all(x["source"] == "ZEPP_NEW_TAIPEI_OFFICIAL" and
                            x["decision"] == "REVIEW" for x in r["candidateFields"]))

    def test_exact_venue_rid_and_title(self):
        for key, value, expected in [
            ("venue_list", m.LIST+"?p=1", "HOLD_VENUE_LIST"),
            ("list_detail_href", m.DETAIL.replace("160667", "160668"), "HOLD_RID_DETAIL_EDGE"),
            ("venue_detail", m.DETAIL+"#show", "HOLD_RID_DETAIL_EDGE"),
            ("rid", "39946", "HOLD_VENUE_IDENTITY"),
            ("title", "unrelated", "HOLD_VENUE_IDENTITY"),
            ("show", "2026-09-19T13:00", "HOLD_VENUE_SHOW_ROLE"),
            ("venue", "Zepp Taipei", "HOLD_VENUE_SHOW_ROLE")]:
            with self.subTest(key=key):
                self.assertEqual(self.check(key, value)["decision"], expected)

    def test_strict_link_redirect_not_session(self):
        for key, value in [
            ("ticket_href", "https://ibontw.com/26_Earendel?session=1"),
            ("redirect_destination", "https://ticket.ibon.com.tw/ActivityInfo/Details/39961"),
            ("redirect_destination", "https://evil.example/ActivityInfo/Details/39946")]:
            with self.subTest(key=key):
                self.assertEqual(self.check(key, value)["decision"], "HOLD_TICKET_REDIRECT_CHAIN")

    def test_vip_price_split_and_sale(self):
        for key, value, expected in [
            ("sale", m.SHOW, "HOLD_SALE_NOT_SHOW"),
            ("sale_is_show", True, "HOLD_SALE_NOT_SHOW"),
            ("vip_total", 3180, "HOLD_VIP_SPLIT_AND_BENEFIT_ROLE"),
            ("vip_admission", 3200, "HOLD_VIP_SPLIT_AND_BENEFIT_ROLE"),
            ("vip_benefit", 200, "HOLD_VIP_SPLIT_AND_BENEFIT_ROLE"),
            ("vip_benefit_role", "GENERAL_ADMISSION", "HOLD_VIP_SPLIT_AND_BENEFIT_ROLE"),
            ("other_prices", [3200, 2600], "HOLD_PRICE_CATEGORIES")]:
            with self.subTest(key=key):
                self.assertEqual(self.check(key, value)["decision"], expected)

    def test_ibon_detail_not_proven(self):
        self.assertEqual(self.check("ticket_detail_title_verified", True)["decision"], "HOLD_IBON_DETAIL_UNVERIFIED")
        for key, value in [("ticket_detail_title", m.TITLE),
                           ("ticket_session_id", "39946"), ("ticket_inventory", 3),
                           ("checkout_url", m.REDIRECT), ("published_event", True),
                           ("ticket_price_from_ibon", 3200)]:
            with self.subTest(key=key):
                self.assertEqual(self.check(key, value)["decision"], "HOLD_UNVERIFIED_IBON_FIELD_OR_SESSION")

    def test_invalid_observation(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-02")["decision"], "HOLD_VENUE_LIST")

if __name__ == "__main__":
    unittest.main()

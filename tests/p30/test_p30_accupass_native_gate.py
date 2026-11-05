"""Offline fail-closed contracts; no live HTTP in tests."""
import unittest
from scripts import p30_accupass_native_gate as gate


class TestAccupassSource(unittest.TestCase):
    def setUp(self):
        self.link = "https://www.accupass.com/event/" + gate.EVENT_ID + "?utm_source=web"
        self.listing = ('<main><a href="' + self.link + '"><span>' +
                        gate.EXPECTED_TITLE + '</span></a></main>')
        self.detail = "<main><article><h1>" + gate.EXPECTED_TITLE + "</h1></article></main>"

    def test_same_id_title_review_only(self):
        out = gate.inspect_same_id(self.listing, self.detail)
        self.assertEqual(out["same_id_review"], 1)
        self.assertEqual(out["formal_accepted_fields"], 0)
        self.assertEqual(out["decision"], "REVIEW_NON_SESSION_ONLY")

    def test_no_list_id_edge_holds(self):
        self.assertEqual(gate.inspect_same_id("<main></main>", self.detail)["same_id_review"], 0)

    def test_cross_id_never_matches(self):
        wrong = self.listing.replace(gate.EVENT_ID, "2606282259461938560272")
        self.assertEqual(gate.inspect_same_id(wrong, self.detail)["same_id_review"], 0)

    def test_global_heading_cannot_establish_event_local_identity(self):
        out = gate.inspect_same_id(self.listing, "<header><h1>" + gate.EXPECTED_TITLE + "</h1></header>")
        self.assertEqual(out["first_failure"], "ACCUPASS_DETAIL_MAIN_LOCAL_EXACT_TITLE_HOLD")

    def test_wrong_title_and_duplicate_query_hold(self):
        self.assertEqual(gate.inspect_same_id(self.listing.replace("八十八石佛", "九十九石佛"),
                                              self.detail)["same_id_review"], 0)
        doubled = self.listing.replace("</main>", '<a href="' + self.link.replace(
            "utm_source=web", "utm_medium=search") + '">' + gate.EXPECTED_TITLE + "</a></main>")
        self.assertEqual(gate.inspect_same_id(doubled, self.detail)["same_id_review"], 0)

    def test_no_checkout_foreign_query_or_fragment(self):
        for url in ("https://evil.example/event/" + gate.EVENT_ID,
                    "https://www.accupass.com/event/" + gate.EVENT_ID + "/registrations/new",
                    self.link + "&session=1", self.link + "#checkout"):
            with self.subTest(url=url):
                self.assertIsNone(gate.exact_public_event_url(url))


if __name__ == "__main__":
    unittest.main()

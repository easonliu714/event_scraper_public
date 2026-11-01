"""P30-L9-CV first-party reciprocal edge, add-on role and negative controls."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9cv_tixcraft_vip_addon.py"
s = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def fixture():
    return dict(standard_url=m.STANDARD, upgrade_url=m.UPGRADE,
                standard_links_upgrade=m.UPGRADE, upgrade_links_standard=m.STANDARD,
                standard_activity_id="26_vashhsu", upgrade_activity_id="26_vashhsu_v",
                standard_title=m.TITLE, upgrade_title=m.TITLE,
                standard_show=m.SHOW, upgrade_show=m.SHOW,
                standard_venue=m.VENUE, upgrade_venue=m.VENUE,
                standard_price=1450, accessible_price=725, upgrade_price=600,
                upgrade_requires_same_show_admission=True, upgrade_valid_alone=False,
                upgrade_is_admission=False, upgrade_is_second_show=False,
                accessible_is_general=False, ticket_session_id=None, inventory=None,
                checkout=None, published_event=None, combined_ticket_price=None)

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def test_review_only_with_provenance(self):
        y = self.check()
        self.assertEqual(y["decision"], "REVIEW_TIXCRAFT_VIP_ADDON_HOLD_SESSIONS")
        self.assertEqual(len(y["candidateFields"]), 7)
        self.assertEqual(y["acceptedFields"], 0)
        self.assertEqual(y["ticketSessionIdsVerified"], 0)
        self.assertFalse(y["published"])
        self.assertTrue(all(z["source"] == "TIXCRAFT_03" and z["decision"] == "REVIEW"
                            and z["observed_at"] == "2026-11-01" for z in y["candidateFields"]))
    def test_exact_urls_and_reciprocal_edges(self):
        for k, v, d in [
            ("standard_url", m.STANDARD+"#buy", "HOLD_STANDARD_SOURCE"),
            ("upgrade_url", "https://tixcraft.com.evil.test/activity/detail/26_vashhsu_v", "HOLD_UPGRADE_SOURCE"),
            ("standard_links_upgrade", m.UPGRADE+"?foo=1", "HOLD_RECIPROCAL_FIRST_PARTY_EDGE"),
            ("upgrade_links_standard", m.UPGRADE, "HOLD_RECIPROCAL_FIRST_PARTY_EDGE"),
            ("upgrade_activity_id", "26_vashhsu", "HOLD_DISTINCT_ACTIVITY_IDENTITIES"),
            ("upgrade_title", "unrelated", "HOLD_SAME_SHOW_TITLE")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], d)
    def test_show_and_prices(self):
        for k, v, d in [
            ("upgrade_show", "2026-11-09T18:00", "HOLD_SAME_SHOW_AND_VENUE"),
            ("upgrade_venue", "Another hall", "HOLD_SAME_SHOW_AND_VENUE"),
            ("upgrade_price", 1450, "HOLD_PRICE_SCOPE"),
            ("accessible_price", 600, "HOLD_PRICE_SCOPE")]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], d)
    def test_upgrade_never_becomes_admission_or_second_show(self):
        for k, v in [("upgrade_requires_same_show_admission", False),
                     ("upgrade_valid_alone", True), ("upgrade_is_admission", True),
                     ("upgrade_is_second_show", True), ("accessible_is_general", True)]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], "HOLD_ADDON_NOT_ADMISSION")
    def test_no_guessed_ticket_or_checkout(self):
        for k, v in [("ticket_session_id", "guessed"), ("inventory", 1),
                     ("checkout", m.UPGRADE), ("published_event", True),
                     ("combined_ticket_price", 2050)]:
            with self.subTest(k=k):
                self.assertEqual(self.check(k, v)["decision"], "HOLD_UNVERIFIED_SESSION_OR_PRICE")
    def test_invalid_observation(self):
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_STANDARD_SOURCE")

if __name__ == "__main__":
    unittest.main()

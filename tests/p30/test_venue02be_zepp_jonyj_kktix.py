"""P30-VENUE-02BE strict venue→organizer provenance and role negatives."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02be_zepp_jonyj_kktix.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return {"venue_list": m.VENUE_LIST, "list_detail_href": m.VENUE_DETAIL,
            "venue_detail": m.VENUE_DETAIL, "venue_ticket_href": m.KKTIX,
            "ticket_organizer_page": m.KKTIX, "venue_title": m.VENUE_TITLE,
            "ticket_title": m.TICKET_TITLE, "venue_rid": "166457",
            "venue_show": m.SHOW, "ticket_show": m.SHOW,
            "venue_name": "Zepp New Taipei",
            "ticket_category_rows": m.CATEGORY_ROWS,
            "ticket_row_showtimes": (m.SHOW, m.SHOW),
            "category_rows_are_two_performances": False,
            "sale_start": "2026-07-27T19:00",
            "vip_eligibility_cutoff": "2026-11-01T23:59",
            "queue_time": "18:00", "entry_times": m.ENTRY_TIMES,
            "upgrade_addon": 680, "business_ticket": 3000, "bundle_price": 3680,
            "upgrade_is_separate_performance": False, "sale_is_showtime": False,
            "ticket_session_ids": None, "verified_registration_url": None,
            "session_inventory": None, "session_prices": None, "published_event": None}

class Gate(unittest.TestCase):
    def check(self, key=None, value=None):
        x = fixture()
        if key is not None: x[key] = value
        return m.inspect(x, "2026-11-01")
    def reject(self, reason, key, value):
        r = self.check(key, value)
        self.assertEqual(r["decision"], reason)
        self.assertEqual(r["acceptedFields"], 0)
        self.assertFalse(r["published"])
    def test_review(self):
        r = self.check()
        self.assertEqual(r["decision"], "REVIEW_ZEPP_TO_KKTIX_ONE_SHOW_TWO_CATEGORY_ROWS_HOLD_SESSION_IDS")
        self.assertEqual(len(r["candidateFields"]), 4)
        self.assertEqual({f["source"] for f in r["candidateFields"]}, {"KKTIX_01", "ZEPP_NEW_TAIPEI_OFFICIAL"})
        self.assertTrue(all(f["decision"] == "REVIEW" for f in r["candidateFields"]))
        self.assertEqual(r["ticketSessionIdsVerified"], 0)
    def test_observation(self): self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
    def test_missing(self): self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_VENUE_LIST")
    def test_list(self): self.reject("HOLD_VENUE_LIST", "venue_list", m.VENUE_LIST + "?rid=1")
    def test_rid(self): self.reject("HOLD_RID_DETAIL_IDENTITY", "list_detail_href", m.VENUE_DETAIL.replace("166457", "163838"))
    def test_detail_fragment(self): self.reject("HOLD_RID_DETAIL_IDENTITY", "venue_detail", m.VENUE_DETAIL + "#foo")
    def test_ticket_host(self): self.reject("HOLD_DIRECT_KKTIX_ORGANIZER_EDGE", "venue_ticket_href", m.KKTIX.replace("spaceport.kktix.cc", "evil.example"))
    def test_ticket_query(self): self.reject("HOLD_DIRECT_KKTIX_ORGANIZER_EDGE", "ticket_organizer_page", m.KKTIX + "?fake=1")
    def test_venue_title(self): self.reject("HOLD_SOURCE_LOCAL_TITLE_RID", "venue_title", "wrong")
    def test_ticket_title(self): self.reject("HOLD_SOURCE_LOCAL_TITLE_RID", "ticket_title", "wrong")
    def test_rid_value(self): self.reject("HOLD_SOURCE_LOCAL_TITLE_RID", "venue_rid", "jonyj")
    def test_venue_show(self): self.reject("HOLD_SAME_SHOWTIME_VENUE", "venue_show", "2026-11-06T18:00")
    def test_ticket_show(self): self.reject("HOLD_SAME_SHOWTIME_VENUE", "ticket_show", "2026-11-07T20:00")
    def test_venue(self): self.reject("HOLD_SAME_SHOWTIME_VENUE", "venue_name", "Zepp Tokyo")
    def test_rows(self): self.reject("HOLD_TWO_CATEGORY_ROWS_SAME_SHOW", "ticket_category_rows", ("1樓站席",))
    def test_row_time(self): self.reject("HOLD_TWO_CATEGORY_ROWS_SAME_SHOW", "ticket_row_showtimes", (m.SHOW, "2026-11-07T20:00"))
    def test_double_show(self): self.reject("HOLD_CATEGORY_ROW_ROLE", "category_rows_are_two_performances", True)
    def test_sale(self): self.reject("HOLD_SALE_VIP_QUEUE_ENTRY_ROLES", "sale_start", m.SHOW)
    def test_vip(self): self.reject("HOLD_SALE_VIP_QUEUE_ENTRY_ROLES", "vip_eligibility_cutoff", m.SHOW)
    def test_entry(self): self.reject("HOLD_SALE_VIP_QUEUE_ENTRY_ROLES", "entry_times", ("18:30",))
    def test_upgrade(self): self.reject("HOLD_UPGRADE_ADDON_BUNDLE_ROLES", "upgrade_addon", 3000)
    def test_bundle(self): self.reject("HOLD_UPGRADE_ADDON_BUNDLE_ROLES", "bundle_price", 3000)
    def test_upgrade_show(self): self.reject("HOLD_ROLE_PROMOTION", "upgrade_is_separate_performance", True)
    def test_sale_show(self): self.reject("HOLD_ROLE_PROMOTION", "sale_is_showtime", True)
    def test_session(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "ticket_session_ids", ["guess"])
    def test_registration(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "verified_registration_url", m.KKTIX)
    def test_inventory(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "session_inventory", 100)
    def test_price(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "session_prices", [3000])
    def test_publish(self): self.reject("HOLD_UNVERIFIED_TICKET_SESSION", "published_event", True)

if __name__ == "__main__":
    unittest.main()

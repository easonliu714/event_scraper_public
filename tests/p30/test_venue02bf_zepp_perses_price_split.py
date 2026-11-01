"""P30-VENUE-02BF official Zepp price arithmetic, cancellation and missing href tests."""
import importlib.util
import pathlib
import unittest

p = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_venue02bf_zepp_perses_price_split.py"
spec = importlib.util.spec_from_file_location("gate", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    return dict(schedule_list=m.LIST, perses_list_href=m.PERSES, perses_detail=m.PERSES,
                akasaki_list_href=m.CANCELLED, akasaki_detail=m.CANCELLED,
                perses_rid="169301", akasaki_rid="160673",
                perses_title=m.TITLE, akasaki_title=m.CANCELLED_TITLE,
                perses_show=m.SHOW, akasaki_show=m.SHOW,
                akasaki_cancelled=True, perses_cancelled=False,
                price_components=m.TIERS, accessible_price=2490,
                accessible_equivalence=4980, sale_start="2026-10-17T12:00",
                sale_is_show=False, claimed_platform="KKTIX",
                ticket_href_text="Link in Bio", verified_kktix_url=None,
                ticket_session_id=None, inventory=None, ticket_price_verified=None,
                published_event=None)

class Gate(unittest.TestCase):
    def inspect(self, key=None, value=None):
        x = fixture()
        if key is not None:
            x[key] = value
        return m.inspect(x, "2026-11-01")
    def test_review_price_provenance(self):
        r = self.inspect()
        self.assertEqual(r["decision"], "REVIEW_PERSES_PRICE_SPLIT_CANCELLED_OTHER_RID_HOLD_KKTIX_URL")
        self.assertEqual(len(r["candidateFields"]), 6)
        self.assertTrue(all(v["decision"] == "REVIEW" and v["source"] == "ZEPP_NEW_TAIPEI_OFFICIAL" for v in r["candidateFields"]))
        self.assertTrue(all(v["observed_at"] == "2026-11-01" for v in r["candidateFields"]))
        self.assertEqual(r["acceptedFields"], 0)
        self.assertEqual(r["ticketSessionIdsVerified"], 0)
        self.assertFalse(r["published"])
    def test_missing_and_observation(self):
        self.assertEqual(m.inspect(None, "2026-11-01")["decision"], "HOLD_OFFICIAL_SCHEDULE_LIST")
        self.assertEqual(m.inspect(fixture(), "bad")["decision"], "HOLD_OBSERVATION")
    def test_source_links_and_rid(self):
        cases = [
            ("schedule_list", m.LIST+"?m=11", "HOLD_OFFICIAL_SCHEDULE_LIST"),
            ("perses_list_href", m.PERSES.replace("169301", "160673"), "HOLD_PERSES_RID"),
            ("perses_detail", m.PERSES+"#foo", "HOLD_PERSES_RID"),
            ("akasaki_list_href", m.CANCELLED.replace("160673", "169301"), "HOLD_CANCELLED_RID"),
            ("akasaki_detail", m.CANCELLED.replace("www.zepp.co.jp", "evil.example"), "HOLD_CANCELLED_RID"),
            ("perses_rid", "160673", "HOLD_DISTINCT_RID_TITLE"),
            ("akasaki_rid", "169301", "HOLD_DISTINCT_RID_TITLE"),
            ("perses_title", m.CANCELLED_TITLE, "HOLD_DISTINCT_RID_TITLE"),
            ("akasaki_title", m.TITLE, "HOLD_DISTINCT_RID_TITLE"),
        ]
        for k,v,expected in cases:
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k,v)["decision"], expected)
    def test_same_day_is_not_same_event(self):
        for k,v,expected in (
            ("perses_show", "2026-11-27T18:00", "HOLD_SAME_DAY_DIFFERENT_EVENT"),
            ("akasaki_show", "2026-11-29T18:00", "HOLD_SAME_DAY_DIFFERENT_EVENT"),
            ("akasaki_cancelled", False, "HOLD_CANCELLATION_SCOPE"),
            ("perses_cancelled", True, "HOLD_CANCELLATION_SCOPE"),
        ):
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k,v)["decision"], expected)
    def test_price_split_and_eligibility(self):
        for k,v,expected in (
            ("price_components", (("SVIP", 7980, 7980, 0),), "HOLD_PRICE_COMPONENTS"),
            ("price_components", None, "HOLD_PRICE_COMPONENTS"),
            ("accessible_price", 4980, "HOLD_ACCESSIBLE_ELIGIBILITY"),
            ("accessible_equivalence", 2490, "HOLD_ACCESSIBLE_ELIGIBILITY"),
            ("sale_start", m.SHOW, "HOLD_SALE_ROLE"),
            ("sale_is_show", True, "HOLD_SALE_ROLE"),
        ):
            with self.subTest(k=k):
                self.assertEqual(self.inspect(k,v)["decision"], expected)
    def test_claimed_platform_is_not_ticket_url(self):
        for k,v,expected in (
            ("claimed_platform", "Tixcraft", "HOLD_CLAIMED_PLATFORM"),
            ("ticket_href_text", "https://kktix.cc/guess", "HOLD_CLAIMED_PLATFORM"),
            ("verified_kktix_url", "https://kktix.cc/guess", "HOLD_NO_DIRECT_TICKET_EDGE"),
            ("ticket_session_id", "169301", "HOLD_NO_DIRECT_TICKET_EDGE"),
            ("inventory", 50, "HOLD_NO_DIRECT_TICKET_EDGE"),
            ("ticket_price_verified", 7980, "HOLD_NO_DIRECT_TICKET_EDGE"),
            ("published_event", True, "HOLD_NO_DIRECT_TICKET_EDGE"),
        ):
            with self.subTest(k=k):
                r=self.inspect(k,v)
                self.assertEqual(r["decision"], expected)
                self.assertEqual(r["acceptedFields"], 0)
                self.assertFalse(r["published"])

if __name__ == "__main__":
    unittest.main()

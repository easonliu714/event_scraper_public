"""Negative identity, role, source and release invariants for L9-DE."""
import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[2] / "scripts/p30_l9de_kham_tmc_edge.py"
spec = importlib.util.spec_from_file_location("l9de", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
NOW = "2026-11-02T05:55:00Z"

def sample():
    return dict(kham_detail_url=m.KHAM, venue_detail_url=m.TMC,
                venue_ticket_href=m.KHAM, kham_title=m.KHAM_TITLE,
                tmc_title=m.TMC_TITLE, kham_sale_start="2026-08-22T12:00:00+08:00",
                venue_show="2026-11-07T19:30:00+08:00",
                venue_name="臺北流行音樂中心 表演廳",
                venue_price_bands=[4280,3880,3480,2880,2480,1880])

class SourceRoles(unittest.TestCase):
    def test_review_has_exact_source_provenance(self):
        r = m.inspect(sample(), NOW)
        self.assertEqual(r["canonicalPlatformId"], "04")
        self.assertEqual(r["decision"], "REVIEW_DIRECT_PRODUCT_LINK_HOLD_SESSION_AND_PRICE_AUTHORITY")
        self.assertEqual(len(r["candidateFields"]), 6)
        self.assertEqual({x["decision"] for x in r["candidateFields"]}, {"REVIEW"})
        self.assertEqual({x["source"] for x in r["candidateFields"]}, {m.KHAM, m.TMC})
        self.assertEqual(r["acceptedFields"], 0)
        self.assertEqual(r["ticketSessionIdsVerified"], 0)
        self.assertEqual(r["goldenAccepted"], 0)
        self.assertFalse(r["published"])
        self.assertEqual(r["releaseState"], "HARD_HOLD_NO_PUBLICATION")

    def test_url_and_cross_source_identity_fail_closed(self):
        for field, value in [
            ("kham_detail_url",m.KHAM+"&PRODUCT_ID=OTHER"),
            ("kham_detail_url",m.KHAM+"#purchase"),
            ("kham_detail_url",m.KHAM.replace("https:","http:")),
            ("kham_detail_url","https://kham.com.tw.evil.example/application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1DF32E2"),
            ("venue_ticket_href","https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=WRONG"),
            ("venue_detail_url",m.TMC+"/other"),
            ("kham_title","not the same event"),
            ("tmc_title","similar but unproven")]:
            with self.subTest(field=field,value=value):
                x=sample();x[field]=value
                r=m.inspect(x,NOW)
                self.assertEqual(r["candidateFields"],[])
                self.assertTrue(r["decision"].startswith("HOLD_"))

    def test_roles_and_ambiguous_prices_fail_closed(self):
        for field, value in [
            ("kham_sale_start","2026-11-07T19:30:00+08:00"),
            ("venue_show","2026-08-22T12:00:00+08:00"),
            ("venue_price_bands",[1880]),
            ("venue_price_bands",[False,3880,3480,2880,2480,1880]),
            ("venue_name","other hall")]:
            with self.subTest(field=field):
                x=sample();x[field]=value
                self.assertEqual(m.inspect(x,NOW)["candidateFields"],[])

    def test_unverified_checkout_session_inventory_never_promoted(self):
        for field,value in [("checkout_url","https://kham.com.tw/buy"),
                            ("ticket_session_id",0),("ticket_session_id",False),
                            ("inventory",0),("inventory",False),
                            ("formal_accepted",False),("golden_accepted",True)]:
            with self.subTest(field=field):
                x=sample();x[field]=value
                r=m.inspect(x,NOW)
                self.assertEqual(r["candidateFields"],[])
                self.assertTrue(r["decision"].startswith("HOLD_UNVERIFIED_"))

    def test_observation_must_be_timezone_aware(self):
        for stamp in ["2026-11-02T13:55:00","invalid",None,0]:
            self.assertEqual(m.inspect(sample(),stamp)["decision"],"HOLD_OBSERVATION")
if __name__ == "__main__":
    unittest.main()

"""Integration tests reuse historical #217/#221 reader contracts, no HTTP."""
import copy
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import p30_venue02bo_tainex_exhibition as tainex
from scripts import p30_l9dc_famiticket_teca as fami
from scripts.p30_multisource_review_lkg import plan, write_isolated

NOW = datetime(2026, 11, 10, 5, 55, tzinfo=timezone.utc)
TAINEX_STAMP = "2026-11-02T06:57:00+08:00"
FAMI_STAMP = "2026-11-02T06:55:00+08:00"


def tainex_packet():
    obs = dict(list_url=tainex.LIST, list_detail_href=tainex.DETAIL,
               detail_url=tainex.DETAIL, list_title=tainex.TITLE,
               detail_title=tainex.TITLE, period_label="展覽活動期間",
               period_start=tainex.START, period_end=tainex.END,
               venue_label="活動地點", venue_hall=tainex.HALL,
               floors=list(tainex.FLOORS), organizer_label="主辦單位",
               organizer=tainex.ORGANIZER, external_website_label="官方網站",
               external_website=tainex.ORGANIZER_SITE)
    return {"source": "tainex", "observation": obs, "observed_at": TAINEX_STAMP}


def fami_packet():
    obs = dict(list_url=fami.LIST, list_detail_href=fami.DETAIL,
               detail_url=fami.DETAIL, list_title=fami.TITLE,
               detail_title=fami.TITLE, period_start=fami.PERIOD[0],
               period_end=fami.PERIOD[1], exhibition_hours="10:00-18:00",
               venue=fami.VENUE, prices=dict(fami.PRICES),
               purchase_control="我要購票")
    return {"source": "famiticket", "observation": obs, "observed_at": FAMI_STAMP}


class MultiSourceBridge(unittest.TestCase):
    def test_two_real_historical_source_reader_contracts_to_common_core(self):
        r = plan([tainex_packet(), fami_packet()], as_of=NOW)
        self.assertEqual(r["source_reader_qualified"], 2)
        self.assertEqual(r["source_platforms"], ["FAMITICKET", "TAINEX"])
        self.assertEqual(r["source_gates"], ["P30-L9-DC", "P30-VENUE-02BO"])
        self.assertEqual(r["new_review"], 2)
        self.assertEqual(len(r["review_rows"]), 2)
        self.assertEqual(r["independently_accepted_fields"], 0)
        self.assertEqual(r["independent_native_detail_new"], 0)
        self.assertEqual(r["native_get"], r["published_delta"])
        self.assertFalse(r["commit_permitted"])
        for row in r["review_rows"]:
            self.assertEqual(row["date"], "未確認")
            self.assertEqual(row["price"], "未確認")
            self.assertEqual(row["location"], "未確認")
            self.assertEqual(row["_candidate"]["decision"], "REVIEW_WITH_HOLD")
            self.assertFalse(row["_candidate"]["published"])
            self.assertIn("SOURCE_READER_NOT_INDEPENDENT_NATIVE_ATTESTATION",
                          row["_candidate"]["hold_reasons"])

    def test_duplicate_same_id_cannot_override_lkg(self):
        p = tainex_packet()
        r = plan([p, copy.deepcopy(p)], as_of=NOW)
        self.assertEqual(len(r["review_rows"]), 1)
        self.assertEqual(r["source_reader_qualified"], 1)
        self.assertEqual(r["new_review"], 1)
        self.assertEqual(len(r["rejected"]), 1)

    def test_prior_lkg_retained_on_source_failure(self):
        old = plan([tainex_packet()], as_of=NOW)["review_rows"]
        bad = fami_packet()
        bad["observation"]["detail_title"] = "unrelated"
        r = plan([bad], previous=old, as_of=NOW)
        self.assertEqual(r["decision"], "HOLD_NO_VALID_NEW_SOURCE")
        self.assertEqual(r["retained_lkg"], 1)
        self.assertEqual(r["review_rows"], old)
        self.assertEqual(len(r["rejected"]), 1)

    def test_source_namespace_and_role_fail_closed(self):
        for key, value in [
            ("list_detail_href", tainex.DETAIL.replace("691", "690")),
            ("period_label", "演出開始"),
            ("venue_hall", "南港展覽館2館"),
            ("ticket_session_id", "691"),
            ("admission_price", 100),
        ]:
            p = tainex_packet()
            p["observation"][key] = value
            r = plan([p], as_of=NOW)
            self.assertEqual(r["source_reader_qualified"], 0, key)
            self.assertEqual(len(r["rejected"]), 1, key)

    def test_famiticket_presale_not_general_minimum(self):
        for key, value in [
            ("list_detail_href", fami.DETAIL + "#bad"),
            ("prices", {"presale_single_day": 150}),
            ("general_admission_price", 150),
            ("ticket_session_id", "fake"),
        ]:
            p = fami_packet()
            p["observation"][key] = value
            r = plan([p], as_of=NOW)
            self.assertEqual(r["source_reader_qualified"], 0, key)

    def test_future_time_and_unregistered_source(self):
        p = tainex_packet()
        p["observed_at"] = "2026-11-11T00:00:00Z"
        self.assertEqual(plan([p], as_of=NOW)["source_reader_qualified"], 0)
        p = tainex_packet()
        p["source"] = "unknown"
        self.assertEqual(plan([p], as_of=NOW)["source_reader_qualified"], 0)

    def test_prior_lkg_tampering_is_hard_failure(self):
        old = plan([tainex_packet()], as_of=NOW)["review_rows"]
        old[0]["_candidate"]["published"] = True
        with self.assertRaisesRegex(ValueError, "PRIOR_LKG_INTEGRITY_HOLD"):
            plan([fami_packet()], previous=old, as_of=NOW)

    def test_replay_does_not_claim_native_or_field_authority(self):
        r = plan([fami_packet()], as_of=NOW)
        self.assertEqual(r["source_platforms"], ["FAMITICKET"])
        self.assertEqual(r["review_rows"][0]["_candidate"]["field_evidence"], {})
        self.assertFalse(r["cross_host_cas_attested"])
        self.assertFalse(r["formal_data_mutated"])
        self.assertFalse(r["scheduler_enabled"])

    def test_atomic_isolated_output_and_docs_forbidden(self):
        r = plan([tainex_packet(), fami_packet()], as_of=NOW)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "_isolated_review" / "multi" / "plan.json"
            digest = write_isolated(r, out, root)
            self.assertEqual(len(digest), 64)
            self.assertTrue(out.is_file())
            with self.assertRaisesRegex(ValueError, "ISOLATED_OUTPUT_ONLY_HOLD"):
                write_isolated(r, root / "docs" / "data.json", root)
            self.assertFalse((root / "docs" / "data.json").exists())


if __name__ == "__main__":
    unittest.main()

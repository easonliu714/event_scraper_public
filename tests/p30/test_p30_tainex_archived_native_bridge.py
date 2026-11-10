"""Historical TaiNEX native artifact receipts -> common isolated REVIEW Core."""
import copy
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.p30_tainex_archived_native_bridge import (
    SPECS, archived_inputs, inspect_archived_native, validate_archived_prior)
from scripts.p30_multisource_review_lkg import plan

NOW = datetime(2026, 11, 10, 7, 55, tzinfo=timezone.utc)
FIXTURES = Path(__file__).parent / "fixtures"


class NativeArchivedTaiNEX(unittest.TestCase):
    def test_pinned_independent_github_native_artifact_receipts(self):
        a, b = [inspect_archived_native(p["id"], p["audit_bytes"], NOW)
                for p in archived_inputs(FIXTURES)]
        self.assertEqual((a["native_run_id"], a["artifact_id"]),
                         (40969673735, 12939228326))
        self.assertEqual((b["native_run_id"], b["artifact_id"]),
                         (40976369881, 12941823947))
        self.assertEqual(a["body_sha256"], SPECS["689"]["body_shas"])
        self.assertTrue(a["same_run_list_detail"])
        self.assertFalse(b["same_run_list_detail"])
        for receipt in (a, b):
            self.assertFalse(receipt["raw_html_available"])
            self.assertEqual(receipt["native_get_this_run"], 0)
            self.assertEqual(receipt["accepted_fields"], 0)

    def test_distinct_689_690_reach_common_review_lkg_without_promotion(self):
        original = archived_inputs(FIXTURES)
        r = plan([], archived_native=original, as_of=NOW)
        self.assertEqual(r["archived_native_receipt_qualified"], 2)
        self.assertEqual(r["source_reader_qualified"], 0)
        self.assertEqual(r["new_review"], 2)
        self.assertEqual([x["_candidate"]["record_id"] for x in r["review_rows"]],
                         ["TAINEX:event:689", "TAINEX:event:690"])
        self.assertEqual(r["independently_accepted_fields"], 0)
        self.assertEqual(r["native_get"], 0)
        self.assertEqual(r["published_delta"], 0)
        self.assertFalse(r["commit_permitted"])
        self.assertFalse(r["cross_host_cas_attested"])
        self.assertIn("LIST_EDGE_NOT_ATTESTED_IN_SAME_NATIVE_RUN",
                      r["review_rows"][1]["_candidate"]["hold_reasons"])
        for row in r["review_rows"]:
            validate_archived_prior(row, NOW)
        second = plan([], archived_native=original, previous=r["review_rows"], as_of=NOW)
        self.assertEqual(second["new_review"], 0)
        self.assertEqual(second["unchanged_review"], 2)
        self.assertEqual(second["review_rows"], r["review_rows"])

    def test_corruption_future_and_false_acceptance_fail_closed(self):
        packets = archived_inputs(FIXTURES)
        damaged = copy.deepcopy(packets)
        damaged[0]["audit_bytes"] += b" "
        r = plan([], archived_native=damaged, as_of=NOW)
        self.assertEqual(r["archived_native_receipt_qualified"], 1)
        self.assertEqual(len(r["rejected"]), 1)
        self.assertIn("ARCHIVED_NATIVE_AUDIT_SHA_HOLD", r["rejected"][0]["reason"])
        self.assertEqual(plan([], archived_native=packets,
                              as_of=datetime(2026, 10, 28, tzinfo=timezone.utc))
                         ["archived_native_receipt_qualified"], 0)
        prior = plan([], archived_native=packets, as_of=NOW)["review_rows"]
        for k, v in [("price", "NT$100 起"), ("date", "2026-11-13 10:00"),
                     ("title", "unrelated")]:
            tampered = copy.deepcopy(prior)
            tampered[0][k] = v
            with self.assertRaisesRegex(ValueError, "PRIOR_(?:LKG|NATIVE)_"):
                plan([], previous=tampered, as_of=NOW)
        tampered = copy.deepcopy(prior)
        tampered[1]["_candidate"]["source_class"] = "NATIVE_ACCEPTED"
        with self.assertRaisesRegex(ValueError, "PRIOR_(?:LKG|NATIVE)_"):
            plan([], previous=tampered, as_of=NOW)


if __name__ == "__main__":
    unittest.main()

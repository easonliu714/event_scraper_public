"""P30-L2-A offline negative/positive cases: no public HTTP calls."""
import importlib.util
import unittest
from pathlib import Path

source = Path(__file__).resolve().parents[2] / "scripts" / "p30_l2_http_triage.py"
spec = importlib.util.spec_from_file_location("p30_l2_triage", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(name, stage, code, count, detail=0):
    return {"platform": name, "listing_url": "https://example.com/",
            "stage1": stage, "list_candidates": count,
            "list_http": {"http_status": code, "url": "https://example.com/",
                          "trail": [{"http_status": code, "url": "https://example.com/"}]},
            "detail_checked": detail, "detail_http_ok": detail}


def sample(items=None):
    items = items if items is not None else [
        row("KKTIX", "HTTP_ERROR", 403, 0),
        row("FamiTicket", "HTTP_OK", 200, 0),
        row("OPENTIX", "HTTP_OK", 200, 2, 1),
    ]
    return {"kind": module.KIND, "platforms": items, "writer_executed": False,
            "notification_executed": False, "golden_accepted": False,
            "app_data_published": False, "auto_hidden": 0,
            "source_runtime": "DORMANT",
            "counts": {"platforms_checked": len(items),
                       "http_ok_platforms": sum(x["stage1"] == "HTTP_OK" for x in items),
                       "list_nonempty_platforms": sum(x["list_candidates"] > 0 for x in items),
                       "total_list_candidates": sum(x["list_candidates"] for x in items)}}


class OfflineTriageTests(unittest.TestCase):
    def test_all_three_tiers(self):
        result = module.triage(sample(), "a" * 64, "40196442965")
        self.assertEqual(result["counts"]["l2_http_failure_review"], 1)
        self.assertEqual(result["counts"]["l3_empty_list_review"], 1)
        self.assertEqual(result["counts"]["l4_detail_sample_next"], 1)
        self.assertEqual(result["platforms"][0]["platform"], "KKTIX")
        self.assertTrue(result["no_new_http_requests"])
        self.assertFalse(result["app_data_published"])

    def test_preserve_code_not_claim_block_reason(self):
        r = module.classify(row("x", "HTTP_ERROR", 403, 0))
        self.assertEqual(r["http_status"], 403)
        self.assertFalse(r["source_gone_proven"])
        self.assertFalse(r["automatic_hide_permitted"])
        self.assertEqual(module.classify(row("x", "HTTP_ERROR", 404, 0))["triage_tier"],
                         "L2_HTTP_FAILURE_REVIEW")

    def test_http_200_empty_is_not_successful_list(self):
        r = module.classify(row("x", "HTTP_OK", 200, 0))
        self.assertEqual(r["triage_tier"], "L3_LIST_EMPTY_REVIEW")

    def test_http_status_conflict_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "CODE_CONFLICT"):
            module.classify(row("x", "HTTP_OK", 403, 1))

    def test_blocked_must_not_produce_list(self):
        with self.assertRaisesRegex(ValueError, "BLOCKED_WITH_LIST_COUNT"):
            module.classify(row("x", "HTTP_ERROR", 429, 3))

    def test_writer_or_publish_flag_fails_closed(self):
        for field in ("writer_executed", "notification_executed",
                      "golden_accepted", "app_data_published"):
            d = sample()
            d[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "UNSAFE_PROVENANCE"):
                module.triage(d, "x", "run")

    def test_count_and_duplicate_guard(self):
        d = sample()
        d["counts"]["total_list_candidates"] = 999
        with self.assertRaisesRegex(ValueError, "COUNT_MISMATCH"):
            module.triage(d, "x", "run")
        d = sample([row("x", "HTTP_OK", 200, 1), row("x", "HTTP_OK", 200, 2)])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PLATFORMS"):
            module.triage(d, "x", "run")

    def test_http_errors_are_not_automatically_antibot(self):
        for code in (400, 403, 404, 429, 500):
            r = module.classify(row("x", "HTTP_ERROR", code, 0))
            self.assertFalse(r["source_gone_proven"])
            self.assertEqual(r["http_status"], code)

    def test_invalid_kind_and_no_platforms_fail_closed(self):
        d = sample()
        d["kind"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "WRONG_DIAGNOSTIC_KIND"):
            module.triage(d, "x", "run")
        d = sample([])
        with self.assertRaisesRegex(ValueError, "NO_PLATFORM_EVIDENCE"):
            module.triage(d, "x", "run")


if __name__ == "__main__":
    unittest.main()

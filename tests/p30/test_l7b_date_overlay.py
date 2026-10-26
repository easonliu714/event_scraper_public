"""P30-L7-B: no-network date-overlay lineage, 44 ID and conflict hold QA."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "p30_l7b_date_overlay.py"
spec = importlib.util.spec_from_file_location("p30_l7b_date_overlay", SCRIPT)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def fixtures():
    ids = []
    for i in range(5):
        ids.append({"id": f"CK-{i}", "platform": "中正紀念堂", "title": f"文化活動-{i}",
                    "officialUrl": f"https://event.culture.tw/CKSMH/id/{i}",
                    "dateStart": None, "dateEnd": None, "ticketStatus": "UNKNOWN"})
    rows = []
    for i in range(39):
        url = f"https://twtc.com.tw/exhibition_more.aspx?id={29000+i}&p=home"
        label = f"2026展覽-{i}"
        ids.append({"id": f"TW-{i}", "platform": "台北世貿", "title": label,
                    "officialUrl": url, "rawPeriod": "11/06 ~ 11/09",
                    "dateStart": "2026-11-06" if i == 0 else None,
                    "dateEnd": "2026-11-09" if i == 0 else None,
                    "timeRole": "OFFICIAL_EXHIBITION_DATE" if i == 0 else "EXHIBITION_PERIOD_RAW_UNNORMALIZED",
                    "sourceLevel": "DETAIL_DATE_CANDIDATE" if i == 0 else "LIST_TABLE_ONLY",
                    "ticketStatus": "UNKNOWN", "goldenVerified": False})
        rows.append({"title": label, "official_url": url, "detail_url": url,
                     "source_period_raw": "11/06 ~ 11/09",
                     "state": p.VERIFIED if i < 38 else "LIST_DETAIL_PERIOD_CONFLICT",
                     **({"start": "2026-11-06", "end": "2026-11-09",
                         "source_time_role": "OFFICIAL_EXHIBITION_DATE",
                         "response_sha256": "a"*64} if i < 38 else {})})
    original = {"kind": p.SOURCE_KIND, "count": 44, "items": ids,
                "sourceFileSHA256": {"twtcCandidate": "a"*64, "twtcDiagnostics": "b"*64},
                "goldenAccepted": False, "published": False, "writerExecuted": False,
                "notificationExecuted": False, "autoHidden": 0, "sourceRuntime": "DORMANT"}
    evidence = {"kind": p.EVIDENCE_KIND, "source_run_id": p.SOURCE_RUN,
                "source_candidate_count": 39,
                "source_file_sha256": {"candidate": "a"*64, "diagnostics": "b"*64},
                "counts": {"candidate_count": 39, "date_verified": 38, "remaining_unverified": 1},
                "identity_gate": "OFFICIAL_URL_ID+HEADING+RAW_PERIOD_PARITY",
                "records": rows,
                "app_data_published": False, "golden_accepted": False, "writer_executed": False,
                "notification_executed": False, "auto_hidden": 0, "source_runtime": "DORMANT"}
    return original, evidence


class OverlayQA(unittest.TestCase):
    def test_38_39_official_dates_and_44_identity_parity(self):
        orig, evidence = fixtures()
        merged, held = p.overlay(orig, evidence, "c"*64)
        self.assertEqual(merged["count"], 44)
        self.assertEqual(merged["dateVerifiedCount"], 38)
        self.assertEqual(len(held), 1)
        self.assertEqual(len({x["id"] for x in merged["items"]}), 44)
        self.assertFalse(merged["published"])
        self.assertFalse(merged["goldenAccepted"])
        self.assertTrue(all(x["dateStart"] == "2026-11-06" for x in merged["items"][5:43]))

    def test_original_accepted_smoke_input_is_not_mutated(self):
        original, evidence = fixtures()
        copy = original["items"][0].copy()
        merged, _ = p.overlay(original, evidence, "c"*64)
        self.assertEqual(original["items"][0], copy)
        self.assertEqual(merged["items"][0], copy)
        self.assertEqual(len([x for x in merged["items"] if x["platform"] == "中正紀念堂"]),5)

    def test_conflicting_official_detail_clears_stale_date(self):
        original, evidence = fixtures()
        original["items"][-1]["dateStart"] = "2026-11-06"
        original["items"][-1]["dateEnd"] = "2026-11-09"
        merged, held = p.overlay(original, evidence, "c"*64)
        self.assertIsNone(merged["items"][-1]["dateStart"])
        self.assertEqual(merged["items"][-1]["dateEvidenceStatus"], "LIST_DETAIL_PERIOD_CONFLICT")
        self.assertEqual(held[0]["reason"], "LIST_DETAIL_PERIOD_CONFLICT")

    def test_drifted_l3a_candidate_and_diagnostic_sha_fail_closed(self):
        for key in ("twtcCandidate", "twtcDiagnostics"):
            original, evidence = fixtures()
            original["sourceFileSHA256"][key] = "f"*64
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "SHA_MISMATCH"):
                p.overlay(original, evidence, "c"*64)

    def test_false_published_flag_fails_closed(self):
        for key in ("published", "goldenAccepted", "writerExecuted", "notificationExecuted"):
            original, evidence = fixtures()
            original[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "SOURCE_FLAG"):
                p.overlay(original, evidence, "c"*64)

    def test_mismatched_identity_rejected(self):
        original, evidence = fixtures()
        evidence["records"][0]["official_url"] = "https://twtc.com.tw/evil"
        with self.assertRaisesRegex(ValueError, "IDENTITY_NOT_IN_EVIDENCE"):
            p.overlay(original, evidence, "c"*64)

    def test_verified_url_and_date_role_required(self):
        original, evidence = fixtures()
        evidence["records"][0]["source_time_role"] = "SALE_WINDOW"
        with self.assertRaisesRegex(ValueError, "ROLE_URL_MISMATCH"):
            p.overlay(original, evidence, "c"*64)

    def test_wrong_verified_counts_rejected(self):
        original, evidence = fixtures()
        evidence["counts"]["date_verified"] = 39
        with self.assertRaisesRegex(ValueError, "COUNTS_MISMATCH"):
            p.overlay(original, evidence, "c"*64)

    def test_title_whitespace_join_conservative(self):
        original, evidence = fixtures()
        evidence["records"][0]["title"] = original["items"][5]["title"]+" "
        result, held = p.overlay(original, evidence, "c"*64)
        self.assertEqual(result["dateVerifiedCount"], 38)
        self.assertEqual(len(held), 1)

    def test_unknown_ticket_and_validity_unchanged(self):
        original, evidence = fixtures()
        for x in original["items"]:
            x["ticketStatus"] = "UNKNOWN"
            x["validity"] = "UNCERTAIN"
        result, _ = p.overlay(original, evidence, "c"*64)
        self.assertTrue(all(x["ticketStatus"] == "UNKNOWN" and x["validity"] == "UNCERTAIN"
                            for x in result["items"]))


if __name__ == "__main__":
    unittest.main()

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.p30_candidate_review_pipeline import (
    build_candidate_dataset, normalize_record, write_isolated_outputs, REVIEW_SCOPE
)


def example(id="A-01-1234", source="1234", platform="KKTIX"):
    return {
        "title": "測試演出 2026", "url": "https://example.org/events/" + source,
        "platform": platform, "type": "音樂會/演唱會",
        "scraped_at": "2026-11-01T17:00:00+08:00",
        "date": "2026-11-21 19:30", "location": "臺北市", "price": "未確認",
        "_candidate": {
            "record_id": id, "scope": REVIEW_SCOPE, "decision": "REVIEW",
            "platform_id": "01", "source_event_id": source,
            "source_class": "A", "sources": ["https://example.org/events/" + source],
            "hold_reasons": ["票券 Session ID 未確認"],
            "golden_accepted": False, "formal_field_pass": False, "published": False,
            "ticket_session_id": None, "inventory": None
        }
    }


class CandidateQualityTests(unittest.TestCase):
    def test_safe_review_only(self):
        candidates, report = build_candidate_dataset([example()])
        self.assertEqual(report["inputRows"], 1)
        self.assertEqual(report["previewRows"], 1)
        self.assertEqual(report["goldenAccepted"], 0)
        self.assertEqual(report["published"], 0)
        self.assertIsNone(candidates[0]["img_url"])
        self.assertEqual(candidates[0]["_candidate"]["scope"], REVIEW_SCOPE)

    def test_no_publication_status_spoof(self):
        for key in ("golden_accepted", "formal_field_pass", "published"):
            e = example()
            e["_candidate"][key] = True
            data, report = build_candidate_dataset([e])
            self.assertEqual(len(data), 0, key)
            self.assertEqual(report["rejectedRows"], 1)

    def test_wrong_scope_or_no_official_url(self):
        for change in ("published", "http", "missing_source", "bad_scope"):
            e = example()
            if change == "published":
                e["_candidate"]["decision"] = "PASS"
            elif change == "http":
                e["url"] = "http://example.org/events/1234"
            elif change == "missing_source":
                e["_candidate"]["sources"] = []
            else:
                e["_candidate"]["scope"] = "FORMAL"
            data, report = build_candidate_dataset([e])
            self.assertFalse(data, change)
            self.assertEqual(report["rejectedRows"], 1)

    def test_candidate_detail_url_requires_exact_source_receipt(self):
        # A listing URL or a different event detail must not authenticate
        # a candidate ticket/detail URL, even on the same HTTPS host.
        for bad_source in ("https://example.org/events",
                           "https://example.org/events/other",
                           "https://another.example.org/events/1234"):
            e = example()
            e["_candidate"]["sources"] = [bad_source]
            data, report = build_candidate_dataset([e])
            self.assertEqual(data, [])
            self.assertIn("DETAIL_URL_NOT_IN_SOURCE_EVIDENCE",
                          report["rejected"][0]["reasons"])
        e = example()
        e["_candidate"]["sources"] = ["https://example.org/events", e["url"]]
        data, report = build_candidate_dataset([e])
        self.assertEqual(report["previewRows"], 1)
        self.assertEqual(len(data), 1)

    def test_review_timestamp_must_be_timezone_aware(self):
        for stamp in ("2026-11-01T17:00:00", "not-a-date", None, 42):
            e = example()
            e["scraped_at"] = stamp
            data, report = build_candidate_dataset([e])
            self.assertEqual(data, [], repr(stamp))
            self.assertIn("OBSERVATION_TIME_UNVERIFIED", report["rejected"][0]["reasons"])
        e = example()
        e["scraped_at"] = "2026-11-01T09:00:00Z"
        self.assertEqual(build_candidate_dataset([e])[1]["previewRows"], 1)

    def test_nested_review_flags_cannot_hide_top_level_publication(self):
        for flag in ("published", "golden_accepted", "formal_field_pass"):
            e = example()
            e[flag] = True
            data, report = build_candidate_dataset([e])
            self.assertEqual(data, [])
            self.assertIn("TOP_LEVEL_PUBLICATION_CLAIM_" + flag.upper(),
                          report["rejected"][0]["reasons"])

    def test_invalid_hold_reasons_and_type_fail_closed(self):
        for bad in ([], [None], [" "], [object()]):
            e = example()
            e["_candidate"]["hold_reasons"] = bad
            data, report = build_candidate_dataset([e])
            self.assertEqual(data, [])
            self.assertIn("MISSING_OR_INVALID_HOLD_REASON",
                          report["rejected"][0]["reasons"])
        e = example()
        e["type"] = {"untrusted": "object"}
        self.assertIn("TYPE_INVALID",
                      build_candidate_dataset([e])[1]["rejected"][0]["reasons"])

    def test_unverified_session_objects_are_quarantined_not_forwarded(self):
        e = example()
        e["_candidate"]["sessions"] = [
            {"ticket_session_id": "fake", "price": "100", "inventory": "available"}
        ]
        rows, report = build_candidate_dataset([e])
        self.assertEqual(report["previewRows"], 1)
        self.assertEqual(rows[0]["_candidate"]["sessions"], [])
        self.assertIn("UNVERIFIED_SESSIONS_QUARANTINED",
                      rows[0]["_candidate"]["hold_reasons"])
        self.assertIsNone(rows[0]["_candidate"]["ticket_session_id"])
        self.assertIsNone(rows[0]["_candidate"]["inventory"])

    def test_review_field_provenance_is_exact_and_fail_closed(self):
        e = example()
        e["price"] = "100"
        rows, report = build_candidate_dataset([e])
        self.assertEqual(report["previewRows"], 1)
        self.assertEqual(rows[0]["date"], "未確認")
        self.assertEqual(rows[0]["location"], "未確認")
        self.assertEqual(rows[0]["price"], "未確認")
        self.assertIn("FIELD_PRICE_PROVENANCE_HOLD", rows[0]["_candidate"]["hold_reasons"])
        receipt = {"value": e["date"], "source": e["url"],
                   "observed_at": "2026-11-01T17:00:00+08:00",
                   "role": "EVENT_DATE", "decision": "REVIEW"}
        e["_candidate"]["field_evidence"] = {"date": receipt}
        rows, _ = build_candidate_dataset([e])
        self.assertEqual(rows[0]["date"], e["date"])
        self.assertFalse(rows[0]["_candidate"]["formal_field_pass"])
        for key, bad in (("source", "https://example.org/other"),
                         ("role", "SALE_END"),
                         ("role", ["EVENT_DATE"]),
                         ("observed_at", "2026-11-01T17:00:00"),
                         ("value", "other"), ("decision", "PASS")):
            changed = copy.deepcopy(e)
            changed["_candidate"]["field_evidence"]["date"][key] = bad
            rows, _ = build_candidate_dataset([changed])
            self.assertEqual(rows[0]["date"], "未確認", key)
            self.assertIn("FIELD_DATE_PROVENANCE_HOLD",
                          rows[0]["_candidate"]["hold_reasons"])

    def test_duplicate_same_platform_event_id_rejected(self):
        first, second = example(), example("second", "1234")
        data, report = build_candidate_dataset([first, second])
        self.assertEqual(len(data), 1)
        self.assertEqual(report["rejected"][0]["reasons"], ["DUPLICATE_CANONICAL_ID"])

    def test_other_platform_same_event_id_is_not_assumed_duplicate(self):
        first, second = example(), example("B-05-1234", "1234", "OPENTIX")
        second["_candidate"]["platform_id"] = "05"
        data, report = build_candidate_dataset([first, second])
        self.assertEqual(len(data), 2)
        self.assertEqual(report["previewRows"], 2)

    def test_title_contamination_is_flagged_not_guess_cleaned(self):
        e = example()
        e["title"] = "主題長篇講座2026-03-11～2026-12-09臺北市中正區精彩課程內容與推廣講座活動招生最新動態預告"
        data, _ = build_candidate_dataset([e])
        self.assertEqual(data[0]["title"], e["title"])
        self.assertIn("TITLE_MIXED_WITH_DATE_REQUIRES_SOURCE_RECHECK",
                      data[0]["_candidate"]["hold_reasons"])

    def test_cross_source_receipts_do_not_prove_candidate_fields(self):
        # A-line: a source-listed VIP add-on is a distinct product, not a
        # source-owned admission price for the base concert.
        base = example(source="26_wte", platform="tixCraft")
        base["url"] = "https://tixcraft.com/activity/detail/26_wte"
        addon = "https://tixcraft.com/activity/detail/26_wte_v"
        base["_candidate"]["sources"] = [base["url"], addon]
        base["price"] = "NT$4,800"
        base["_candidate"]["field_evidence"] = {
            "price": {
                "value": base["price"], "source": addon,
                "role": "EVENT_ADMISSION_PRICE",
                "observed_at": "2026-11-01T23:52:00+08:00",
                "decision": "REVIEW",
            }
        }
        rows, report = build_candidate_dataset([base])
        self.assertEqual(report["previewRows"], 1)
        self.assertEqual(rows[0]["price"], "未確認")
        self.assertNotIn("price", rows[0]["_candidate"]["field_evidence"])
        self.assertIn("FIELD_PRICE_PROVENANCE_HOLD",
                      rows[0]["_candidate"]["hold_reasons"])

        # B-line: an OPENTIX multi-venue Event URL in sources[] is not a
        # verified New Taipei Art Center performance Session/date receipt.
        venue = example(source="0Q152372523738311866",
                        platform="新北市藝文中心")
        venue["url"] = ("https://www.culture.ntpc.gov.tw/artcenter_chi/"
                        "xmdoc/cont?sid=0Q152372523738311866")
        ticket = "https://www.opentix.life/event/2086734015886159873"
        venue["_candidate"]["sources"] = [venue["url"], ticket]
        venue["date"] = "2026-11-07 14:30"
        venue["_candidate"]["field_evidence"] = {
            "date": {
                "value": venue["date"], "source": ticket,
                "role": "VENUE_EVENT_DATE",
                "observed_at": "2026-11-01T23:52:00+08:00",
                "decision": "REVIEW",
            }
        }
        rows, report = build_candidate_dataset([venue])
        self.assertEqual(report["previewRows"], 1)
        self.assertEqual(rows[0]["date"], "未確認")
        self.assertIn("FIELD_DATE_PROVENANCE_HOLD",
                      rows[0]["_candidate"]["hold_reasons"])
        self.assertEqual(report["formalFieldAccepted"], 0)
        self.assertEqual(report["goldenAccepted"], 0)

        # Exact same-row URL can support a REVIEW value only with an
        # allowed semantic role; sale/publication timestamps stay HOLD.
        venue["_candidate"]["field_evidence"]["date"]["source"] = venue["url"]
        rows, _ = build_candidate_dataset([venue])
        self.assertEqual(rows[0]["date"], venue["date"])
        self.assertEqual(rows[0]["_candidate"]["field_evidence"]["date"]["decision"],
                         "REVIEW")
        venue["_candidate"]["field_evidence"]["date"]["role"] = "BULLETIN_PUBLISHED_AT"
        rows, _ = build_candidate_dataset([venue])
        self.assertEqual(rows[0]["date"], "未確認")
        self.assertIn("FIELD_DATE_PROVENANCE_HOLD",
                      rows[0]["_candidate"]["hold_reasons"])

    def test_output_frozen_public_pages_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            formal = root / "docs"
            formal.mkdir()
            (formal / "data.json").write_text("[123]", encoding="utf-8")
            original = hashlib.sha256((formal / "data.json").read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                write_isolated_outputs([example()], formal, root)
            target = root / "out" / "candidate_review"
            report = write_isolated_outputs([example()], target, root)
            self.assertEqual(report["previewRows"], 1)
            self.assertEqual(hashlib.sha256((formal / "data.json").read_bytes()).hexdigest(), original)
            data = json.loads((target / "data.json").read_text(encoding="utf-8"))
            self.assertEqual(data[0]["_candidate"]["published"], False)
            manifest = (target / "SHA256SUMS.txt").read_text()
            self.assertIn("data.json", manifest)
            self.assertIn("quality_report.json", manifest)

    def test_audit_only_18_legacy_rows_reports_rejections_without_preview(self):
        # This is a contract test using 18 untrusted legacy-shaped inputs,
        # NOT the Owner's missing 18-record source dataset.
        legacy = [
            {"title": "待核活動", "url": "https://example.org/event/" + str(i),
             "platform": "平台A" if i < 11 else "平台B",
             "type": "其他", "scraped_at": "2026-11-01T17:00:00+08:00"}
            for i in range(18)
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "isolated-audit"
            report = write_isolated_outputs(
                legacy, dest, root, audit_only=True, expected_rows=18
            )
            self.assertEqual(report["inputRows"], 18)
            self.assertEqual(report["previewRows"], 0)
            self.assertEqual(report["rejectedRows"], 18)
            self.assertEqual(report["inputPlatformCounts"], {"平台A": 11, "平台B": 7})
            self.assertEqual(report["rejectedPlatformCounts"], {"平台A": 11, "平台B": 7})
            self.assertEqual(report["rejectionReasonCounts"]["MISSING__CANDIDATE"], 18)
            self.assertTrue(report["auditOnly"])
            self.assertFalse(report["previewImportAllowed"])
            self.assertFalse((dest / "data.json").exists())
            self.assertTrue((dest / "quality_report.json").exists())
            self.assertEqual(len((dest / "SHA256SUMS.txt").read_text().splitlines()), 1)

    def test_expected_row_count_fail_closed_and_no_stale_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "audit"
            with self.assertRaisesRegex(ValueError, "EXPECTED_INPUT_ROW_COUNT_MISMATCH"):
                write_isolated_outputs([example()], dest, root,
                                       audit_only=True, expected_rows=18)
            self.assertFalse(dest.exists())
            dest.mkdir()
            (dest / "data.json").write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "AUDIT_ONLY_OUTPUT_HAS_STALE_PREVIEW_DATA"):
                write_isolated_outputs([example()], dest, root,
                                       audit_only=True, expected_rows=1)

    def test_oversized_input_rejected(self):
        with self.assertRaises(ValueError):
            build_candidate_dataset([example()] * 2001)


if __name__ == "__main__":
    unittest.main()

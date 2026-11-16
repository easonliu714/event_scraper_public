"""Offline RAW5 native evidence tests: no HTTP requests are made."""
import json
import unittest
from datetime import datetime, timedelta, timezone

from scripts.p30_tpac_raw5_native_response import (
    seal_native_detail_response, verify_native_detail_receipt,
)

BASE = dict(requested_url="https://tpac.org.taipei/program/2083",
            final_url="https://tpac.org.taipei/program/2083",
            status=200, content_type="text/html; charset=utf-8",
            body=b"<html>native bytes</html>",
            observed_at=datetime(2026, 11, 16, 8, 0, tzinfo=timezone.utc),
            executor_id="runner-001", claim_id="claim-001", run_id="raw5-run-001")


class NativeResponseTests(unittest.TestCase):
    def test_original_bytes_and_receipt_round_trip(self):
        manifest, body = seal_native_detail_response(**BASE)
        record = verify_native_detail_receipt(manifest, body)
        self.assertEqual(body, BASE["body"])
        self.assertEqual(record["namespace"], "program")
        self.assertEqual(record["event_id"], "2083")
        self.assertFalse(record["formal_publish_allowed"])

    def test_tampered_body_rejected(self):
        manifest, body = seal_native_detail_response(**BASE)
        with self.assertRaisesRegex(ValueError, "BYTES_PARITY_HOLD"):
            verify_native_detail_receipt(manifest, body + b"x")

    def test_cross_origin_and_cross_id_redirect_rejected(self):
        for url in ("http://tpac.org.taipei/program/2083",
                    "https://evil.example/program/2083",
                    "https://tpac.org.taipei/event/2083",
                    "https://tpac.org.taipei/program/2084",
                    "https://tpac.org.taipei/program/2083?token=secret"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                seal_native_detail_response(**{**BASE, "final_url": url})

    def test_http_429_and_non_html_rejected(self):
        for change in ({"status": 429}, {"status": 403},
                       {"content_type": "application/json"}, {"body": b""},
                       {"body": b"x" * (2 * 1024 * 1024 + 1)}):
            with self.subTest(change=list(change)), self.assertRaises(ValueError):
                seal_native_detail_response(**{**BASE, **change})

    def test_local_time_and_untrusted_ids_rejected(self):
        for change in ({"observed_at": BASE["observed_at"].astimezone(timezone(timedelta(hours=8)))},
                       {"observed_at": datetime(2026, 11, 16)},
                       {"run_id": "../unsafe"}):
            with self.subTest(change=list(change)), self.assertRaises(ValueError):
                seal_native_detail_response(**{**BASE, **change})

    def test_manifest_false_publication_cannot_be_changed(self):
        manifest, body = seal_native_detail_response(**BASE)
        record = json.loads(manifest)
        record["formal_publish_allowed"] = True
        with self.assertRaisesRegex(ValueError, "BYTES_PARITY_HOLD"):
            verify_native_detail_receipt(json.dumps(record).encode(), body)


if __name__ == "__main__":
    unittest.main()

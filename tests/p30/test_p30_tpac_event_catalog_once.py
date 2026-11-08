"""No-network TPAC /event robots + LIST + two distinct DETAIL one-shot tests."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.p30_tpac_event_catalog_once import (
    ROOT, ROBOTS, SOURCE_IDS, bounded_fetch, collect_once,
)

ROBOTS_OK = b"User-agent: *\nAllow: /event\n"
LIST = (b'<main><a href="/event/1301" title="Exhibition">Exhibition</a>'
        b'<a href="/event/2072" title="Tour">Tour</a></main>')
ONE = b"<main><h1>Exhibition</h1><p>Opening hours</p></main>"
TWO = b"<main><h1>Tour</h1><p>Showtimes</p></main>"


class EventSourceOnceTests(unittest.TestCase):
    def test_robots_then_list_then_two_different_details(self):
        calls = []
        allowed = {
            ROBOTS: ROBOTS_OK, ROOT: LIST,
            ROOT + "/1301": ONE, ROOT + "/2072": TWO,
        }
        def fetch(u):
            calls.append(u)
            return allowed[u]
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            report = collect_once(out, fetch=fetch)
            self.assertEqual(calls, [ROBOTS, ROOT, ROOT + "/1301", ROOT + "/2072"])
            self.assertEqual(report["successful_get"], 4)
            self.assertEqual(report["listed_id_count"], 2)
            self.assertEqual(report["decision"], "NATIVE_BODY_CAPTURED_FOR_INDEPENDENT_REPLAY_ONLY")
            self.assertFalse(report["native_official_attestation"])
            self.assertEqual(report["published"], 0)
            self.assertEqual(report["accepted_fields"], 0)
            self.assertEqual(report["source_receipts"]["1301"]["body_sha256"], hashlib.sha256(ONE).hexdigest())
            self.assertEqual((out / "event_2072_detail.html").read_bytes(), TWO)
            self.assertFalse((out / "docs" / "data.json").exists())

    def test_robots_disallow_blocks_list_and_detail(self):
        calls = []
        def denied(url):
            calls.append(url)
            return b"User-agent: *\nDisallow: /event\n"
        with tempfile.TemporaryDirectory() as root:
            report = collect_once(root, fetch=denied)
            self.assertEqual(calls, [ROBOTS])
            self.assertEqual(report["decision"], "HOLD")
            self.assertIn("ROBOTS_DISALLOW_HOLD", report["first_failure"])
            self.assertEqual(report["successful_get"], 1)

    def test_missing_second_list_link_prevents_detail_get(self):
        calls = []
        def missing(u):
            calls.append(u)
            return ROBOTS_OK if u == ROBOTS else LIST.replace(b"/event/2072", b"/event/9999")
        with tempfile.TemporaryDirectory() as root:
            report = collect_once(root, fetch=missing)
            self.assertEqual(calls, [ROBOTS, ROOT])
            self.assertEqual(report["decision"], "HOLD")
            self.assertIn("TWO_DISTINCT_LIST_EDGES_MISSING_HOLD", report["first_failure"])

    def test_403_first_detail_has_no_retry_or_second_detail(self):
        calls = []
        def gone(u):
            calls.append(u)
            if u == ROOT + "/1301":
                raise ValueError("403")
            return ROBOTS_OK if u == ROBOTS else LIST
        with tempfile.TemporaryDirectory() as root:
            report = collect_once(root, fetch=gone)
            self.assertEqual(calls, [ROBOTS, ROOT, ROOT + "/1301"])
            self.assertEqual(report["decision"], "HOLD")
            self.assertEqual(report["successful_get"], 2)
            self.assertFalse((Path(root) / "event_2072_detail.html").exists())

    def test_unapproved_detail_id_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError, "UNAPPROVED_URL_HOLD"):
            bounded_fetch(ROOT + "/9999")


if __name__ == "__main__":
    unittest.main()

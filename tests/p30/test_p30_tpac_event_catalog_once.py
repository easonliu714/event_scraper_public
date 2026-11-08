"""No-network TPAC /event robots + LIST + two distinct DETAIL one-shot tests."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.p30_tpac_event_catalog_once import (
    ROOT, ROBOTS, SOURCE_IDS, bounded_fetch, collect_once,
    collect_bounded_review_cycle,
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



    def test_r4_dynamic_two_ids_bounded_receipts_manifest_and_one_shot(self):
        calls, sleeps = [], []
        listing = (b'<main><a href="/event/3456" title="Tour">Tour</a>'
                   b'<a href="/event/9876" title="Exhibition">Exhibition</a></main>')
        pages = {ROBOTS: ROBOTS_OK, ROOT: listing,
                 ROOT + "/3456": ONE, ROOT + "/9876": TWO}
        def fake(url):
            calls.append(url)
            return pages[url]
        from datetime import datetime, timezone
        def clock():
            return datetime(2026, 11, 9, 1, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "cycle-01"
            report = collect_bounded_review_cycle(
                out, "tpac-r4-20261109-010000z-a1b2c3d4",
                source_policy_approved=True, fetch=fake,
                clock=clock, pause=sleeps.append)
            self.assertEqual(report["decision"], "ISOLATED_NATIVE_BYTES_CAPTURED_REPLAY_REQUIRED")
            self.assertEqual(report["selected_ids"], ["3456", "9876"])
            self.assertEqual(calls, [ROBOTS, ROOT, ROOT + "/3456", ROOT + "/9876"])
            self.assertEqual(sleeps, [3, 3, 3])
            self.assertEqual(report["successful_get"], 4)
            self.assertFalse(report["independent_cycle_verified"])
            self.assertFalse(report["global_one_shot_registry_verified"])
            self.assertEqual(report["published"], 0)
            manifest = json.loads((out / "tpac_r4_refresh_manifest.json").read_text())
            self.assertEqual(manifest["catalog"], "event")
            self.assertNotIn("prior", manifest)
            self.assertEqual(set(manifest["details"]), {"3456", "9876"})
            self.assertEqual(manifest["list_receipt"]["body_sha256"],
                             hashlib.sha256(listing).hexdigest())
            self.assertEqual((out / "event_9876_detail.html").read_bytes(), TWO)
            with self.assertRaisesRegex(ValueError, "ALREADY_CLAIMED_HOLD"):
                collect_bounded_review_cycle(
                    out, "tpac-r4-20261109-010000z-a1b2c3d4",
                    source_policy_approved=True, fetch=fake, pause=sleeps.append)
            self.assertEqual(len(calls), 4)

    def test_r4_requires_explicit_source_policy_before_any_request(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "no-authorization"
            with self.assertRaisesRegex(ValueError, "SOURCE_POLICY_AUTHORITY_HOLD"):
                collect_bounded_review_cycle(out, "tpac-r4-20261109-010000z-a1b2c3d4",
                                             fetch=lambda url: self.fail("network attempted"))
            self.assertFalse(out.exists())
            with self.assertRaisesRegex(ValueError, "CYCLE_ID_HOLD"):
                collect_bounded_review_cycle(out, "../wrong",
                                             source_policy_approved=True,
                                             fetch=lambda url: self.fail("network attempted"))
            self.assertFalse(out.exists())

    def test_r4_robots_denial_stops_before_list_and_preserves_forensic_receipt(self):
        calls = []
        def denied(url):
            calls.append(url)
            return b"User-agent: *\nDisallow: /event\n"
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "denied"
            report = collect_bounded_review_cycle(
                out, "tpac-r4-20261109-020000z-a1b2c3d4",
                source_policy_approved=True, fetch=denied, pause=lambda n: None)
            self.assertEqual(calls, [ROBOTS])
            self.assertEqual(report["decision"], "HOLD")
            self.assertIn("ROBOTS_LIST_DISALLOW_HOLD", report["first_failure"])
            self.assertTrue((out / "tpac_r4_cycle_receipt.json").is_file())
            self.assertFalse((out / "tpac_r4_refresh_manifest.json").exists())

    def test_r4_detail_403_no_retry_and_no_consumable_manifest(self):
        calls = []
        listing = (b'<a href="/event/3456">A</a>'
                   b'<a href="/event/9876">B</a>')
        def fail_first_detail(url):
            calls.append(url)
            if url == ROOT + "/3456":
                raise ValueError("HTTP 403")
            return ROBOTS_OK if url == ROBOTS else listing
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "forensic"
            report = collect_bounded_review_cycle(
                out, "tpac-r4-20261109-030000z-a1b2c3d4",
                source_policy_approved=True, fetch=fail_first_detail,
                pause=lambda n: None)
            self.assertEqual(calls, [ROBOTS, ROOT, ROOT + "/3456"])
            self.assertEqual(report["successful_get"], 2)
            self.assertEqual(report["decision"], "HOLD")
            self.assertFalse((out / "tpac_r4_refresh_manifest.json").exists())
            self.assertTrue((out / "event_list.html").is_file())

    def test_r4_excessive_robots_crawl_delay_holds_before_list(self):
        calls = []
        def slow(url):
            calls.append(url)
            return b"User-agent: *\nCrawl-delay: 120\nAllow: /event\n"
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "slow"
            report = collect_bounded_review_cycle(
                out, "tpac-r4-20261109-040000z-a1b2c3d4",
                source_policy_approved=True, fetch=slow,
                pause=lambda n: self.fail("unexpected delay"))
            self.assertEqual(calls, [ROBOTS])
            self.assertEqual(report["decision"], "HOLD")
            self.assertIn("CRAWL_DELAY_OVER_BUDGET_HOLD", report["first_failure"])
            self.assertFalse((out / "tpac_r4_refresh_manifest.json").exists())


if __name__ == "__main__":
    unittest.main()

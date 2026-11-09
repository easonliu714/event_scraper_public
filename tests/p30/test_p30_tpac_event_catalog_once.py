"""No-network TPAC /event robots + LIST + two distinct DETAIL one-shot tests."""
import hashlib
from urllib.error import HTTPError
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.p30_tpac_event_catalog_once import (
    ROOT, ROBOTS, SOURCE_IDS, bounded_fetch, collect_once,
    collect_bounded_review_cycle, GitHubAtomicClaimRegistry,
)

ROBOTS_OK = b"User-agent: *\nAllow: /event\n"
LIST = (b'<main><a href="/event/1301" title="Exhibition">Exhibition</a>'
        b'<a href="/event/2072" title="Tour">Tour</a></main>')
ONE = b"<main><h1>Exhibition</h1><p>Opening hours</p></main>"
TWO = b"<main><h1>Tour</h1><p>Showtimes</p></main>"




class FakeGitHubOpener:
    """No-network REST double with shared tag state across simulated hosts."""
    SHA = "a" * 40
    API = GitHubAtomicClaimRegistry.API

    def __init__(self, claimed=None, *, main_sha=None, corrupt_readback=False):
        self.claimed = claimed if claimed is not None else set()
        self.main_sha = main_sha or self.SHA
        self.corrupt_readback = corrupt_readback
        self.calls = []

    def open(self, req, timeout=None):
        url = req.full_url
        method = req.get_method()
        self.calls.append((method, url))
        class Response:
            def __init__(self, url, status, body):
                self.url, self.status = url, status
                self.body = json.dumps(body).encode()
            def geturl(self):
                return self.url
            def read(self, cap):
                return self.body[:cap]
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
        if method == "GET" and url == self.API + "/git/ref/heads/main":
            return Response(url, 200, {
                "ref": "refs/heads/main", "object": {"sha": self.main_sha}})
        prefix = "refs/tags/eventradar-tpac-r4-claims/"
        if method == "POST" and url == self.API + "/git/refs":
            value = json.loads(req.data.decode())
            ref = value["ref"]
            if ref in self.claimed:
                raise HTTPError(url, 422, "already exists", {}, None)
            self.claimed.add(ref)
            return Response(url, 201, {
                "ref": ref, "object": {"sha": value["sha"]}})
        if method == "GET" and url.startswith(
                self.API + "/git/ref/tags/eventradar-tpac-r4-claims/"):
            ref = "refs/tags/" + url.split("/git/ref/tags/", 1)[1]
            if ref not in self.claimed:
                raise HTTPError(url, 404, "missing", {}, None)
            return Response(url, 200, {
                "ref": ref,
                "object": {"sha": ("b" * 40 if self.corrupt_readback else self.SHA)}})
        raise AssertionError("unexpected GitHub request " + method + " " + url)


def fake_global_registry(shared=None, **kwargs):
    opener = FakeGitHubOpener(shared, **kwargs)
    return GitHubAtomicClaimRegistry("no-network-unit-test-token", opener.SHA,
                                     opener=opener)


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

    def test_retired_direct_fetch_rejects_all_allowlisted_urls_before_network(self):
        # Closing the CLI alone left a direct Python bounded_fetch() GET path.
        # No default or explicitly injected opener may access old one-shot URLs.
        from unittest.mock import patch

        calls = []
        class PoisonOpener:
            def open(self, *args, **kwargs):
                calls.append((args, kwargs))
                raise AssertionError("LEGACY_DIRECT_NETWORK_MUST_NOT_BE_CALLED")

        with patch("scripts.p30_tpac_event_catalog_once.build_opener",
                   side_effect=AssertionError("DEFAULT_NETWORK_MUST_NOT_BE_CALLED")):
            for url in (ROBOTS, ROOT, ROOT + "/1301", ROOT + "/2072"):
                for opener in (None, PoisonOpener()):
                    with self.subTest(url=url, explicit_opener=opener is not None):
                        with self.assertRaisesRegex(
                                ValueError, "TPAC_EVENT_DIRECT_NATIVE_FETCH_DISABLED_HOLD"):
                            bounded_fetch(url, opener=opener)
        self.assertEqual(calls, [])

    def test_consumed_legacy_one_shot_no_default_native_get_or_cli_output(self):
        # Historical run 42491637804 exhausted the legacy native GET marker.
        # A default CLI must not bypass the newer R4 immutable-retention HOLD.
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "legacy-must-not-fetch"
            for injected in (None, bounded_fetch):
                with self.subTest(fetch=str(injected)):
                    with self.assertRaisesRegex(
                            ValueError, "TPAC_EVENT_LEGACY_NATIVE_FETCH_DISABLED_HOLD"):
                        collect_once(out, fetch=injected)
                    self.assertFalse(out.exists())
            proc = subprocess.run(
                [sys.executable, "-m", "scripts.p30_tpac_event_catalog_once",
                 "--output", str(out)],
                capture_output=True, text=True, timeout=10, check=False)
            self.assertEqual(proc.returncode, 49, proc.stderr)
            self.assertIn("TPAC_EVENT_LEGACY_NATIVE_GET_DISABLED_HOLD", proc.stdout)
            self.assertFalse(out.exists())

    def test_ci_never_reissues_consumed_legacy_source_one_shot(self):
        workflow = (Path(__file__).resolve().parents[2] /
                    ".github/workflows/eventradar_tpac_multi_event_refresh.yml")
        content = workflow.read_text(encoding="utf-8")
        self.assertIn("PASS_TPAC_EVENT_ONE_SHOT_CONSUMED_NO_NATIVE_GET", content)
        self.assertNotIn("python -m scripts.p30_tpac_event_catalog_once --output", content)
        self.assertIn("run-id: 42491637804", content)




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
            registry = Path(root) / "registry"
            registry.mkdir()
            report = collect_bounded_review_cycle(
                out, "tpac-r4-20261109-010000z-a1b2c3d4",
                source_policy_approved=True, fetch=fake,
                clock=clock, pause=sleeps.append, registry_dir=registry, global_registry=fake_global_registry())
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
                    source_policy_approved=True, fetch=fake, pause=sleeps.append,
                    registry_dir=registry, global_registry=fake_global_registry())
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
            registry = Path(root) / "registry"
            registry.mkdir()
            report = collect_bounded_review_cycle(
                out, "tpac-r4-20261109-020000z-a1b2c3d4",
                source_policy_approved=True, fetch=denied, pause=lambda n: None,
                registry_dir=registry, global_registry=fake_global_registry())
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
            registry = Path(root) / "registry"
            registry.mkdir()
            report = collect_bounded_review_cycle(
                out, "tpac-r4-20261109-030000z-a1b2c3d4",
                source_policy_approved=True, fetch=fail_first_detail,
                pause=lambda n: None, registry_dir=registry, global_registry=fake_global_registry())
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
            registry = Path(root) / "registry"
            registry.mkdir()
            report = collect_bounded_review_cycle(
                out, "tpac-r4-20261109-040000z-a1b2c3d4",
                source_policy_approved=True, fetch=slow,
                pause=lambda n: self.fail("unexpected delay"),
                registry_dir=registry, global_registry=fake_global_registry())
            self.assertEqual(calls, [ROBOTS])
            self.assertEqual(report["decision"], "HOLD")
            self.assertIn("CRAWL_DELAY_OVER_BUDGET_HOLD", report["first_failure"])
            self.assertFalse((out / "tpac_r4_refresh_manifest.json").exists())


    def test_r4_durable_registry_blocks_same_id_across_distinct_outputs_after_denial(self):
        calls = []
        def denied(url):
            calls.append(url)
            return b"User-agent: *\nDisallow: /event\n"
        with tempfile.TemporaryDirectory() as root:
            registry = Path(root) / "registry"
            registry.mkdir()
            first = Path(root) / "first"
            second = Path(root) / "second"
            cycle = "tpac-r4-20261109-050000z-a1b2c3d4"
            report = collect_bounded_review_cycle(
                first, cycle, source_policy_approved=True, fetch=denied,
                pause=lambda n: None, registry_dir=registry, global_registry=fake_global_registry())
            self.assertEqual(report["decision"], "HOLD")
            self.assertEqual(calls, [ROBOTS])
            self.assertTrue((registry / (cycle + ".claim.json")).is_file())
            with self.assertRaisesRegex(ValueError, "DURABLE_CYCLE_REUSE_HOLD"):
                collect_bounded_review_cycle(
                    second, cycle, source_policy_approved=True, fetch=denied,
                    pause=lambda n: None, registry_dir=registry, global_registry=fake_global_registry())
            self.assertFalse(second.exists())
            self.assertEqual(calls, [ROBOTS])

    def test_r4_missing_or_symlink_registry_holds_before_any_request(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "out"
            cycle = "tpac-r4-20261109-060000z-a1b2c3d4"
            no_get = lambda url: self.fail("unexpected network")
            with self.assertRaisesRegex(ValueError, "DURABLE_REGISTRY_REQUIRED_HOLD"):
                collect_bounded_review_cycle(
                    out, cycle, source_policy_approved=True, fetch=no_get)
            self.assertFalse(out.exists())
            target = Path(root) / "registry"
            target.mkdir()
            alias = Path(root) / "alias"
            try:
                alias.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError):
                return
            with self.assertRaisesRegex(ValueError, "DURABLE_REGISTRY_UNTRUSTED_HOLD"):
                collect_bounded_review_cycle(
                    out, cycle, source_policy_approved=True,
                    fetch=no_get, registry_dir=alias)
            self.assertFalse(out.exists())


    def test_r4_global_registry_required_before_source_get(self):
        with tempfile.TemporaryDirectory() as root:
            registry = Path(root) / "registry"
            registry.mkdir()
            out = Path(root) / "no-global"
            with self.assertRaisesRegex(ValueError, "GLOBAL_ATOMIC_REGISTRY_REQUIRED_HOLD"):
                collect_bounded_review_cycle(
                    out, "tpac-r4-20261109-065500z-a1b2c3d4",
                    source_policy_approved=True, registry_dir=registry,
                    fetch=lambda url: self.fail("network attempted"))
            self.assertFalse(out.exists())
            self.assertEqual(list(registry.iterdir()), [])

    def test_r4_live_cli_retention_gap_holds_before_global_tag_or_source_get(self):
        """A caller policy boolean plus deletable GitHub tag cannot authorize live GET."""
        with tempfile.TemporaryDirectory() as root:
            registry = Path(root) / "registry"
            registry.mkdir()
            out = Path(root) / "real-source-must-hold"
            shared_tags = set()
            global_registry = fake_global_registry(shared_tags)
            with self.assertRaisesRegex(
                    ValueError, "GLOBAL_RETENTION_AUTHORITY_UNVERIFIED_HOLD"):
                collect_bounded_review_cycle(
                    out, "tpac-r4-20261109-075500z-a1b2c3d4",
                    source_policy_approved=True, registry_dir=registry,
                    global_registry=global_registry)
            self.assertFalse(out.exists())
            self.assertEqual(list(registry.iterdir()), [])
            self.assertEqual(shared_tags, set())
            self.assertEqual(global_registry._opener.calls, [])

    def test_r4_two_hosts_same_cycle_global_atomic_ref_rejects_second(self):
        calls, shared = [], set()
        def denied(url):
            calls.append(url)
            return b"User-agent: *\nDisallow: /event\n"
        with tempfile.TemporaryDirectory() as root:
            cycle = "tpac-r4-20261109-065500z-a1b2c3d4"
            registry_a, registry_b = Path(root)/"a", Path(root)/"b"
            registry_a.mkdir()
            registry_b.mkdir()
            first = collect_bounded_review_cycle(
                Path(root)/"first", cycle, source_policy_approved=True,
                registry_dir=registry_a, global_registry=fake_global_registry(shared),
                fetch=denied, pause=lambda _: None)
            self.assertEqual(first["decision"], "HOLD")
            self.assertTrue(first["global_atomic_claim_created"])
            self.assertFalse(first["global_immutable_registry_verified"])
            self.assertEqual(len(calls), 1)
            with self.assertRaisesRegex(ValueError, "GLOBAL_CYCLE_ALREADY_CLAIMED"):
                collect_bounded_review_cycle(
                    Path(root)/"second", cycle, source_policy_approved=True,
                    registry_dir=registry_b, global_registry=fake_global_registry(shared),
                    fetch=denied, pause=lambda _: None)
            self.assertEqual(len(calls), 1)
            self.assertFalse((Path(root)/"second").exists())
            self.assertEqual(list(registry_b.iterdir()), [])

    def test_r4_global_claim_main_drift_and_readback_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            reg = Path(root)/"registry"
            reg.mkdir()
            cycle = "tpac-r4-20261109-065500z-a1b2c3d4"
            for name, opts, reason in (
                ("drift", {"main_sha":"c"*40}, "MAIN_HEAD_DRIFT_HOLD"),
                ("readback", {"corrupt_readback":True}, "READBACK_PARITY_HOLD"),
            ):
                with self.subTest(name=name):
                    out = Path(root)/name
                    with self.assertRaisesRegex(ValueError, reason):
                        collect_bounded_review_cycle(
                            out, cycle, source_policy_approved=True,
                            registry_dir=reg, global_registry=fake_global_registry(**opts),
                            fetch=lambda url: self.fail("network attempted"))
                    self.assertFalse(out.exists())
                    self.assertEqual(list(reg.iterdir()), [])



if __name__ == "__main__":
    unittest.main()

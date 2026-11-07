"""Executable A/B same-ID -> preview REVIEW -> checksum/CAS LKG integration."""
import hashlib
import io
import json
from contextlib import redirect_stdout
import tempfile
import unittest
from pathlib import Path

from scripts import p30_ab_kktix_fuzhong_native as a
from scripts import p30_ntpc_artcenter_source as b
from scripts import p30_review_bridge as bridge

STAMP = "2026-11-07T01:00:00+00:00"


class ReviewBridgeTests(unittest.TestCase):
    def setUp(self):
        self.a_list = ('<main><a href="' + a.SOURCES["A_KIMU"]["detail"] +
                       '">' + a.SOURCES["A_KIMU"]["title"] + '</a></main>').encode()
        self.a_detail = ('<main><article><h2>' + a.SOURCES["A_KIMU"]["title"] +
                         '</h2><p>2026/11/14 10:00-16:30</p></article></main>').encode()
        self.b_list = ('<main><a href="/artcenter_chi/xmdoc/cont?sid=' + b.SID +
                       '&sq=&xsmsid=' + b.XSMSID + '">' + b.TITLE +
                       '</a></main>').encode()
        self.b_detail = ('<main><article><h3>' + b.TITLE +
                         '</h3><p>展覽地點：' + b.VENUE +
                         '</p></article></main>').encode()

    def test_a_ticket_adapter_to_real_preview_normalizer(self):
        result = bridge.build_review_envelope("A", self.a_list, self.a_detail, STAMP)
        self.assertEqual(result["decision"], "REVIEW_ONLY_NOT_NATIVE")
        self.assertEqual(result["source_id"], "01")
        self.assertEqual(result["candidate"]["_candidate"]["scope"], "CANDIDATE_PREVIEW_ONLY")
        self.assertEqual(result["candidate"]["date"], "未確認")
        self.assertEqual(result["candidate"]["location"], "未確認")
        self.assertEqual(result["candidate"]["_candidate"]["published"], False)
        self.assertEqual(result["native_get"], 0)
        self.assertTrue(all(not x["native_attested"] for x in result["role_receipts"]))

    def test_b_venue_adapter_to_same_preview_contract(self):
        result = bridge.build_review_envelope("B", self.b_list, self.b_detail, STAMP)
        self.assertEqual(result["decision"], "REVIEW_ONLY_NOT_NATIVE")
        self.assertEqual(result["source_event_id"], b.SID)
        self.assertEqual(result["candidate"]["location"], "未確認")
        self.assertEqual(result["candidate"]["img_url"], None)
        self.assertEqual(result["role_receipts"][0]["role"], "VENUE_ROOM_REVIEW")

    def test_wrong_event_and_sibling_venue_fail_without_candidate(self):
        wrong = self.a_list.replace(b"2026itmgameforum", b"foreign-event")
        out = bridge.build_review_envelope("A", wrong, self.a_detail, STAMP)
        self.assertEqual(out["decision"], "HOLD")
        self.assertIsNone(out["candidate"])
        foreign = ('<main><article><h3>' + b.TITLE +
                   '</h3></article><article><p>展覽地點：' +
                   b.VENUE + '</p></article></main>').encode()
        out = bridge.build_review_envelope("B", self.b_list, foreign, STAMP)
        self.assertEqual(out["decision"], "HOLD")
        self.assertIsNone(out["candidate"])

    def test_reject_bad_timestamp_and_raw_html(self):
        for bad in ("2026-11-07T01:00:00", "nonsense", None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    bridge.build_review_envelope("A", self.a_list, self.a_detail, bad)
        with self.assertRaises(ValueError):
            bridge.build_review_envelope("B", b"x" * (bridge.MAX_HTML + 1),
                                         self.b_detail, STAMP)

    def test_atomic_checksum_and_cas(self):
        envelope = bridge.build_review_envelope("B", self.b_list, self.b_detail, STAMP)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "_isolated_review" / "review_snapshot.json"
            first = bridge.write_isolated_review_lkg(envelope, target, root)
            self.assertEqual(first, json.loads(target.read_text())["sha256"])
            with self.assertRaisesRegex(ValueError, "CAS_MISMATCH"):
                bridge.write_isolated_review_lkg(envelope, target, root)
            self.assertEqual(bridge.write_isolated_review_lkg(
                envelope, target, root, expected_sha=first), first)
            saved = json.loads(target.read_text())
            saved["payload"]["published"] = 1
            target.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, "AUTHORITY_HOLD"):
                bridge.write_isolated_review_lkg(envelope, target, root,
                                                 expected_sha=first)

    def test_cas_cannot_replace_other_source_or_replay_old_bytes(self):
        good = bridge.build_review_envelope("A", self.a_list, self.a_detail, STAMP)
        other = bridge.build_review_envelope("B", self.b_list, self.b_detail, STAMP)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "_isolated_review" / "review_snapshot.json"
            sha = bridge.write_isolated_review_lkg(good, target, root)
            with self.assertRaisesRegex(ValueError, "CROSS_IDENTITY_HOLD"):
                bridge.write_isolated_review_lkg(other, target, root, sha)
            stale = bridge.build_review_envelope(
                "A", self.a_list, self.a_detail, "2026-11-06T01:00:00+00:00")
            with self.assertRaisesRegex(ValueError, "STALE_OBSERVATION_HOLD"):
                bridge.write_isolated_review_lkg(stale, target, root, sha)
            drift = bridge.build_review_envelope(
                "A", self.a_list.replace(b"<main>", b"<main> "),
                self.a_detail, STAMP)
            with self.assertRaisesRegex(ValueError, "SAME_INSTANT_BODY_DRIFT_HOLD"):
                bridge.write_isolated_review_lkg(drift, target, root, sha)
            self.assertEqual(json.loads(target.read_text())["sha256"], sha)

    def test_hold_never_replaces_lkg_or_writes_formal_docs(self):
        good = bridge.build_review_envelope("A", self.a_list, self.a_detail, STAMP)
        bad = bridge.build_review_envelope("A", b"<main/>", self.a_detail, STAMP)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "_isolated_review" / "review_snapshot.json"
            sha = bridge.write_isolated_review_lkg(good, target, root)
            with self.assertRaisesRegex(ValueError, "NON_REVIEW"):
                bridge.write_isolated_review_lkg(bad, target, root, sha)
            self.assertEqual(json.loads(target.read_text())["sha256"], sha)
            with self.assertRaisesRegex(ValueError, "TARGET"):
                bridge.write_isolated_review_lkg(good, root / "docs" /
                                                 "review_snapshot.json", root)

    def test_slot_lease_serializes_cas_and_preserves_other_line(self):
        """Concurrent A writer must HOLD without blocking independent B."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a_good = bridge.build_review_envelope(
                "A", self.a_list, self.a_detail, STAMP)
            b_good = bridge.build_review_envelope(
                "B", self.b_list, self.b_detail, STAMP)
            a_target = root / "_isolated_review" / "A" / "review_snapshot.json"
            b_target = root / "_isolated_review" / "B" / "review_snapshot.json"
            a_sha = bridge.write_isolated_review_lkg(a_good, a_target, root)
            original = a_target.read_bytes()
            lease = a_target.parent / ".review_snapshot.lock"
            lease.mkdir()
            try:
                with self.assertRaisesRegex(ValueError, "CONCURRENT_WRITER_HOLD"):
                    bridge.write_isolated_review_lkg(
                        a_good, a_target, root, expected_sha=a_sha)
                self.assertEqual(a_target.read_bytes(), original)
                self.assertEqual(
                    bridge.write_isolated_review_lkg(b_good, b_target, root),
                    json.loads(b_target.read_text())["sha256"])
            finally:
                lease.rmdir()
            self.assertEqual(
                bridge.write_isolated_review_lkg(
                    a_good, a_target, root, expected_sha=a_sha), a_sha)
            self.assertFalse(lease.exists())

    def test_durable_review_nested_authority_and_monotonic_roles(self):
        """A/B LKG must not regress source roles or hide nested publication."""
        good = bridge.build_review_envelope(
            "B", self.b_list, self.b_detail, STAMP)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "_isolated_review" / "B" / "review_snapshot.json"
            sha = bridge.write_isolated_review_lkg(good, target, root)
            original = target.read_bytes()
            newer = bridge.build_review_envelope(
                "B", self.b_list, self.b_detail, "2026-11-07T02:00:00+00:00")
            newer["role_receipts"] = []
            with self.assertRaisesRegex(ValueError, "ROLE_REGRESSION_HOLD"):
                bridge.write_isolated_review_lkg(newer, target, root, sha)
            for flag in ("published", "golden_accepted", "formal_field_pass"):
                nested = bridge.build_review_envelope(
                    "B", self.b_list, self.b_detail, STAMP)
                nested["candidate"]["_candidate"][flag] = True
                with self.subTest(flag=flag), self.assertRaisesRegex(
                        ValueError, "NESTED_AUTHORITY_HOLD"):
                    bridge.write_isolated_review_lkg(nested, target, root, sha)
            forged = bridge.build_review_envelope(
                "B", self.b_list, self.b_detail, STAMP)
            forged["role_receipts"][0]["native_attested"] = True
            with self.assertRaisesRegex(ValueError, "ROLE_PROVENANCE_HOLD"):
                bridge.write_isolated_review_lkg(forged, target, root, sha)
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(
                bridge.write_isolated_review_lkg(good, target, root, sha), sha)

    def test_existing_alternate_a_b_adapters_have_source_owned_lkg(self):
        """Reuse two existing parsers end-to-end; no native claim or formal write."""
        for line, key in (("A", "A_UDN"), ("B", "B_CERAMICS")):
            with self.subTest(adapter=key), tempfile.TemporaryDirectory() as td:
                source = a.SOURCES[key]
                listing = ('<main><a href="' + source["detail"] + '">' +
                           source["title"] + '</a></main>').encode("utf-8")
                detail = ('<main><article><h2>' + source["title"] +
                          '</h2><p>Official detail</p></article></main>').encode("utf-8")
                envelope = bridge.build_review_envelope(
                    line, listing, detail, STAMP, adapter_key=key)
                self.assertEqual(envelope["decision"], "REVIEW_ONLY_NOT_NATIVE")
                self.assertEqual(envelope["source_event_id"], source["event_id"])
                manifest = {**{k: envelope[k] for k in (
                    "line", "adapter_key", "source_id", "source_event_id",
                    "list_url", "detail_url", "observed_at_utc",
                    "source_attestation")}, **envelope["body_digests"]}
                root = Path(td)
                out = bridge.replay_manifest_to_isolated_lkg(
                    manifest, listing, detail, root)
                self.assertEqual(out["native_get"], 0)
                self.assertEqual(out["formal_accepted_fields"], 0)
                target = root / "_isolated_review" / line / key / "review_snapshot.json"
                self.assertEqual(json.loads(target.read_text())["sha256"],
                                 out["snapshot_sha256"])
                self.assertFalse((root / "docs" / "data.json").exists())
                with self.assertRaisesRegex(ValueError, "ADAPTER_LINE_HOLD"):
                    bridge.replay_manifest_to_isolated_lkg(
                        {**manifest, "adapter_key": "B_NTPC" if line == "A" else "A_UDN"},
                        listing, detail, root, out["snapshot_sha256"])

    def test_accupass_and_zepp_exact_event_pipeline_with_ticket_edge(self):
        """Reuse distinct official-source parsers; caller bytes are not native."""
        a_src = a.SOURCES["A_ACCUPASS"]
        b_src = a.SOURCES["B_ZEPP_TAKASE"]
        cases = [
            ("A", "A_ACCUPASS",
             ('<main><a href="' + a_src["detail"] + '">' +
              a_src["title"] + '</a></main>').encode("utf-8"),
             ('<article><h1>' + a_src["title"] +
              '</h1><p>2026.11.22 (Sun) 13:45 - 17:00</p>' +
              '<p>植境plantārium-複合式空間</p></article>').encode("utf-8"),
             False),
            ("B", "B_ZEPP_TAKASE",
             ('<main><a href="/hall/newtaipei/schedule/single/?rid=160668">' +
              '2026 11.7 SAT 高瀬統也 ' + b_src["title"] +
              ' [OPEN] 17:00 [START] 18:00 READ MORE</a></main>').encode("utf-8"),
             ('<article><h2>' + b_src["title"] + '</h2>' +
              '<a href="' + b_src["public_ticket_event"] +
              '">KKTIX</a></article>').encode("utf-8"),
             True),
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for line, key, listing, detail, has_edge in cases:
                with self.subTest(adapter=key):
                    envelope = bridge.build_review_envelope(
                        line, listing, detail, STAMP, adapter_key=key)
                    self.assertEqual(envelope["decision"], "REVIEW_ONLY_NOT_NATIVE")
                    self.assertEqual(envelope["source_event_id"],
                                     a.SOURCES[key]["event_id"])
                    self.assertEqual(bool(envelope["direct_ticket_edge"]), has_edge)
                    manifest = {**{k: envelope[k] for k in (
                        "line", "adapter_key", "source_id", "source_event_id",
                        "list_url", "detail_url", "observed_at_utc",
                        "source_attestation")}, **envelope["body_digests"]}
                    out = bridge.replay_manifest_to_isolated_lkg(
                        manifest, listing, detail, root)
                    self.assertEqual(out["direct_ticket_edge_review"], int(has_edge))
                    self.assertEqual((out["native_get"],
                                      out["formal_accepted_fields"],
                                      out["golden"], out["published"]), (0, 0, 0, 0))
                    target = root / "_isolated_review" / line / key / "review_snapshot.json"
                    saved = json.loads(target.read_text(encoding="utf-8"))
                    self.assertEqual(saved["sha256"], out["snapshot_sha256"])
                    if has_edge:
                        self.assertEqual(
                            saved["payload"]["direct_ticket_edge"]["target_url"],
                            b_src["public_ticket_event"])
                        # The ticket event edge is not a venue event ID.
                        self.assertEqual(saved["payload"]["source_event_id"], "160668")
                    self.assertFalse((root / "docs" / "data.json").exists())

    def test_manifest_cli_integrates_both_source_adapters(self):
        for line, listing, detail in (
                ("A", self.a_list, self.a_detail),
                ("B", self.b_list, self.b_detail)):
            with self.subTest(line=line), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                envelope = bridge.build_review_envelope(line, listing, detail, STAMP)
                manifest = {**{k: envelope[k] for k in (
                    "line", "source_id", "source_event_id", "list_url",
                    "detail_url", "observed_at_utc", "source_attestation")},
                    **envelope["body_digests"]}
                inbox = root / "_isolated_review" / "inbox"
                inbox.mkdir(parents=True)
                (inbox / "manifest.json").write_text(json.dumps(manifest))
                (inbox / "list.html").write_bytes(listing)
                (inbox / "detail.html").write_bytes(detail)
                with redirect_stdout(io.StringIO()) as output:
                    code = bridge.main([
                        "--repo-root", str(root),
                        "--manifest", str(inbox / "manifest.json"),
                        "--list-html", str(inbox / "list.html"),
                        "--detail-html", str(inbox / "detail.html")])
                self.assertEqual(code, 0)
                result = json.loads(output.getvalue())
                self.assertEqual(result["decision"], "REVIEW_ONLY_NOT_NATIVE")
                self.assertEqual(result["native_get"], 0)
                self.assertEqual(result["formal_accepted_fields"], 0)
                snapshot = root / "_isolated_review" / line / "review_snapshot.json"
                self.assertEqual(json.loads(snapshot.read_text())["sha256"],
                                 result["snapshot_sha256"])
                with self.assertRaisesRegex(ValueError, "CAS_MISMATCH"):
                    bridge.replay_manifest_to_isolated_lkg(
                        manifest, listing, detail, root)

    def test_manifest_tamper_and_hold_preserve_lkg(self):
        envelope = bridge.build_review_envelope("B", self.b_list,
                                                self.b_detail, STAMP)
        manifest = {**{k: envelope[k] for k in (
            "line", "source_id", "source_event_id", "list_url",
            "detail_url", "observed_at_utc", "source_attestation")},
            **envelope["body_digests"]}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            good = bridge.replay_manifest_to_isolated_lkg(
                manifest, self.b_list, self.b_detail, root)
            target = root / "_isolated_review" / "B" / "review_snapshot.json"
            original = target.read_bytes()
            for key, bad in (
                    ("source_event_id", "foreign"),
                    ("detail_url", "https://example.org/checkout"),
                    ("detail_sha256", "0" * 64),
                    ("source_attestation", "NATIVE_HTTP_200")):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    bridge.replay_manifest_to_isolated_lkg(
                        {**manifest, key: bad}, self.b_list, self.b_detail,
                        root, good["snapshot_sha256"])
                self.assertEqual(target.read_bytes(), original)
            held = bridge.replay_manifest_to_isolated_lkg(
                {**manifest, "list_sha256": hashlib.sha256(b"<main/>").hexdigest()},
                b"<main/>", self.b_detail, root, good["snapshot_sha256"])
            self.assertEqual(held["decision"], "HOLD")
            self.assertEqual(target.read_bytes(), original)
            outside = root / "docs"
            outside.mkdir()
            (outside / "list.html").write_bytes(self.b_list)
            with self.assertRaisesRegex(ValueError, "INBOX_PATH_HOLD"):
                bridge._isolated_inbox_file(root, outside / "list.html", 1024)


    def test_dual_line_durable_replay_is_independent_and_symlink_fail_closed(self):
        """Both official-source adapters can retain independent REVIEW LKGs."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            outcomes = {}
            for line, listing, detail in (
                    ("A", self.a_list, self.a_detail),
                    ("B", self.b_list, self.b_detail)):
                envelope = bridge.build_review_envelope(line, listing, detail, STAMP)
                manifest = {**{k: envelope[k] for k in (
                    "line", "source_id", "source_event_id", "list_url",
                    "detail_url", "observed_at_utc", "source_attestation")},
                    **envelope["body_digests"]}
                outcomes[line] = bridge.replay_manifest_to_isolated_lkg(
                    manifest, listing, detail, root)
                self.assertEqual(outcomes[line]["decision"], "REVIEW_ONLY_NOT_NATIVE")
                self.assertEqual(outcomes[line]["native_get"], 0)
            a_path = root / "_isolated_review" / "A" / "review_snapshot.json"
            b_path = root / "_isolated_review" / "B" / "review_snapshot.json"
            self.assertTrue(a_path.is_file())
            self.assertTrue(b_path.is_file())
            a_bytes, b_bytes = a_path.read_bytes(), b_path.read_bytes()
            self.assertNotEqual(a_bytes, b_bytes)
            self.assertEqual(json.loads(a_bytes)["payload"]["line"], "A")
            self.assertEqual(json.loads(b_bytes)["payload"]["line"], "B")
            with self.assertRaisesRegex(ValueError, "CAS_MISMATCH"):
                bridge.replay_manifest_to_isolated_lkg(
                    manifest, listing, detail, root)
            self.assertEqual(a_path.read_bytes(), a_bytes)
            self.assertEqual(b_path.read_bytes(), b_bytes)

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            root = Path(td)
            isolation = root / "_isolated_review"
            try:
                isolation.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unsupported")
            envelope = bridge.build_review_envelope(
                "A", self.a_list, self.a_detail, STAMP)
            with self.assertRaisesRegex(ValueError, "TARGET_ISOLATION_HOLD"):
                bridge.write_isolated_review_lkg(
                    envelope, isolation / "A" / "review_snapshot.json", root)
            self.assertEqual(list(Path(outside).iterdir()), [])


if __name__ == "__main__":
    unittest.main()

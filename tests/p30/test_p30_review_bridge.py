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
from scripts import p30_ab_opentix_ticc_native_once as opentix
from scripts import p30_cloudgate_native_gate as cloudgate

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


    def test_b_cloudgate_exact_1680_postponement_fixed_review_lkg(self):
        # Caller-supplied HTML exercises the existing source-owned adapter.
        # This is NOT a new official native GET or a formal show-date claim.
        listing = ('<main><article><a href="/cgt/theater-event/1680">'
                   + cloudgate.TITLE +
                   '2026.10.17 - 12.19</a></article></main>').encode()
        detail = ('<main><article><h1>' + cloudgate.TITLE +
                  '</h1><p>12月19日(六) 13:30</p>'
                  '<p>原11/14兩場講座延期至12/19</p>'
                  '</article></main>').encode()
        env = bridge.build_review_envelope(
            "B", listing, detail, STAMP, adapter_key="B_CLOUDGATE")
        self.assertEqual((env["source_event_id"], env["decision"]),
                         ("1680", "REVIEW_ONLY_NOT_NATIVE"))
        self.assertEqual({x["role"] for x in env["role_receipts"]},
                         {"EVENT_LOCAL_TITLE_REVIEW",
                          "VENUE_POSTPONEMENT_REVIEW_NOT_SESSION"})
        self.assertEqual((env["native_get"], env["native_body_lkg"],
                          env["formal_accepted_fields"], env["golden"],
                          env["published"]), (0, 0, 0, 0, 0))
        self.assertEqual(env["candidate"]["date"], "未確認")
        self.assertEqual(env["candidate"]["price"], "未確認")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = {k: env[k] for k in (
                "line", "adapter_key", "source_id", "source_event_id",
                "list_url", "detail_url", "observed_at_utc",
                "source_attestation")}
            manifest.update(env["body_digests"])
            saved = bridge.replay_manifest_to_isolated_lkg(
                manifest, listing, detail, root)
            target = root / "_isolated_review" / "B" / "B_CLOUDGATE" / "review_snapshot.json"
            self.assertEqual(json.loads(target.read_text())["sha256"],
                             saved["snapshot_sha256"])
            self.assertFalse((root / "docs").exists())
        foreign = listing.replace(b"/1680", b"/1584")
        denied = bridge.build_review_envelope(
            "B", foreign, detail, STAMP, adapter_key="B_CLOUDGATE")
        self.assertEqual(denied["decision"], "HOLD")
        self.assertIsNone(denied["candidate"])
        sibling = ('<main><article><h1>' + cloudgate.TITLE +
                   '</h1></article><article><p>12月19日</p>'
                   '<p>原11/14兩場講座延期至12/19</p></article></main>').encode()
        held = bridge.build_review_envelope(
            "B", listing, sibling, STAMP, adapter_key="B_CLOUDGATE")
        self.assertEqual(held["decision"], "REVIEW_ONLY_NOT_NATIVE")
        self.assertEqual([x["role"] for x in held["role_receipts"]],
                         ["EVENT_LOCAL_TITLE_REVIEW"])
        self.assertEqual(held["candidate"]["date"], "未確認")

    def test_opentix_exact_id_review_to_isolated_cas_lkg(self):
        src = opentix.SOURCES["A"]
        listing = ('<main><article><a href="' + src["detail"] + '">' +
                   src["title"] + '</a></article></main>').encode("utf-8")
        detail = ('<main><article><h1>' + src["title"] +
                  '</h1></article></main>').encode("utf-8")
        env = bridge.build_review_envelope(
            "A", listing, detail, STAMP, adapter_key="A_OPENTIX")
        self.assertEqual(env["decision"], "REVIEW_ONLY_NOT_NATIVE")
        self.assertEqual((env["source_id"], env["source_event_id"]),
                         ("05", src["event_id"]))
        self.assertEqual((env["native_get"], env["native_body_lkg"],
                          env["formal_accepted_fields"], env["published"]),
                         (0, 0, 0, 0))
        self.assertFalse(env["role_receipts"][0]["native_attested"])
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = {k: env[k] for k in (
                "line", "adapter_key", "source_id", "source_event_id",
                "list_url", "detail_url", "observed_at_utc",
                "source_attestation")}
            manifest.update(env["body_digests"])
            saved = bridge.replay_manifest_to_isolated_lkg(
                manifest, listing, detail, root)
            path = root / "_isolated_review" / "A" / "A_OPENTIX" / "review_snapshot.json"
            self.assertEqual(json.loads(path.read_text())["sha256"],
                             saved["snapshot_sha256"])
            self.assertFalse((root / "docs" / "data.json").exists())
        rejected = bridge.build_review_envelope(
            "A", b"<main><a href='/event/999'>wrong</a></main>",
            detail, STAMP, adapter_key="A_OPENTIX")
        self.assertEqual(rejected["decision"], "HOLD")
        self.assertIsNone(rejected["candidate"])

    def test_opentix_event_local_venue_receipt_remains_non_native(self):
        src = opentix.SOURCES["A"]
        listing = ('<main><article><a href="' + src["detail"] + '">' +
                   src["title"] + '</a></article></main>').encode()
        detail = ('<main><article><h1>' + src["title"] +
                  '</h1><p>場館：' + src["venue"] +
                  '</p></article></main>').encode()
        env = bridge.build_review_envelope(
            "A", listing, detail, STAMP, adapter_key="A_OPENTIX")
        self.assertEqual({x["role"] for x in env["role_receipts"]},
                         {"EVENT_LOCAL_TITLE_REVIEW",
                          "VENUE_ROOM_REVIEW_NOT_SESSION"})
        self.assertEqual((env["native_get"], env["native_body_lkg"],
                          env["formal_accepted_fields"], env["golden"],
                          env["published"]), (0, 0, 0, 0, 0))
        self.assertTrue(all(x["native_attested"] is False and
                            x["formal_accepted"] is False
                            for x in env["role_receipts"]))

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

    def test_checksum_valid_preview_field_injection_is_quarantined(self):
        """A/B caller receipts cannot silently become display price/date/venue."""
        for line, listing, detail in (
                ("A", self.a_list, self.a_detail),
                ("B", self.b_list, self.b_detail)):
            envelope = bridge.build_review_envelope(line, listing, detail, STAMP)
            self.assertEqual(envelope["decision"], "REVIEW_ONLY_NOT_NATIVE")
            changes = {
                "price": lambda c: c.__setitem__("price", "NT$100"),
                "date": lambda c: c.__setitem__("date", "2026-11-22"),
                "remote_image": lambda c: c.__setitem__("img_url", "https://example.com/x.jpg"),
                "extra_property": lambda c: c.__setitem__("sale_status", "AVAILABLE"),
                "foreign_title": lambda c: c.__setitem__("title", "FOREIGN EVENT"),
                "field_evidence": lambda c: c["_candidate"].__setitem__(
                    "field_evidence", {"price": {"decision": "REVIEW"}}),
                "foreign_sources": lambda c: c["_candidate"].__setitem__(
                    "sources", ["https://example.com/foreign"]),
            }
            for label, mutate in changes.items():
                with self.subTest(line=line, injection=label):
                    forged = json.loads(json.dumps(envelope, ensure_ascii=False))
                    mutate(forged["candidate"])
                    sealed = {
                        "payload": forged,
                        "sha256": hashlib.sha256(bridge._canonical(forged)).hexdigest(),
                    }
                    with self.assertRaisesRegex(
                            ValueError, "REVIEW_SNAPSHOT_PREVIEW_FIELD_AUTHORITY_HOLD"):
                        bridge._validate_snapshot(sealed)
                    with tempfile.TemporaryDirectory() as td:
                        root = Path(td)
                        target = (root / "_isolated_review" / line /
                                  "review_snapshot.json")
                        with self.assertRaisesRegex(
                                ValueError, "REVIEW_SNAPSHOT_PREVIEW_FIELD_AUTHORITY_HOLD"):
                            bridge.write_isolated_review_lkg(forged, target, root)
                        self.assertFalse(target.exists())

    def test_caller_supplied_review_cannot_forge_native_body_lkg(self):
        """A checksum-valid caller envelope is never native source evidence."""
        envelope = bridge.build_review_envelope(
            "B", self.b_list, self.b_detail, STAMP)
        self.assertEqual(envelope["native_body_lkg"], 0)
        forged = {**envelope, "native_body_lkg": 1}
        sealed = {"payload": forged,
                  "sha256": hashlib.sha256(bridge._canonical(forged)).hexdigest()}
        with self.assertRaisesRegex(ValueError, "REVIEW_SNAPSHOT_AUTHORITY_HOLD"):
            bridge._validate_snapshot(sealed)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "_isolated_review" / "B" / "review_snapshot.json"
            with self.assertRaisesRegex(ValueError, "REVIEW_SNAPSHOT_AUTHORITY_HOLD"):
                bridge.write_isolated_review_lkg(forged, target, root)
            self.assertFalse(target.exists())

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


    def test_tpac_event_2072_conflicting_official_dates_review_cas(self):
        """Exact same event identity is not permission to accept date/session."""
        from scripts import p30_tpac_event_source as tpac
        listing = ('<main><article><a href="/event/2072">' + tpac.TITLE +
                   '</a><p>2026-11-10 - 2026-11-12</p></article></main>').encode()
        detail = ('<main><article><h1>' + tpac.TITLE +
                  '</h1><p>2026-11-11 - 2026-11-13</p></article></main>').encode()
        verdict = tpac.inspect_caller_html(listing.decode(), detail.decode())
        self.assertEqual(verdict["same_id_review"], 1)
        self.assertTrue(verdict["date_conflict"])
        self.assertEqual(verdict["field_roles"], ["EVENT_TITLE_REVIEW"])
        self.assertEqual(verdict["first_failure"],
                         "TPAC_EVENT_OFFICIAL_LIST_DETAIL_DATE_CONFLICT_HOLD")
        envelope = bridge.build_review_envelope(
            "B", listing, detail, STAMP, adapter_key="B_TPAC_EVENT2072")
        self.assertEqual(envelope["decision"], "REVIEW_ONLY_NOT_NATIVE")
        self.assertEqual(envelope["first_failure"], verdict["first_failure"])
        self.assertEqual([r["role"] for r in envelope["role_receipts"]],
                         ["EVENT_TITLE_REVIEW"])
        self.assertIn(verdict["first_failure"],
                      envelope["candidate"]["_candidate"]["hold_reasons"])
        manifest = {**{k: envelope[k] for k in (
            "line", "adapter_key", "source_id", "source_event_id",
            "list_url", "detail_url", "observed_at_utc",
            "source_attestation")}, **envelope["body_digests"]}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = bridge.replay_manifest_to_isolated_lkg(
                manifest, listing, detail, root)
            self.assertEqual((out["native_get"], out["formal_accepted_fields"],
                              out["golden"], out["published"]), (0, 0, 0, 0))
            target = root / "_isolated_review/B/B_TPAC_EVENT2072/review_snapshot.json"
            before = target.read_bytes()
            self.assertEqual(json.loads(before)["sha256"], out["snapshot_sha256"])
            with self.assertRaisesRegex(ValueError, "REVIEW_MANIFEST_BODY_SHA_HOLD"):
                bridge.replay_manifest_to_isolated_lkg(
                    manifest, listing.replace(b"/event/2072", b"/event/2073"),
                    detail, root, out["snapshot_sha256"])
            self.assertEqual(target.read_bytes(), before)
        # A sibling event's date cannot be borrowed into this event owner.
        no_date = ('<main><article><a href="/event/2072">' + tpac.TITLE +
                   '</a></article><article><p>2026-11-11 - 2026-11-13'
                   '</p></article></main>')
        self.assertEqual(tpac.inspect_caller_html(no_date, detail.decode())[
            "first_failure"], "TPAC_EVENT_DATE_RANGE_LOCAL_AUTHORITY_HOLD")
        ghost = '<main><script><article><a href="/event/2072">' + tpac.TITLE + '</a></article></script></main>'
        self.assertEqual(tpac.inspect_caller_html(ghost, detail.decode())[
            "same_id_review"], 0)
        aligned = detail.replace(b"2026-11-11 - 2026-11-13",
                                 b"2026-11-10 - 2026-11-12")
        positive = tpac.inspect_caller_html(listing.decode(), aligned.decode())
        self.assertEqual(positive["field_roles"],
                         ["EVENT_TITLE_REVIEW", "VENUE_EVENT_DATE_RANGE_REVIEW_NOT_SESSION"])
        self.assertEqual(positive["formal_accepted_fields"], 0)

    def test_isolated_inbox_ancestor_symlink_and_utc_receipt_fail_closed(self):
        """Caller bytes cannot escape the repo or masquerade as UTC evidence."""
        self.assertEqual(bridge._observed("2026-11-07T12:00:00Z"),
                         "2026-11-07T12:00:00Z")
        self.assertEqual(bridge._observed("2026-11-07T12:00:00+00:00"),
                         "2026-11-07T12:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "OBSERVED_AT_INVALID_HOLD"):
            bridge._observed("2026-11-07T20:00:00+08:00")
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as ext:
            root, outside = Path(td), Path(ext)
            inbox = outside / "inbox"
            inbox.mkdir()
            secret = inbox / "manifest.json"
            secret.write_text('{"external":true}', encoding="utf-8")
            isolation = root / "_isolated_review"
            try:
                isolation.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unsupported")
            with self.assertRaisesRegex(ValueError, "REVIEW_INBOX_PATH_HOLD"):
                bridge._isolated_inbox_file(root, isolation / "inbox" / "manifest.json", 1024)
            self.assertEqual(secret.read_text(encoding="utf-8"), '{"external":true}')
            self.assertFalse((root / "docs").exists())

if __name__ == "__main__":
    unittest.main()

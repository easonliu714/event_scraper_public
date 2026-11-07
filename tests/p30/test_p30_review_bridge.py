"""Executable A/B same-ID -> preview REVIEW -> checksum/CAS LKG integration."""
import json
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


if __name__ == "__main__":
    unittest.main()

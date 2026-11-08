"""Real fixed A/B CLI-to-LKG integration, caller bytes only (NO NATIVE GET)."""
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts import p30_ab_kktix_fuzhong_native as tickets
from scripts import p30_tpac_event_source as tpac
from scripts import p30_review_bridge as bridge
from scripts import p30_ab_fixed_review_workflow as workflow
from scripts import p30_ab_opentix_ticc_native_once as opentix

STAMP = "2026-11-07T11:55:00+00:00"


class FixedABWorkflowTests(unittest.TestCase):
    def _inbox(self, root, a_adapter="A_OPENTIX"):
        inbox = root / "_isolated_review" / "inbox"
        inbox.mkdir(parents=True)
        a = (opentix.SOURCES["A"] if a_adapter == "A_OPENTIX"
             else tickets.SOURCES["A_ACCUPASS"])
        pairs = {
            "A": (a_adapter,
                  ('<main><article><a href="' + a["detail"] + '">' +
                   a["title"] + '</a></article></main>').encode(),
                  ('<main><article><h1>' + a["title"] +
                   '</h1><p>官方公開活動介紹</p></article></main>').encode()),
            "B": ("B_TPAC_EVENT2072",
                  ('<main><article><a href="/event/2072">' + tpac.TITLE +
                   '</a><p>2026-11-10 - 2026-11-12</p></article></main>').encode(),
                  ('<main><article><h1>' + tpac.TITLE +
                   '</h1><p>2026-11-11 - 2026-11-13</p></article></main>').encode()),
        }
        inputs = {}
        for line, (key, listing, detail) in pairs.items():
            envelope = bridge.build_review_envelope(
                line, listing, detail, STAMP, adapter_key=key)
            self.assertEqual(envelope["decision"], "REVIEW_ONLY_NOT_NATIVE")
            manifest = {k: envelope[k] for k in (
                "line", "adapter_key", "source_id", "source_event_id",
                "list_url", "detail_url", "observed_at_utc", "source_attestation")}
            manifest.update(envelope["body_digests"])
            names = {k: inbox / (line + "_" + k) for k in
                     ("manifest", "list_html", "detail_html")}
            names["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
            names["list_html"].write_bytes(listing)
            names["detail_html"].write_bytes(detail)
            inputs[line] = {**names, "expected_sha": None}
        return inputs

    def test_fixed_a_opentix_b_tpac_end_to_end_and_cas(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root)
            out = workflow.run_fixed_ab(root, inputs)
            self.assertEqual(out["decision"], "REVIEW_ONLY_NOT_NATIVE")
            self.assertEqual((out["native_get"], out["native_body_lkg"],
                              out["formal_accepted_fields"], out["golden"],
                              out["published"]), (0, 0, 0, 0, 0))
            for line in ("A", "B"):
                entry = out["lines"][line]
                path = (root / "_isolated_review" / line /
                        entry["adapter_key"] / "review_snapshot.json")
                saved = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(saved["sha256"], entry["snapshot_sha256"])
                self.assertEqual(saved["payload"]["source_event_id"],
                                 entry["source_event_id"])
                self.assertEqual(saved["payload"]["source_attestation"],
                                 "CALLER_SUPPLIED_NOT_NATIVE")
                self.assertFalse(saved["payload"]["candidate"]["_candidate"]["published"])
                inputs[line]["expected_sha"] = entry["snapshot_sha256"]
            b = out["lines"]["B"]
            self.assertEqual(b["source_event_id"], "2072")
            self.assertEqual(b["role_receipts"], 1)
            again = workflow.run_fixed_ab(root, inputs)
            self.assertEqual(again["lines"]["A"]["snapshot_sha256"],
                             out["lines"]["A"]["snapshot_sha256"])
            self.assertEqual(again["lines"]["B"]["snapshot_sha256"],
                             out["lines"]["B"]["snapshot_sha256"])
            self.assertFalse((root / "docs" / "data.json").exists())

    def test_prior_accupass_fixed_pair_remains_covered(self):
        """OPENTIX integration must not regress the accepted ACCUPASS path."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root, "A_ACCUPASS")
            out = workflow.run_fixed_ab(root, inputs)
            self.assertEqual(out["decision"], "REVIEW_ONLY_NOT_NATIVE")
            self.assertEqual(out["lines"]["A"]["adapter_key"], "A_ACCUPASS")
            self.assertEqual(out["native_get"], 0)
            self.assertEqual(out["formal_accepted_fields"], 0)
            self.assertFalse((root / "docs" / "data.json").exists())

    def test_invalid_b_digest_preflight_never_writes_a(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root)
            path = inputs["B"]["manifest"]
            manifest = json.loads(path.read_text())
            manifest["detail_sha256"] = "0" * 64
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "BODY_DIGEST_HOLD"):
                workflow.run_fixed_ab(root, inputs)
            self.assertEqual(list((root / "_isolated_review").rglob("review_snapshot.json")), [])

    def test_stale_b_cas_preflight_preserves_both_snapshots(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root)
            out = workflow.run_fixed_ab(root, inputs)
            paths = {line: (root / "_isolated_review" / line /
                             out["lines"][line]["adapter_key"] /
                             "review_snapshot.json") for line in ("A", "B")}
            before = {line: path.read_bytes() for line, path in paths.items()}
            inputs["A"]["expected_sha"] = out["lines"]["A"]["snapshot_sha256"]
            inputs["B"]["expected_sha"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "PREFLIGHT_CAS_HOLD"):
                workflow.run_fixed_ab(root, inputs)
            self.assertEqual({line: path.read_bytes() for line, path in paths.items()},
                             before)

    def test_stale_b_preflight_blocks_new_a_observation_without_partial_commit(self):
        """A valid later A receipt must not commit if B is already stale."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root)
            initial = workflow.run_fixed_ab(root, inputs)
            paths = {line: (root / "_isolated_review" / line /
                            initial["lines"][line]["adapter_key"] /
                            "review_snapshot.json") for line in ("A", "B")}
            before = {line: path.read_bytes() for line, path in paths.items()}
            for line, observed in (
                    ("A", "2026-11-08T00:55:00+00:00"),
                    ("B", "2026-11-06T00:55:00+00:00")):
                inputs[line]["expected_sha"] = initial["lines"][line]["snapshot_sha256"]
                manifest_path = inputs[line]["manifest"]
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["observed_at_utc"] = observed
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "REVIEW_LKG_STALE_OBSERVATION_HOLD"):
                workflow.run_fixed_ab(root, inputs)
            self.assertEqual({line: path.read_bytes() for line, path in paths.items()},
                             before)

    def test_cli_runs_fixed_pair_and_no_formal_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root)
            argv = ["--repo-root", str(root)]
            for line in ("A", "B"):
                for field, arg in (("manifest", "manifest"),
                                   ("list_html", "list-html"),
                                   ("detail_html", "detail-html")):
                    argv.extend(["--" + line.lower() + "-" + arg,
                                 str(inputs[line][field])])
            with redirect_stdout(io.StringIO()) as stdout:
                code = workflow.main(argv)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["decision"],
                             "REVIEW_ONLY_NOT_NATIVE")
            self.assertFalse((root / "docs").exists())

    def test_immutable_pair_receipt_binds_both_source_snapshots(self):
        """A/B same-ID LKG has a durable source-bound pair receipt."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root, "A_ACCUPASS")
            out = workflow.run_fixed_ab(root, inputs)
            self.assertEqual(out["decision"], "REVIEW_ONLY_NOT_NATIVE")
            path = root / out["pair_receipt_path"]
            sealed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(sealed["sha256"], out["pair_receipt_sha256"])
            self.assertEqual(hashlib.sha256(bridge._canonical(
                sealed["payload"])).hexdigest(), sealed["sha256"])
            self.assertEqual(set(sealed["payload"]["lines"]), {"A", "B"})
            for line in ("A", "B"):
                evidence = sealed["payload"]["lines"][line]
                self.assertEqual(evidence["snapshot_sha256"],
                                 out["lines"][line]["snapshot_sha256"])
                self.assertEqual(evidence["source_event_id"],
                                 out["lines"][line]["source_event_id"])
                self.assertEqual(evidence["source_attestation"],
                                 "CALLER_SUPPLIED_NOT_NATIVE")
                inputs[line]["expected_sha"] = out["lines"][line]["snapshot_sha256"]
            self.assertEqual(sealed["payload"]["native_get"], 0)
            self.assertEqual(sealed["payload"]["formal_accepted_fields"], 0)
            self.assertEqual(sealed["payload"]["golden"], 0)
            self.assertEqual(sealed["payload"]["published"], 0)
            again = workflow.run_fixed_ab(root, inputs)
            self.assertEqual(again["pair_receipt_sha256"], sealed["sha256"])
            self.assertEqual(path.read_bytes(), bridge._canonical(sealed) + b"\n")
            self.assertFalse((root / "docs").exists())

    def test_tampered_pair_receipt_holds_without_publication(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root)
            first = workflow.run_fixed_ab(root, inputs)
            path = root / first["pair_receipt_path"]
            path.write_bytes(b"tampered historical receipt\n")
            for line in ("A", "B"):
                inputs[line]["expected_sha"] = first["lines"][line]["snapshot_sha256"]
            result = workflow.run_fixed_ab(root, inputs)
            self.assertEqual(result["decision"], "PARTIAL_HOLD")
            self.assertIn("AB_FIXED_PAIR_RECEIPT_COLLISION_HOLD",
                          result["first_failure"])
            self.assertEqual(path.read_bytes(), b"tampered historical receipt\n")
            self.assertFalse((root / "docs").exists())



    def test_independent_pair_verifier_and_read_only_cli(self):
        """Independent audit verifies both exact slots without a new write."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root)
            committed = workflow.run_fixed_ab(root, inputs)
            receipt = root / committed["pair_receipt_path"]
            before = receipt.read_bytes()
            verified = workflow.verify_pair_receipt(
                root, committed["pair_receipt_sha256"])
            self.assertEqual(verified["decision"],
                             "VERIFIED_REVIEW_ONLY_NOT_NATIVE")
            self.assertEqual(set(verified["lines"]), {"A", "B"})
            self.assertEqual(verified["native_get"], 0)
            self.assertEqual(verified["formal_accepted_fields"], 0)
            self.assertEqual(verified["golden"], 0)
            self.assertEqual(verified["published"], 0)
            with redirect_stdout(io.StringIO()) as output:
                exit_code = workflow.main([
                    "--repo-root", str(root), "--verify-pair-sha",
                    committed["pair_receipt_sha256"]])
            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(output.getvalue())["decision"],
                             "VERIFIED_REVIEW_ONLY_NOT_NATIVE")
            self.assertEqual(receipt.read_bytes(), before)
            self.assertFalse((root / "docs").exists())

    def test_pair_verifier_rejects_tampered_slot_without_changing_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root)
            committed = workflow.run_fixed_ab(root, inputs)
            receipt = root / committed["pair_receipt_path"]
            before = receipt.read_bytes()
            target = (root / "_isolated_review" / "B" /
                      committed["lines"]["B"]["adapter_key"] /
                      "review_snapshot.json")
            target.write_bytes(b'{"payload": {}, "sha256": "bad"}')
            with self.assertRaisesRegex(
                    ValueError, "AB_FIXED_VERIFY_SLOT_VALIDATION_HOLD"):
                workflow.verify_pair_receipt(
                    root, committed["pair_receipt_sha256"])
            self.assertEqual(receipt.read_bytes(), before)
            self.assertFalse((root / "docs").exists())

    def test_pair_verifier_rejects_receipt_byte_drift_and_mixed_write_cli(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inbox(root)
            committed = workflow.run_fixed_ab(root, inputs)
            receipt = root / committed["pair_receipt_path"]
            receipt.write_bytes(receipt.read_bytes() + b"\n")
            with self.assertRaisesRegex(
                    ValueError, "AB_FIXED_VERIFY_RECEIPT_CANONICAL_HOLD"):
                workflow.verify_pair_receipt(
                    root, committed["pair_receipt_sha256"])
            with redirect_stdout(io.StringIO()) as output:
                code = workflow.main([
                    "--repo-root", str(root), "--verify-pair-sha",
                    committed["pair_receipt_sha256"],
                    "--a-manifest", str(inputs["A"]["manifest"])])
            self.assertEqual(code, 49)
            self.assertIn("AB_FIXED_VERIFY_MIXED_WRITE_INPUT_HOLD",
                          json.loads(output.getvalue())["first_failure"])
            self.assertFalse((root / "docs").exists())



if __name__ == "__main__":
    unittest.main()

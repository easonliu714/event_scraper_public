"""Rotated A/B first-party adapters -> durable non-native REVIEW pair."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts import p30_dual_native_rotation as rotation
from scripts import p30_review_bridge as bridge
from scripts import p30_ab_fixed_review_workflow as fixed

STAMP = "2026-11-08T07:00:00+00:00"

class NextSourceFixedIntegration(unittest.TestCase):
    def _inputs(self, root):
        inbox = root / "_isolated_review" / "inbox"
        inbox.mkdir(parents=True)
        inputs = {}
        for line, adapter in (("A", "A_TIXCRAFT_NEXT"),
                              ("B", "B_ZEPP_NEXT")):
            cfg = rotation.NEXT[line]
            listing = ('<main><article><a href="' + cfg["detail"] + '">' +
                       cfg["title"] + '</a></article></main>').encode()
            detail = ('<main><article><h1>' + cfg["title"] +
                      '</h1><p>' + cfg["venue"] +
                      '</p></article></main>').encode()
            env = bridge.build_review_envelope(
                line, listing, detail, STAMP, adapter_key=adapter)
            self.assertEqual(env["decision"], "REVIEW_ONLY_NOT_NATIVE")
            self.assertEqual({r["role"] for r in env["role_receipts"]},
                             {"SOURCE_EVENT_TITLE_REVIEW", "SOURCE_VENUE_REVIEW"})
            self.assertEqual((env["native_get"], env["native_body_lkg"],
                              env["formal_accepted_fields"], env["golden"],
                              env["published"]), (0, 0, 0, 0, 0))
            self.assertEqual(env["candidate"]["date"], "未確認")
            self.assertEqual(env["candidate"]["price"], "未確認")
            manifest = {k: env[k] for k in (
                "line", "adapter_key", "source_id", "source_event_id",
                "list_url", "detail_url", "observed_at_utc", "source_attestation")}
            manifest.update(env["body_digests"])
            paths = {}
            for key, value in (("manifest", json.dumps(manifest).encode()),
                               ("list_html", listing), ("detail_html", detail)):
                path = inbox / (line + "_" + key)
                path.write_bytes(value)
                paths[key] = path
            inputs[line] = {**paths, "expected_sha": None}
        return inputs

    def _rebind(self, inputs, line, name, body):
        inputs[line][name].write_bytes(body)
        manifest_path = inputs[line]["manifest"]
        manifest = json.loads(manifest_path.read_text())
        manifest["list_sha256" if name == "list_html" else "detail_sha256"] = (
            hashlib.sha256(body).hexdigest())
        manifest_path.write_text(json.dumps(manifest))

    def test_pair_cas_receipt_readback_and_formal_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inputs(root)
            out = fixed.run_fixed_ab(root, inputs)
            self.assertEqual(out["decision"], "REVIEW_ONLY_NOT_NATIVE")
            self.assertEqual((out["native_get"], out["native_body_lkg"],
                              out["formal_accepted_fields"], out["golden"],
                              out["published"]), (0, 0, 0, 0, 0))
            self.assertEqual(fixed.verify_pair_receipt(
                root, out["pair_receipt_sha256"])["decision"],
                "VERIFIED_REVIEW_ONLY_NOT_NATIVE")
            for line in ("A", "B"):
                slot = (root / "_isolated_review" / line /
                        out["lines"][line]["adapter_key"] / "review_snapshot.json")
                payload = json.loads(slot.read_text())["payload"]
                self.assertEqual(payload["source_event_id"], rotation.NEXT[line]["id"])
                self.assertEqual(payload["detail_url"], rotation.NEXT[line]["detail"])
                self.assertEqual(payload["candidate"]["location"], "未確認")
                self.assertEqual(payload["candidate"]["_candidate"]["sessions"], [])
                inputs[line]["expected_sha"] = out["lines"][line]["snapshot_sha256"]
            self.assertEqual(fixed.run_fixed_ab(root, inputs)["pair_receipt_sha256"],
                             out["pair_receipt_sha256"])
            self.assertFalse((root / "docs").exists())

    def test_foreign_id_or_sibling_venue_blocks_both_slots(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = self._inputs(root)
            foreign = inputs["A"]["list_html"].read_bytes().replace(
                b"/26_minhyun", b"/26_foreign")
            self._rebind(inputs, "A", "list_html", foreign)
            with self.assertRaisesRegex(ValueError, "AB_FIXED_EVENT_LOCAL_HOLD"):
                fixed.run_fixed_ab(root, inputs)
            self.assertFalse((root / "_isolated_review" / "A" /
                              "A_TIXCRAFT_NEXT").exists())
            cfg = rotation.NEXT["A"]
            good = ('<main><article><a href="' + cfg["detail"] + '">' +
                    cfg["title"] + '</a></article></main>').encode()
            self._rebind(inputs, "A", "list_html", good)
            cfg = rotation.NEXT["B"]
            sibling = ('<main><article><h1>' + cfg["title"] +
                       '</h1></article><article><p>' + cfg["venue"] +
                       '</p></article></main>').encode()
            self._rebind(inputs, "B", "detail_html", sibling)
            with self.assertRaisesRegex(ValueError, "AB_FIXED_EVENT_LOCAL_HOLD"):
                fixed.run_fixed_ab(root, inputs)
            self.assertFalse((root / "_isolated_review" / "A" /
                              "A_TIXCRAFT_NEXT").exists())
            self.assertFalse((root / "docs").exists())

if __name__ == "__main__":
    unittest.main()

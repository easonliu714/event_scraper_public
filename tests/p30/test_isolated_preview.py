"""P30-G1 immutable Preview historical snapshot and path safety gates (offline only)."""
import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PWA = ROOT / "docs" / "p30-preview"
ORIGINAL = ROOT / "docs" / "data.json"
EXPECTED_PREVIEW_SHA = "ef39c6be44a3f26c30bc3ce13f41548d1bd6b6408af8e872eb55fff360fea43b"
EXPECTED_PREVIEW_BLOB = "c64a72bafd32f1248c53acd83279a33eaca4c41b"
EXPECTED_SOURCE_BLOB = "7fc4fe32567a57fd504483eeb9a8b9e10b568ea4"
EXPECTED_SOURCE_SHA = "d812b6872bb2959b101d03ae659d84f3ea899fae04ae227acad9f40969d0823b"


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()


def validate_manifest(cfg):
    if cfg.get("kind") != "EVENTRADAR_P30_IMMUTABLE_PREVIEW_SNAPSHOT":
        raise ValueError("HOLD_BAD_MANIFEST_KIND")
    if cfg.get("source_main_sha") != "03e515d65e827d5ed67fe341d079907a96bf784a":
        raise ValueError("HOLD_PREVIEW_LINEAGE")
    if cfg.get("preview_rows") != 9850 or cfg.get("preview_bytes") != 5161754:
        raise ValueError("HOLD_PREVIEW_SNAPSHOT_DIMENSION")
    if cfg.get("preview_data_sha256") != EXPECTED_PREVIEW_SHA:
        raise ValueError("HOLD_PREVIEW_SHA")
    if cfg.get("preview_data_git_blob") != EXPECTED_PREVIEW_BLOB:
        raise ValueError("HOLD_PREVIEW_BLOB")
    expected = ["data-parts/part_{:02d}.txt".format(i) for i in range(13)]
    if cfg.get("parts") != expected:
        raise ValueError("HOLD_PART_ORDER_OR_PATH")
    if len(cfg.get("part_git_blobs", [])) != len(expected):
        raise ValueError("HOLD_PART_COUNT")
    if not all(re.fullmatch(r"[0-9a-f]{40}", s) for s in cfg["part_git_blobs"]):
        raise ValueError("HOLD_PART_BLOB_FORMAT")
    return expected


def reassemble_snapshot(cfg):
    partpaths = validate_manifest(cfg)
    fragments = []
    for name, sha in zip(partpaths, cfg["part_git_blobs"]):
        data = (PWA / name).read_bytes()
        if git_blob_sha(data) != sha:
            raise ValueError("HOLD_PART_BLOB_TAMPER")
        fragments.append(data)
    result = b"".join(fragments)
    if len(result) != cfg["preview_bytes"]:
        raise ValueError("HOLD_REASSEMBLED_BYTE_SIZE")
    if hashlib.sha256(result).hexdigest() != cfg["preview_data_sha256"]:
        raise ValueError("HOLD_REASSEMBLED_SHA256")
    if git_blob_sha(result) != cfg["preview_data_git_blob"]:
        raise ValueError("HOLD_REASSEMBLED_GIT_BLOB")
    return result


class TestP30IsolatedPreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((PWA / "snapshot_manifest.json").read_text("utf-8"))
        cls.preview_raw = reassemble_snapshot(cls.manifest)
        cls.preview = json.loads(cls.preview_raw)
        cls.source_raw = ORIGINAL.read_bytes()
        cls.source = json.loads(cls.source_raw)

    def test_preview_bytes_sha256_git_blob_and_9850_rows(self):
        self.assertEqual(len(self.preview_raw), 5161754)
        self.assertEqual(hashlib.sha256(self.preview_raw).hexdigest(), EXPECTED_PREVIEW_SHA)
        self.assertEqual(git_blob_sha(self.preview_raw), EXPECTED_PREVIEW_BLOB)
        self.assertEqual(len(self.preview), 9850)
        self.assertEqual(len({r["url"] for r in self.preview}), 9850)

    def test_source_root_data_unchanged(self):
        self.assertEqual(git_blob_sha(self.source_raw), EXPECTED_SOURCE_BLOB)
        self.assertEqual(hashlib.sha256(self.source_raw).hexdigest(), EXPECTED_SOURCE_SHA)
        self.assertEqual(len(self.source), 8436)
        self.assertEqual(len({r["url"] for r in self.source}), 8436)

    def test_cross_repository_url_parity(self):
        s = {r["url"] for r in self.source}
        p = {r["url"] for r in self.preview}
        self.assertEqual(len(s & p), 7914)
        self.assertEqual(len(s - p), 522)
        self.assertEqual(len(p - s), 1936)

    def test_historical_status_manifest(self):
        status = json.loads((PWA / "preview_status.json").read_text("utf-8"))
        self.assertTrue(status["public_unverified"])
        self.assertEqual(status["preview_rows"], 9850)
        self.assertEqual(status["preview_data_sha256"], EXPECTED_PREVIEW_SHA)

    def test_pwa_path_and_safety_contract(self):
        html = (PWA / "index.html").read_text("utf-8")
        manifest = json.loads((PWA / "manifest.json").read_text("utf-8"))
        self.assertIn("loadIsolatedSnapshot()", html)
        self.assertIn("snapshot_manifest.json", html)
        self.assertIn("data-parts/part_", html)
        self.assertIn("P30 隔離整併候選", html)
        self.assertIn("PREVIEW_NOTIFICATIONS_OFF", html)
        self.assertIn("event_visibility.js", html)
        self.assertIn("eventgo_period_gate.js", html)
        self.assertNotIn("fetch(`data.json", html)
        self.assertEqual(manifest["start_url"], "./index.html")
        self.assertEqual(manifest["scope"], "./")
        self.assertIn("測試", manifest["name"])
        self.assertFalse((PWA / "data.json").exists(), "No fake or overwritten snapshot data.json")

    def test_negative_manifest_order_and_digests(self):
        for field, bad in [
            ("kind", "WRONG"),
            ("preview_rows", 9849),
            ("preview_bytes", 42),
            ("preview_data_sha256", "0" * 64),
            ("preview_data_git_blob", "0" * 40),
            ("source_main_sha", "0" * 40),
        ]:
            with self.subTest(field=field):
                mutated = copy.deepcopy(self.manifest)
                mutated[field] = bad
                with self.assertRaises(ValueError):
                    validate_manifest(mutated)
        mutated = copy.deepcopy(self.manifest)
        mutated["parts"][0], mutated["parts"][1] = mutated["parts"][1], mutated["parts"][0]
        with self.assertRaises(ValueError):
            validate_manifest(mutated)
        self.assertNotEqual(
            hashlib.sha256(b"X" + self.preview_raw[1:]).hexdigest(),
            EXPECTED_PREVIEW_SHA,
        )


if __name__ == "__main__":
    unittest.main()

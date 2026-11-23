"""No-network, source-owned KKTIX and ACCUPASS LIST->DETAIL adapter regressions."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.p30_offline_source_adapters import replay_offline_sources


class TwoProviderOfflineAdapterTests(unittest.TestCase):
    def _fixture(self, root):
        stamp = "2026-11-23T10:00:00+08:00"
        manifest = {"mode": "SEALED_OFFLINE_REPLAY_ONLY", "sources": {}}
        for provider, base, path in (
            ("kktix", "https://kktix.com", "/events/abc123"),
            ("accupass", "https://www.accupass.com", "/event/abc123"),
        ):
            title = "已封存同一活動 ID 測試 " + provider
            entry_url = base + path
            if provider == "kktix":
                listing = ('<a href="' + path + '" title="' + title +
                           '"><span class="name">' + title + '</span></a>').encode()
            else:
                listing = ('<a href="' + path + '"><h3>' + title +
                           '</h3></a>').encode()
            detail = ('<article><h1>' + title + '</h1>'
                      '<p>日期／票價尚未驗證</p></article>').encode()
            lp, dp = provider + "_list.html", provider + "_detail.html"
            (root / lp).write_bytes(listing)
            (root / dp).write_bytes(detail)
            def receipt(raw, url):
                return {"evidence_class": "SEALED_OFFLINE_FIXTURE_ONLY",
                        "source_url": url,
                        "body_sha256": hashlib.sha256(raw).hexdigest(),
                        "observed_at": stamp}
            manifest["sources"][provider] = {
                "list_file": lp, "list_receipt": receipt(listing, base + "/"),
                "details": {"abc123": {
                    "detail_file": dp, "receipt": receipt(detail, entry_url)}},
            }
        return manifest

    def test_two_platforms_same_id_are_independent_and_never_publish(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture = self._fixture(root)
            result = replay_offline_sources(fixture, root)
            self.assertEqual(set(result["records"]), {"kktix:abc123", "accupass:abc123"})
            self.assertEqual(result["counts"]["review_identities"], 2)
            self.assertEqual(result["source_states"], {
                "kktix": "REVIEW_IDENTITY_ONLY",
                "accupass": "REVIEW_IDENTITY_ONLY"})
            for provider in ("kktix", "accupass"):
                row = result["records"][provider + ":abc123"]
                title = row["fields"]["title"]
                self.assertEqual(row["event_id"], "abc123")
                self.assertEqual(title["role"], "EVENT_TITLE")
                self.assertEqual(title["decision"], "REVIEW")
                self.assertEqual(title["source_url"], row["detail_source_url"])
                self.assertEqual(title["event_id"], "abc123")
                self.assertRegex(title["source_body_sha256"], r"^[0-9a-f]{64}$")
                self.assertEqual(title["observed_at"], "2026-11-23T10:00:00+08:00")
                self.assertEqual(title["hold_reason"],
                                 "SOURCE_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE")
                for field in ("date", "show_start", "price", "venue", "image"):
                    self.assertIsNone(row["fields"][field]["value"])
                    self.assertEqual(row["fields"][field]["decision"], "HOLD")
            self.assertEqual((result["new_official_get"], result["accepted_fields"],
                              result["published"]), (0, 0, 0))
            self.assertEqual(result["release_state"], "HARD_HOLD_NO_PUBLICATION")
            self.assertFalse((root / "docs" / "data.json").exists())

    def test_swapped_detail_and_missing_list_hold_own_provider(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture = self._fixture(root)
            source = fixture["sources"]
            source["accupass"]["details"]["abc123"]["detail_file"] = (
                source["kktix"]["details"]["abc123"]["detail_file"])
            result = replay_offline_sources(fixture, root)
            self.assertEqual(set(result["records"]), {"kktix:abc123"})
            self.assertEqual(result["holds"]["accupass:abc123"],
                             "SOURCE_RECEIPT_PROVENANCE_HOLD")
            self.assertEqual(result["records"]["kktix:abc123"]["fields"]["title"]["decision"],
                             "REVIEW")
            # LIST failure affects only its own source and never creates an
            # empty publication or silently inherits the other source's ID.
            source["accupass"]["list_file"] = "does_not_exist.html"
            result = replay_offline_sources(fixture, root)
            self.assertEqual(result["source_states"]["accupass"], "HOLD_LIST")
            self.assertEqual(set(result["records"]), {"kktix:abc123"})
            self.assertEqual(result["holds"]["accupass"], "SOURCE_FIXTURE_IO_HOLD")
            self.assertEqual(result["published"], 0)

    def test_title_conflict_tamper_empty_list_and_path_escape_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture = self._fixture(root)
            data = fixture["sources"]["kktix"]
            body = b"<article><h1>Unrelated event</h1></article>"
            (root / "kktix_detail.html").write_bytes(body)
            data["details"]["abc123"]["receipt"]["body_sha256"] = hashlib.sha256(body).hexdigest()
            result = replay_offline_sources(fixture, root)
            self.assertEqual(result["holds"]["kktix:abc123"],
                             "SOURCE_LIST_DETAIL_TITLE_PARITY_HOLD")
            self.assertEqual(set(result["records"]), {"accupass:abc123"})
            data["list_file"] = "../foreign-secret.html"
            result = replay_offline_sources(fixture, root)
            self.assertEqual(result["source_states"]["kktix"], "HOLD_LIST")
            self.assertEqual(result["holds"]["kktix"], "SOURCE_FIXTURE_PATH_HOLD")
            data["list_file"] = "kktix_list.html"
            raw = b"<html><body>No event links</body></html>"
            (root / "kktix_list.html").write_bytes(raw)
            data["list_receipt"]["body_sha256"] = hashlib.sha256(raw).hexdigest()
            result = replay_offline_sources(fixture, root)
            self.assertEqual(result["source_states"]["kktix"], "HOLD_EMPTY_LIST")
            self.assertEqual(result["published"], 0)
            bad = copy.deepcopy(fixture)
            bad["sources"]["accupass"]["details"]["different_id"] = (
                bad["sources"]["accupass"]["details"].pop("abc123"))
            with self.assertRaisesRegex(ValueError, "SOURCE_DETAIL_ID_NOT_IN_LIST_HOLD"):
                replay_offline_sources(bad, root)

    def test_actual_cli_read_only_and_repeatable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture = self._fixture(root)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            command = [sys.executable, "-m", "scripts.p30_offline_source_adapters",
                       "--manifest", str(manifest), "--fixture-root", str(root)]
            a = subprocess.check_output(command, text=True)
            b = subprocess.check_output(command, text=True)
            self.assertEqual(a, b)
            result = json.loads(a)
            self.assertEqual(result["counts"]["review_identities"], 2)
            self.assertEqual(result["published"], 0)
            self.assertEqual(set(path.name for path in root.iterdir()), {
                "manifest.json", "kktix_list.html", "kktix_detail.html",
                "accupass_list.html", "accupass_detail.html"})


    def test_shared_core_candidate_cas_restart_sibling_hold_and_rollback(self):
        from scripts.p30_offline_source_adapters import (
            commit_offline_candidate_lkg, load_offline_candidate_lkg,
            rollback_offline_candidate_lkg)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            initial = replay_offline_sources(manifest, root)
            first = commit_offline_candidate_lkg(initial, root)
            snap = load_offline_candidate_lkg(root, first["sha256"])
            self.assertEqual(set(snap["candidates"]), {"kktix:abc123", "accupass:abc123"})
            self.assertEqual(snap["candidates"]["kktix:abc123"]["fields"]["title"]["decision"],
                             "REVIEW_ONLY_NOT_ACCEPTED")
            self.assertEqual(snap["candidates"]["accupass:abc123"]["held_fields"]["price"]["decision"], "HOLD")
            self.assertFalse(snap["candidates"]["kktix:abc123"]["source_current"])
            manifest["sources"]["accupass"]["list_file"] = "missing.html"
            second_report = replay_offline_sources(manifest, root)
            second = commit_offline_candidate_lkg(second_report, root, first["sha256"])
            self.assertEqual(set(load_offline_candidate_lkg(root, second["sha256"])["candidates"]),
                             {"kktix:abc123", "accupass:abc123"})
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_CAS_HOLD"):
                commit_offline_candidate_lkg(second_report, root, "0" * 64)
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_ROLLBACK_CAS_HOLD"):
                rollback_offline_candidate_lkg(root, first["sha256"], "0" * 64)
            restored = rollback_offline_candidate_lkg(root, first["sha256"], second["sha256"])
            self.assertEqual(restored["sha256"], first["sha256"])
            self.assertEqual(load_offline_candidate_lkg(root, first["sha256"]), snap)
            self.assertFalse((root / "docs" / "data.json").exists())

    def test_shared_core_rejects_tampered_candidate_and_destructive_identity(self):
        from scripts.p30_offline_source_adapters import (
            commit_offline_candidate_lkg, load_offline_candidate_lkg)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            report = replay_offline_sources(manifest, root)
            first = commit_offline_candidate_lkg(report, root)
            forged = copy.deepcopy(report)
            forged["records"]["kktix:abc123"]["fields"]["price"]["value"] = 100
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_FIELD_AUTHORITY_HOLD"):
                commit_offline_candidate_lkg(forged, root, first["sha256"])
            forged = copy.deepcopy(report)
            forged["records"]["kktix:abc123"]["detail_source_url"] = (
                "https://www.accupass.com/event/abc123")
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_SOURCE_URL_HOLD"):
                commit_offline_candidate_lkg(forged, root, first["sha256"])
            forged = copy.deepcopy(report)
            forged["records"].pop("kktix:abc123")
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_DESTRUCTIVE_REMOVAL_HOLD"):
                commit_offline_candidate_lkg(forged, root, first["sha256"])
            path = root / "_isolated_multi_source_candidates" / "candidate_lkg.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_READ_CAS_HOLD"):
                load_offline_candidate_lkg(root, first["sha256"])

if __name__ == "__main__":
    unittest.main()

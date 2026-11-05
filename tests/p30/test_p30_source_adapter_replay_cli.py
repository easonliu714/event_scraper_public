"""Executable A/B replay integration: exact source SHA, timestamp, CAS and LKG."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts import p30_source_adapter_replay_cli as m
from scripts.p30_l7_field_golden_readiness import load_isolated_review_lkg


class TestABSourceReplayCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="eventradar_ab_replay_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = Path.cwd().resolve()
        self.output = self.root / "review_lkg_snapshot.json"
        self.stamp = datetime.now(timezone.utc).replace(microsecond=0)

    def write_manifest(self, line, *, tamper_sha=False, age_hours=0,
                       wrong_title=False, wrong_url=False):
        if line == "A":
            urls = (m.OPENTIX_ROTATION_LIST, m.OPENTIX_ROTATION_DETAIL)
            title = "C MUSICAL 音樂劇《小王子》"
            listing = '<main><a href="' + urls[1] + '">' + title + '</a></main>'
            detail = ('<main><h1>' + title + '</h1>'
                      '<p data-role="venue">臺北表演藝術中心 藍盒子</p></main>')
        else:
            urls = (m.SONGSHAN_PUBLIC_LIST,
                    m.SONGSHAN_PUBLIC_LIST + "/activity/" + m.SECOND_UUID)
            title = m.SECOND_TITLE
            listing = ('<main><div><a href="' + urls[1] + '">' + title +
                       '</a></div></main>')
            detail = '<main><h1>' + title + '</h1></main>'
        if wrong_title:
            detail = detail.replace(title, "其他活動")
        sources = []
        for i, (url, html) in enumerate(zip(urls, (listing, detail))):
            path = self.root / (line + str(i) + ".html")
            raw = html.encode("utf-8")
            path.write_bytes(raw)
            sources.append({
                "url": "https://example.org/other" if wrong_url and i == 1 else url,
                "path": str(path),
                "sha256": ("0" * 64 if tamper_sha and i == 1
                           else hashlib.sha256(raw).hexdigest()),
                "observed_at_utc": (self.stamp - timedelta(hours=age_hours)).isoformat()
            })
        manifest = self.root / (line + "_manifest.json")
        manifest.write_text(json.dumps({
            "kind": "P30_PREACQUIRED_OFFICIAL_HTML_V1",
            "transport": "CALLER_SUPPLIED_NOT_NATIVE_ATTESTED",
            "sources": sources
        }), encoding="utf-8")
        return manifest

    def test_a_opentix_same_id_to_sealed_lkg_and_no_native(self):
        manifest = self.write_manifest("A")
        out = m.replay("A", manifest, self.output, self.repo, now_utc=self.stamp)
        self.assertEqual(out["decision"], "REVIEW_ONLY_NONPUBLISHING", out)
        self.assertEqual(out["same_id_review_lkg"], 1)
        self.assertEqual(out["native_get_this_call"], 0)
        self.assertFalse(out["native_get_attested"])
        snap = load_isolated_review_lkg(self.output, self.repo)
        self.assertEqual(snap["rows"][0]["_candidate"]["record_id"],
                         "05:2072516129034670080")
        self.assertEqual(snap["rows"][0]["scraped_at"], self.stamp.isoformat())
        self.assertEqual(snap["formal_accepted_fields"], 0)
        self.assertEqual(snap["published_events"], 0)

    def test_b_songshan_second_uuid_same_id_sealed_review_only(self):
        manifest = self.write_manifest("B")
        out = m.replay("B", manifest, self.output, self.repo, now_utc=self.stamp)
        self.assertEqual(out["decision"], "REVIEW_ONLY_NONPUBLISHING", out)
        self.assertEqual(out["same_id_review_lkg"], 1)
        snap = load_isolated_review_lkg(self.output, self.repo)
        self.assertEqual(snap["rows"][0]["_candidate"]["record_id"],
                         "14:" + m.SECOND_UUID)
        self.assertEqual(snap["rows"][0]["scraped_at"], self.stamp.isoformat())
        self.assertEqual(snap["release_state"], "HARD_HOLD_NO_PUBLICATION")

    def test_tampered_sha_fails_before_any_snapshot_write(self):
        manifest = self.write_manifest("A", tamper_sha=True)
        out = m.replay("A", manifest, self.output, self.repo, now_utc=self.stamp)
        self.assertEqual(out["decision"], "HOLD")
        self.assertIn("SHA256_MISMATCH", out["first_failure"])
        self.assertFalse(self.output.exists())

    def test_stale_and_foreign_url_fail_closed(self):
        for kwargs in ({"age_hours": 25}, {"wrong_url": True}):
            with self.subTest(kwargs=kwargs):
                manifest = self.write_manifest("B", **kwargs)
                out = m.replay("B", manifest, self.output, self.repo,
                               now_utc=self.stamp)
                self.assertEqual(out["decision"], "HOLD", out)
                self.assertFalse(self.output.exists())

    def test_bad_detail_keeps_previous_snapshot_byte_identical(self):
        good = self.write_manifest("B")
        self.assertEqual(m.replay("B", good, self.output, self.repo,
                                  now_utc=self.stamp)["same_id_review_lkg"], 1)
        original = self.output.read_bytes()
        bad = self.write_manifest("B", wrong_title=True)
        out = m.replay("B", bad, self.output, self.repo, now_utc=self.stamp)
        self.assertEqual(out["decision"], "HOLD", out)
        self.assertEqual(self.output.read_bytes(), original)

    def test_cross_platform_lkg_cas_never_overwrites(self):
        self.assertEqual(m.replay("A", self.write_manifest("A"), self.output,
                                  self.repo, now_utc=self.stamp)["same_id_review_lkg"], 1)
        original = self.output.read_bytes()
        out = m.replay("B", self.write_manifest("B"), self.output,
                       self.repo, now_utc=self.stamp)
        self.assertEqual(out["decision"], "HOLD", out)
        self.assertEqual(self.output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()

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

    def test_accupass_partition_backlog_persists_across_cli_batches_and_restart(self):
        from scripts.p30_offline_source_adapters import (
            load_offline_candidate_lkg, rollback_offline_candidate_lkg,
            select_partition_pending, commit_offline_candidate_lkg)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = "https://www.accupass.com/"
            stamp = "2026-11-24T10:00:00+08:00"
            def receipt(raw, url):
                return {"evidence_class": "SEALED_OFFLINE_FIXTURE_ONLY",
                        "source_url": url, "observed_at": stamp,
                        "body_sha256": hashlib.sha256(raw).hexdigest()}
            ids = ["id%02d" % i for i in range(26)]
            raw = "".join('<a href="/event/%s"><h3>%s</h3></a>' %
                          (sid, sid) for sid in ids).encode()
            (root / "north.html").write_bytes(raw)
            entry = {"list_file": "north.html",
                     "list_receipt": receipt(raw, base + "?area=north"),
                     "details": {}}
            manifest = {"mode": "SEALED_OFFLINE_REPLAY_ONLY",
                        "sources": {"accupass": entry}}
            mf = root / "manifest.json"
            dest = root / "isolated"
            cmd = [sys.executable, "-m", "scripts.p30_offline_source_adapters",
                   "--manifest", str(mf), "--fixture-root", str(root),
                   "--candidate-root", str(dest)]
            def run(expected=None):
                mf.write_text(json.dumps(manifest), encoding="utf-8")
                extra = [] if expected is None else ["--expected-sha", expected]
                return json.loads(subprocess.check_output(cmd + extra, text=True))[
                    "candidate_commit"]
            def fill(batch):
                entry["details"] = {}
                for sid in batch:
                    body = ("<h1>" + sid + "</h1>").encode()
                    filename = sid + ".html"
                    (root / filename).write_bytes(body)
                    entry["details"][sid] = {"detail_file": filename,
                        "receipt": receipt(body, base + "event/" + sid)}
            first = run()
            self.assertEqual(first["pending_details"], 26)
            initial = load_offline_candidate_lkg(dest, first["sha256"])
            self.assertEqual(initial["candidates"], {})
            self.assertEqual(select_partition_pending(initial), ids[:20])
            fill(first["next_detail_ids"])
            second = run(first["sha256"])
            self.assertEqual(second["pending_details"], 6)
            self.assertEqual(second["next_detail_ids"], ids[20:])
            middle = load_offline_candidate_lkg(dest, second["sha256"])
            self.assertEqual(len(middle["candidates"]), 20)
            fill(second["next_detail_ids"])
            third = run(second["sha256"])
            self.assertEqual(third["pending_details"], 0)
            finished = load_offline_candidate_lkg(dest, third["sha256"])
            self.assertEqual(len(finished["candidates"]), 26)
            self.assertEqual(finished["partition_inventory"]["items"][ids[0]]["status"],
                             "DETAIL_REVIEW_ONLY")
            self.assertEqual(finished["candidates"]["accupass:" + ids[0]],
                             middle["candidates"]["accupass:" + ids[0]])
            # An identical archived LIST with no newly supplied detail is
            # idempotent. An explicitly failed DETAIL is not equivalent.
            entry["details"] = {}
            self.assertEqual(run(third["sha256"])["sha256"], third["sha256"])
            fill([ids[0]])
            entry["details"][ids[0]]["receipt"]["body_sha256"] = "0" * 64
            failed = run(third["sha256"])
            self.assertEqual(failed["next_detail_ids"], [ids[0]])
            # A different partition adds an ID without losing older pending work.
            other = b'<a href="/event/south"><h3>South</h3></a>'
            (root / "south.html").write_bytes(other)
            manifest["sources"]["accupass"] = {
                "list_file": "south.html",
                "list_receipt": receipt(other, base + "?area=south"), "details": {}}
            fifth = run(failed["sha256"])
            self.assertEqual(fifth["next_detail_ids"], [ids[0], "south"])
            saved = load_offline_candidate_lkg(dest, fifth["sha256"])
            self.assertEqual(len(saved["partition_inventory"]["items"]), 27)
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_CAS_HOLD"):
                commit_offline_candidate_lkg(replay_offline_sources(manifest, root),
                                             dest, third["sha256"])
            forged = copy.deepcopy(saved)
            forged["partition_inventory"]["detail_backlog"] = []
            with self.assertRaisesRegex(ValueError, "SOURCE_PARTITION_LEDGER_SCHEMA_HOLD"):
                select_partition_pending(forged)
            rollback_offline_candidate_lkg(dest, second["sha256"], fifth["sha256"])
            self.assertEqual(load_offline_candidate_lkg(dest, second["sha256"]), middle)
            self.assertFalse((dest / "docs" / "data.json").exists())

    def test_accupass_partition_union_backlog_and_non_destructive_cas(self):
        from scripts.p30_offline_source_adapters import (
            commit_offline_candidate_lkg, load_offline_candidate_lkg)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture = self._fixture(root)
            entry = fixture["sources"]["accupass"]
            template = entry["list_receipt"]
            base = "https://www.accupass.com/"
            def listing(name, url, raw):
                (root / name).write_bytes(raw)
                return {"list_file": name, "list_receipt": {
                    **template, "source_url": url,
                    "body_sha256": hashlib.sha256(raw).hexdigest()}}
            north = listing("north.html", base + "?area=north",
                            (root / entry["list_file"]).read_bytes())
            # The identical event appears in several regions/categories.
            # Only the second page carries this particular observed UTM edge.
            edge = base + "event/abc123?utm_source=web"
            title = "已封存同一活動 ID 測試 accupass"
            south = listing("south.html", base + "?area=south",
                            ('<a href="' + edge + '"><h3>' + title +
                             '</h3></a>' + ''.join(
                                 '<a href="/event/s%d"><h3>South %d</h3></a>' % (i, i)
                                 for i in range(25))).encode())
            broken = listing("center.html", base + "?area=center",
                             b'<a href="/event/center"><h3>Center</h3></a>')
            broken["list_receipt"]["body_sha256"] = "0" * 64
            detail = copy.deepcopy(entry["details"]["abc123"])
            detail["receipt"]["source_url"] = edge
            manifest = {"mode": fixture["mode"], "sources": {"accupass": {
                "lists": [north, south, broken], "details": {"abc123": detail}}}}
            report = replay_offline_sources(manifest, root)
            inv = report["partition_inventory"]["accupass"]
            self.assertEqual(report["source_states"]["accupass"], "REVIEW_PARTITION_ONLY")
            self.assertEqual(inv["coverage"], "PARTIAL_NOT_PROVIDER_COMPLETE")
            self.assertEqual(len(inv["event_ids"]), 26)
            self.assertEqual(len(inv["detail_backlog"]), 25)
            self.assertEqual(len(inv["pages"]), 2)
            self.assertEqual(inv["failed_pages"]["2"], "SOURCE_RECEIPT_PROVENANCE_HOLD")
            self.assertEqual(set(report["records"]), {"accupass:abc123"})
            evidence = report["records"]["accupass:abc123"]["source_evidence"]
            self.assertEqual(evidence["list_url"], base + "?area=south")
            self.assertEqual(evidence["list_body_sha256"], south["list_receipt"]["body_sha256"])
            self.assertEqual(evidence["list_link_urls"], [edge])
            first = commit_offline_candidate_lkg(report, root)
            baseline = load_offline_candidate_lkg(root, first["sha256"])

            # A later category-only observation must not erase an event
            # outside that category. A new ID is independently admitted.
            category = listing("learning.html", base + "?area=north&channel=1",
                               b'<a href="/event/new_id"><h3>New event</h3></a>')
            body = b'<h1>New event</h1>'
            (root / "new.html").write_bytes(body)
            new_detail = {"detail_file": "new.html", "receipt": {
                **template, "source_url": base + "event/new_id",
                "body_sha256": hashlib.sha256(body).hexdigest()}}
            partial = {"mode": fixture["mode"], "sources": {"accupass": {
                **category, "details": {"new_id": new_detail}}}}
            next_report = replay_offline_sources(partial, root)
            second = commit_offline_candidate_lkg(next_report, root, first["sha256"])
            stored = load_offline_candidate_lkg(root, second["sha256"])
            self.assertEqual(set(stored["candidates"]), {"accupass:abc123", "accupass:new_id"})
            self.assertEqual(stored["candidates"]["accupass:abc123"],
                             baseline["candidates"]["accupass:abc123"])

            # No arbitrary query or duplicate partition URL; conflicting
            # titles across pages cannot be silently overwritten.
            invalid = copy.deepcopy(manifest)
            invalid["sources"]["accupass"]["lists"] = [north, north]
            denied = replay_offline_sources(invalid, root)
            self.assertEqual(denied["holds"]["accupass"], "SOURCE_PARTITION_DUPLICATE_URL_HOLD")
            conflict = listing("conflict.html", base + "?area=north&channel=2",
                               b'<a href="/event/abc123"><h3>Different title</h3></a>')
            invalid["sources"]["accupass"]["lists"] = [north, conflict]
            denied = replay_offline_sources(invalid, root)
            self.assertEqual(denied["holds"]["accupass"], "SOURCE_LIST_DUPLICATE_IDENTITY_HOLD")
            invalid["sources"]["accupass"]["lists"] = [
                listing("unknown.html", base + "?area=north&page=2",
                        b'<a href="/event/abc123"><h3>Unknown query</h3></a>')]
            denied = replay_offline_sources(invalid, root)
            self.assertEqual(denied["partition_inventory"]["accupass"]["failed_pages"]["0"],
                             "SOURCE_RECEIPT_PROVENANCE_HOLD")
            self.assertEqual(denied["records"], {})
            self.assertEqual(load_offline_candidate_lkg(root, second["sha256"]), stored)
            self.assertFalse((root / "docs" / "data.json").exists())

    def test_independent_provider_cli_candidate_cas_without_synthetic_sibling(self):
        from scripts.p30_offline_source_adapters import (
            commit_offline_candidate_lkg, load_offline_candidate_lkg)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture = self._fixture(root)
            single = copy.deepcopy(fixture)
            del single["sources"]["kktix"]
            report = replay_offline_sources(single, root)
            self.assertEqual(report["source_states"]["kktix"], "NOT_ATTEMPTED")
            self.assertEqual(report["listed_identities"]["kktix"], [])
            self.assertNotIn("kktix", report["holds"])
            self.assertEqual(report["counts"]["sources"], 1)
            self.assertEqual(set(report["records"]), {"accupass:abc123"})
            for sources in ({}, {"unknown": single["sources"]["accupass"]}):
                with self.assertRaisesRegex(ValueError, "SOURCE_DUAL_ADAPTER_MANIFEST_HOLD"):
                    replay_offline_sources(dict(single, sources=sources), root)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(single), encoding="utf-8")
            dest = root / "isolated"
            cmd = [sys.executable, "-m", "scripts.p30_offline_source_adapters",
                   "--manifest", str(manifest), "--fixture-root", str(root),
                   "--candidate-root", str(dest)]
            created = json.loads(subprocess.check_output(cmd, text=True))
            first = created["candidate_commit"]["sha256"]
            stored = load_offline_candidate_lkg(dest, first)
            self.assertEqual(set(stored["candidates"]), {"accupass:abc123"})
            sibling = copy.deepcopy(fixture)
            del sibling["sources"]["accupass"]
            manifest.write_text(json.dumps(sibling), encoding="utf-8")
            advanced = json.loads(subprocess.check_output(
                cmd + ["--expected-sha", first], text=True))
            second = advanced["candidate_commit"]["sha256"]
            updated = load_offline_candidate_lkg(dest, second)
            self.assertEqual(set(updated["candidates"]), {"accupass:abc123", "kktix:abc123"})
            self.assertEqual(updated["candidates"]["accupass:abc123"],
                             stored["candidates"]["accupass:abc123"])
            stale = subprocess.run(cmd + ["--expected-sha", first], capture_output=True, text=True)
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("SOURCE_CANDIDATE_CAS_HOLD", stale.stderr)
            self.assertEqual(load_offline_candidate_lkg(dest, second), updated)
            forged = copy.deepcopy(report)
            forged["source_states"]["accupass"] = "NOT_ATTEMPTED"
            forged["listed_identities"]["accupass"] = []
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_IDENTITY_HOLD"):
                commit_offline_candidate_lkg(forged, dest, second)
            forged["source_states"]["accupass"] = "FORGED"
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_AUTHORITY_HOLD"):
                commit_offline_candidate_lkg(forged, dest, second)
            self.assertEqual(load_offline_candidate_lkg(dest, second), updated)
            self.assertEqual((advanced["new_official_get"], advanced["accepted_fields"],
                              advanced["published"]), (0, 0, 0))
            self.assertFalse((dest / "docs" / "data.json").exists())

    def test_accupass_observed_search_url_and_canonical_candidate_lineage(self):
        # Reuse the historical #236 exact UTM contract; fixture is NOT
        # official raw evidence. This tests the cross-branch integration.
        from scripts.p30_offline_source_adapters import (
            commit_offline_candidate_lkg, load_offline_candidate_lkg)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            entry = manifest["sources"]["accupass"]
            canonical = "https://www.accupass.com/event/abc123"
            query = "?utm_campaign=accu_e_&utm_medium=search_result_&utm_source=web"
            original = (root / entry["list_file"]).read_bytes()
            def seal(suffix, observed_url):
                body = original.replace(b'/event/abc123"', ("/event/abc123" + suffix + '"').encode())
                (root / entry["list_file"]).write_bytes(body)
                entry["list_receipt"]["body_sha256"] = hashlib.sha256(body).hexdigest()
                entry["list_receipt"]["source_url"] = "https://www.accupass.com/search"
                entry["details"]["abc123"]["receipt"]["source_url"] = observed_url
                return replay_offline_sources(manifest, root)
            report = seal(query, canonical + query)
            row = report["records"]["accupass:abc123"]
            self.assertEqual(row["detail_source_url"], canonical)
            self.assertEqual(row["source_evidence"]["detail_observed_url"], canonical + query)
            self.assertEqual(row["source_evidence"]["list_link_urls"], [canonical + query])
            self.assertEqual(row["source_evidence"]["list_url"], "https://www.accupass.com/search")
            self.assertEqual(row["source_evidence"]["list_body_sha256"],
                             entry["list_receipt"]["body_sha256"])
            saved = commit_offline_candidate_lkg(report, root)
            candidate = load_offline_candidate_lkg(root, saved["sha256"])["candidates"]["accupass:abc123"]
            self.assertEqual(candidate["source_evidence"], row["source_evidence"])
            self.assertEqual(candidate["detail_source_url"], canonical)
            self.assertEqual((report["new_official_get"], report["accepted_fields"],
                              report["published"]), (0, 0, 0))
            # A canonical request and a LIST-discovery URL are distinct.
            self.assertIn("accupass:abc123", seal(query, canonical)["records"])
            for suffix in ("?utm_source=other", "?utm_source=web&utm_source=web",
                           "?session=abc", "?utm_other=web", "#fragment"):
                rejected = seal(suffix, canonical + suffix)
                self.assertNotIn("accupass:abc123", rejected["records"])
                self.assertIn("kktix:abc123", rejected["records"])
            mismatched = seal(query, canonical + "?utm_source=web")
            self.assertEqual(mismatched["holds"]["accupass:abc123"],
                             "SOURCE_RECEIPT_PROVENANCE_HOLD")
            forged = copy.deepcopy(report)
            forged["records"]["accupass:abc123"]["source_evidence"]["detail_observed_url"] = (
                "https://www.accupass.com/event/other")
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_SOURCE_EVIDENCE_HOLD"):
                commit_offline_candidate_lkg(forged, root, saved["sha256"])

    def test_list_card_conflicting_title_assertions_hold_provider_only(self):
        # Source LIST identity is not trustworthy when the same anchor
        # advertises conflicting visible and attribute titles. Keep the
        # healthy sibling; never infer or publish a disputed event.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            baseline = replay_offline_sources(manifest, root)
            self.assertEqual(len(baseline["records"]), 2)
            for provider in ("kktix", "accupass"):
                entry = manifest["sources"][provider]
                original = (root / entry["list_file"]).read_bytes()
                title = ("已封存同一活動 ID 測試 " + provider)
                if provider == "kktix":
                    changed = original.replace(
                        ('title="' + title + '"').encode(),
                        b'title="CONFLICTING LIST TITLE"')
                else:
                    changed = original.replace(
                        b'<h3>', b'title="CONFLICTING LIST TITLE"><h3>', 1)
                    # Ensure the new title attribute is inside the anchor.
                    changed = changed.replace(
                        b'<a href="/event/abc123">title="CONFLICTING LIST TITLE">',
                        b'<a href="/event/abc123" title="CONFLICTING LIST TITLE">')
                self.assertNotEqual(changed, original)
                (root / entry["list_file"]).write_bytes(changed)
                entry["list_receipt"]["body_sha256"] = hashlib.sha256(changed).hexdigest()
                report = replay_offline_sources(manifest, root)
                self.assertEqual(report["source_states"][provider], "HOLD_LIST")
                self.assertEqual(report["holds"][provider],
                                 "SOURCE_LIST_CARD_TITLE_CONFLICT_HOLD")
                self.assertNotIn(provider + ":abc123", report["records"])
                other = "accupass" if provider == "kktix" else "kktix"
                self.assertIn(other + ":abc123", report["records"])
                self.assertEqual((report["new_official_get"], report["accepted_fields"],
                                  report["published"]), (0, 0, 0))
                (root / entry["list_file"]).write_bytes(original)
                entry["list_receipt"]["body_sha256"] = hashlib.sha256(original).hexdigest()
            self.assertEqual(len(replay_offline_sources(manifest, root)["records"]), 2)

    def test_jsonld_same_id_title_fallback_without_h1(self):
        # Archived JS-rendered DETAIL may have no H1. A unique same-ID Event
        # assertion can establish title identity, but never a mismatched,
        # duplicate, or cross-provider identity.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            entry = manifest["sources"]["kktix"]["details"]["abc123"]
            title = "已封存同一活動 ID 測試 kktix"
            event = {"@type": "Event", "url": "https://kktix.com/events/abc123",
                     "name": title, "startDate": "2026-12-01T19:30:00+08:00",
                     "location": {"@type": "Place", "name": "離線場館"}}
            def replay(objects):
                raw = ("<article><div id='app'></div><script type='application/ld+json'>" +
                       json.dumps({"@graph": objects}, ensure_ascii=False) +
                       "</script></article>").encode()
                (root / entry["detail_file"]).write_bytes(raw)
                entry["receipt"]["body_sha256"] = hashlib.sha256(raw).hexdigest()
                return replay_offline_sources(manifest, root)
            accepted = replay([event])
            self.assertEqual(accepted["records"]["kktix:abc123"]["fields"]["title"]["decision"], "REVIEW")
            self.assertEqual(accepted["records"]["kktix:abc123"]["fields"]["venue"]["value"], "離線場館")
            self.assertEqual(accepted["records"]["accupass:abc123"]["fields"]["title"]["decision"], "REVIEW")
            self.assertEqual((accepted["new_official_get"], accepted["accepted_fields"],
                              accepted["published"]), (0, 0, 0))
            for invalid in ([dict(event, name="錯誤標題")],
                            [dict(event, url="https://kktix.com/events/other")],
                            [event, dict(event)],
                            [dict(event, url="https://www.accupass.com/event/abc123")],
                            []):
                degraded = replay(invalid)
                self.assertNotIn("kktix:abc123", degraded["records"])
                self.assertIn("kktix:abc123", degraded["holds"])
                self.assertIn("accupass:abc123", degraded["records"])

    def test_structured_same_event_show_and_venue_review_and_candidate_restart(self):
        from scripts.p30_offline_source_adapters import (
            commit_offline_candidate_lkg, load_offline_candidate_lkg)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            entry = manifest["sources"]["kktix"]["details"]["abc123"]
            title = "已封存同一活動 ID 測試 kktix"
            event = {"@context": "https://schema.org", "@type": "Event",
                     "url": "https://kktix.com/events/abc123", "name": title,
                     "startDate": "2026-12-01T19:30:00+08:00",
                     "location": {"@type": "Place", "name": "測試展演廳"}}
            def seal(obj):
                raw = ("<article><h1>" + title + "</h1><script type='application/ld+json'>" +
                       json.dumps(obj, ensure_ascii=False) + "</script></article>").encode()
                (root / entry["detail_file"]).write_bytes(raw)
                entry["receipt"]["body_sha256"] = hashlib.sha256(raw).hexdigest()
            seal(event)
            report = replay_offline_sources(manifest, root)
            fields = report["records"]["kktix:abc123"]["fields"]
            self.assertEqual(fields["show_start"]["value"], event["startDate"])
            self.assertEqual(fields["venue"]["value"], "測試展演廳")
            self.assertEqual(fields["price"]["decision"], "HOLD")
            self.assertEqual(fields["show_start"]["decision"], "REVIEW")
            committed = commit_offline_candidate_lkg(report, root)
            saved = load_offline_candidate_lkg(root, committed["sha256"])
            self.assertEqual(saved["candidates"]["kktix:abc123"]["fields"]["venue"]["value"], "測試展演廳")
            self.assertEqual(saved["candidates"]["kktix:abc123"]["fields"]["show_start"]["decision"], "REVIEW_ONLY_NOT_ACCEPTED")
            self.assertEqual((report["new_official_get"], report["accepted_fields"], report["published"]), (0, 0, 0))
            for invalid in (
                dict(event, url="https://kktix.com/events/other"),
                dict(event, startDate="2026-12-01T19:30:00"),
                {key: value for key, value in event.items() if key != "startDate"},
                dict(event, startDate="not-a-date"),
                dict(event, name="Other event"),
            ):
                seal(invalid)
                degraded = replay_offline_sources(manifest, root)["records"]["kktix:abc123"]["fields"]
                self.assertEqual(degraded["show_start"]["decision"], "HOLD")
                self.assertEqual(degraded["venue"]["decision"], "HOLD")
            # A valid event start with no venue keeps only the independently
            # evidenced show time in REVIEW, never invents a venue.
            seal({key: value for key, value in event.items() if key != "location"})
            partial_fields = replay_offline_sources(manifest, root)["records"]["kktix:abc123"]["fields"]
            self.assertEqual(partial_fields["show_start"]["decision"], "REVIEW")
            self.assertEqual(partial_fields["venue"]["decision"], "HOLD")
            seal(event)
            raw = (root / entry["detail_file"]).read_text()
            raw = raw.replace("</article>", "<script type='application/ld+json'>" +
                              json.dumps(event, ensure_ascii=False) + "</script></article>")
            (root / entry["detail_file"]).write_text(raw)
            entry["receipt"]["body_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
            ambiguous = replay_offline_sources(manifest, root)["records"]["kktix:abc123"]["fields"]
            self.assertEqual(ambiguous["show_start"]["decision"], "HOLD")
            self.assertEqual(ambiguous["venue"]["decision"], "HOLD")

    def test_jsonld_graph_same_id_and_duplicate_fail_closed(self):
        # Realistic schema.org @graph is parsed without trusting unrelated
        # Event nodes or accepting duplicate same-ID event assertions.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            entry = manifest["sources"]["kktix"]["details"]["abc123"]
            title = "已封存同一活動 ID 測試 kktix"
            event = {"@type": ["Thing", "Event"],
                     "url": "https://kktix.com/events/abc123",
                     "name": title, "startDate": "2026-12-01T19:30:00+08:00",
                     "location": {"@type": "Place", "name": "圖譜展演廳"}}
            unrelated = dict(event, url="https://kktix.com/events/unrelated")
            def replay(graph):
                raw = ("<article><h1>" + title +
                       "</h1><script type='application/ld+json'>" +
                       json.dumps({"@context": "https://schema.org",
                                   "@graph": graph}, ensure_ascii=False) +
                       "</script></article>").encode()
                (root / entry["detail_file"]).write_bytes(raw)
                entry["receipt"]["body_sha256"] = hashlib.sha256(raw).hexdigest()
                return replay_offline_sources(manifest, root)
            report = replay([unrelated, event])
            fields = report["records"]["kktix:abc123"]["fields"]
            self.assertEqual(fields["show_start"]["decision"], "REVIEW")
            self.assertEqual(fields["venue"]["value"], "圖譜展演廳")
            self.assertEqual(report["accepted_fields"], 0)
            self.assertEqual(report["published"], 0)
            duplicate = replay([event, dict(event)])
            self.assertEqual(duplicate["records"]["kktix:abc123"]["fields"]["show_start"]["decision"], "HOLD")
            self.assertEqual(duplicate["records"]["kktix:abc123"]["fields"]["venue"]["decision"], "HOLD")
            wrong = replay([unrelated])
            self.assertEqual(wrong["records"]["kktix:abc123"]["fields"]["show_start"]["decision"], "HOLD")
            self.assertEqual(wrong["records"]["kktix:abc123"]["fields"]["venue"]["decision"], "HOLD")
            self.assertEqual(set(wrong["records"]), {"kktix:abc123", "accupass:abc123"})

    def test_jsonld_graph_local_place_reference_review_and_ambiguous_hold(self):
        # Real JSON-LD @graph Event.location often refers to a separate Place.
        # Only an unambiguous local graph reference may supply venue evidence.
        from scripts.p30_offline_source_adapters import (
            commit_offline_candidate_lkg, load_offline_candidate_lkg)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            entry = manifest["sources"]["kktix"]["details"]["abc123"]
            title = "已封存同一活動 ID 測試 kktix"
            event = {"@type": "Event", "url": "https://kktix.com/events/abc123",
                     "name": title, "startDate": "2026-12-01T19:30:00+08:00",
                     "location": {"@id": "#venue"}}
            place = {"@id": "#venue", "@type": "Place", "name": "獨立圖譜場館"}
            def replay(nodes):
                raw = ("<article><h1>" + title +
                       "</h1><script type='application/ld+json'>" +
                       json.dumps({"@context": "https://schema.org",
                                   "@graph": nodes}, ensure_ascii=False) +
                       "</script></article>").encode()
                (root / entry["detail_file"]).write_bytes(raw)
                entry["receipt"]["body_sha256"] = hashlib.sha256(raw).hexdigest()
                return replay_offline_sources(manifest, root)
            report = replay([event, place])
            fields = report["records"]["kktix:abc123"]["fields"]
            self.assertEqual(fields["venue"]["value"], "獨立圖譜場館")
            self.assertEqual(fields["show_start"]["decision"], "REVIEW")
            saved = commit_offline_candidate_lkg(report, root)
            snap = load_offline_candidate_lkg(root, saved["sha256"])
            self.assertEqual(snap["candidates"]["kktix:abc123"]["fields"]["venue"]["value"],
                             "獨立圖譜場館")
            self.assertEqual(snap["candidates"]["accupass:abc123"]["fields"]["title"]["decision"],
                             "REVIEW_ONLY_NOT_ACCEPTED")
            for nodes in ([event], [event, place, dict(place, name="偽造場館")],
                          [event, dict(place, **{"@id": "#other"})]):
                degraded = replay(nodes)["records"]["kktix:abc123"]["fields"]
                self.assertEqual(degraded["venue"]["decision"], "HOLD")
                self.assertEqual(degraded["show_start"]["decision"], "REVIEW")
            self.assertEqual((report["new_official_get"], report["accepted_fields"],
                              report["published"]), (0, 0, 0))

    def test_jsonld_place_reference_is_document_local(self):
        # A matching @id in a second script must not supply an Event venue.
        # A same-document Place with a multi-type schema remains supported.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            entry = manifest["sources"]["kktix"]["details"]["abc123"]
            title = "已封存同一活動 ID 測試 kktix"
            event = {"@type": "Event", "url": "https://kktix.com/events/abc123",
                     "name": title, "startDate": "2026-12-01T19:30:00+08:00",
                     "location": {"@id": "#venue"}}
            place = {"@id": "#venue", "@type": ["Thing", "Place"],
                     "name": "同文件場館"}
            def replay(documents):
                scripts = "".join("<script type='application/ld+json'>" +
                                  json.dumps(document, ensure_ascii=False) +
                                  "</script>" for document in documents)
                raw = ("<article><h1>" + title + "</h1>" + scripts +
                       "</article>").encode()
                (root / entry["detail_file"]).write_bytes(raw)
                entry["receipt"]["body_sha256"] = hashlib.sha256(raw).hexdigest()
                return replay_offline_sources(manifest, root)
            split = replay([{"@graph": [event]}, {"@graph": [place]}])
            self.assertEqual(split["records"]["kktix:abc123"]["fields"]["venue"]["decision"], "HOLD")
            self.assertEqual(split["records"]["kktix:abc123"]["fields"]["show_start"]["decision"], "REVIEW")
            self.assertEqual(split["records"]["accupass:abc123"]["fields"]["title"]["decision"], "REVIEW")
            joined = replay([{"@graph": [event, place]}])
            self.assertEqual(joined["records"]["kktix:abc123"]["fields"]["venue"]["value"], "同文件場館")
            self.assertEqual((joined["new_official_get"], joined["accepted_fields"],
                              joined["published"]), (0, 0, 0))
            # Inline multi-type Place must use the same admission predicate
            # as a same-document @id-resolved Place, not silently HOLD.
            inline = dict(event, location={"@type": ["Thing", "Place"],
                                           "name": "內嵌場館"})
            inline_report = replay([{"@graph": [inline]}])
            self.assertEqual(
                inline_report["records"]["kktix:abc123"]["fields"]["venue"]["value"],
                "內嵌場館")
            self.assertEqual(
                inline_report["records"]["kktix:abc123"]["fields"]["venue"]["decision"],
                "REVIEW")
            # Multiple Place declarations in one location must fail closed.
            ambiguous = dict(event, location={"@type": ["Place", "Place"],
                                              "name": "不可信場館"})
            ambiguous_report = replay([{"@graph": [ambiguous]}])
            self.assertEqual(
                ambiguous_report["records"]["kktix:abc123"]["fields"]["venue"]["decision"],
                "HOLD")
            # A duplicate same-document Place ID is ambiguous even with matching names.
            duplicate = replay([{"@graph": [event, place, dict(place)]}])
            self.assertEqual(duplicate["records"]["kktix:abc123"]["fields"]["venue"]["decision"], "HOLD")

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

    def test_listed_missing_detail_withdraws_old_review_but_keeps_identity_and_sibling(self):
        # The multi-source writer must not let one unavailable DETAIL block
        # updates to an otherwise verified LIST and a healthy second adapter.
        from scripts.p30_offline_source_adapters import (
            commit_offline_candidate_lkg, load_offline_candidate_lkg)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture = self._fixture(root)
            original_detail = copy.deepcopy(
                fixture["sources"]["accupass"]["details"]["abc123"])
            initial_report = replay_offline_sources(fixture, root)
            first = commit_offline_candidate_lkg(initial_report, root)
            baseline = load_offline_candidate_lkg(root, first["sha256"])
            self.assertEqual(
                initial_report["listed_identities"]["accupass"], ["accupass:abc123"])
            # Event remains LIST-identified but its DETAIL is now missing.
            fixture["sources"]["accupass"]["details"].pop("abc123")
            partial = replay_offline_sources(fixture, root)
            self.assertEqual(partial["holds"]["accupass:abc123"],
                             "SOURCE_DETAIL_NOT_PROVIDED_HOLD")
            self.assertNotIn("accupass:abc123", partial["records"])
            second = commit_offline_candidate_lkg(partial, root, first["sha256"])
            saved = load_offline_candidate_lkg(root, second["sha256"])
            self.assertEqual(set(saved["candidates"]),
                             {"accupass:abc123", "kktix:abc123"})
            self.assertEqual(saved["candidates"]["kktix:abc123"],
                             baseline["candidates"]["kktix:abc123"])
            held = saved["candidates"]["accupass:abc123"]
            self.assertEqual(held["fields"], {})
            self.assertFalse(held["source_current"])
            self.assertEqual(held["detail_replay_hold_reason"],
                             "SOURCE_DETAIL_NOT_PROVIDED_HOLD")
            self.assertEqual(held["held_fields"]["title"]["decision"], "HOLD")
            self.assertIsNone(held["held_fields"]["title"]["value"])
            self.assertEqual(held["held_fields"]["title"]["hold_reason"],
                             "SOURCE_DETAIL_NOT_PROVIDED_HOLD")
            self.assertEqual(
                held["held_fields"]["title"]["source_body_sha256"],
                baseline["candidates"]["accupass:abc123"]["fields"]["title"]
                        ["source_body_sha256"])
            # Forging an unsupported HOLD or pretending that an unlisted ID
            # remains present must not bypass the destructive-removal gate.
            wrong = copy.deepcopy(partial)
            wrong["listed_identities"]["accupass"] = []
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_DESTRUCTIVE_REMOVAL_HOLD"):
                commit_offline_candidate_lkg(wrong, root, second["sha256"])
            wrong = copy.deepcopy(partial)
            wrong["holds"]["accupass:abc123"] = "UNTRUSTED_FORCE_KEEP"
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_DESTRUCTIVE_REMOVAL_HOLD"):
                commit_offline_candidate_lkg(wrong, root, second["sha256"])
            self.assertEqual(load_offline_candidate_lkg(root, second["sha256"]), saved)
            # DETAIL recovers; its source-owned title returns as REVIEW only.
            fixture["sources"]["accupass"]["details"]["abc123"] = original_detail
            recovered = replay_offline_sources(fixture, root)
            third = commit_offline_candidate_lkg(recovered, root, second["sha256"])
            restored = load_offline_candidate_lkg(root, third["sha256"])
            self.assertEqual(restored, baseline)
            self.assertEqual(
                restored["candidates"]["accupass:abc123"]["fields"]["title"]
                        ["decision"], "REVIEW_ONLY_NOT_ACCEPTED")
            # LIST has a *different* event now: this is genuine unverified
            # removal, not a missing DETAIL for the original event.
            new_list = b'<a href="/event/new_id"><h3>Other event</h3></a>'
            (root / "accupass_list.html").write_bytes(new_list)
            fixture["sources"]["accupass"]["list_receipt"]["body_sha256"] = (
                hashlib.sha256(new_list).hexdigest())
            fixture["sources"]["accupass"]["details"] = {}
            removed = replay_offline_sources(fixture, root)
            self.assertEqual(removed["listed_identities"]["accupass"],
                             ["accupass:new_id"])
            with self.assertRaisesRegex(ValueError, "SOURCE_CANDIDATE_DESTRUCTIVE_REMOVAL_HOLD"):
                commit_offline_candidate_lkg(removed, root, third["sha256"])
            self.assertEqual(load_offline_candidate_lkg(root, third["sha256"]),
                             restored)
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

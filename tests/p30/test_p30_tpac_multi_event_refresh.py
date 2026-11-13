"""Deterministic two-ID positive/negative TPAC fixed multi-event refresh tests."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.p30_tpac_multi_event_refresh import (
    KIND, ROOT, discover_list, refresh_plan, refresh_event_plan, write_isolated_plan,
    restore_isolated_version,
)

NOW = datetime(2026, 11, 8, 14, 0, tzinfo=timezone.utc)
OBS = "2026-11-08T13:55:00Z"
TITLES = {"2040": "沉浸式劇場《士林YES！》",
          "2111": "測試官方展演活動 A",
          "2112": "測試官方展演活動 B"}
FIRST = {"2040": "2026-11-20 (五) 19:30",
         "2111": "2026-11-21 (六) 19:30",
         "2112": "2026-11-22 (日) 12:30"}


def receipt(url, body, observed=OBS, status=200, robots=True):
    return {"http_status": status, "final_url": url,
            "robots_allowed": robots, "observed_at": observed,
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "body_bytes": len(body)}


def listing(ids=("2111", "2112")):
    html = "<main>"
    for sid in ids:
        title = TITLES[sid]
        html += ('<a class="card-program" title="' + title
                 + '" href="/program/' + sid + '">'
                 + '<span class="card-program__text-title">' + title + '</span>'
                 + '<span class="card-program__text-date">2026-11-19 - 2026-11-28</span>'
                 + '</a>')
    return (html + "</main>").encode()


def detail(sid, title=None, show=None):
    title = title or TITLES[sid]
    show = show or FIRST[sid]
    return ('<main><article class="page-program__article">'
            '<h1>' + title + '</h1>'
            '<div class="page-program__article-top">2026-11-20 - 2026-11-30</div>'
            '</article><div class="page-program__aside-place-showtimes">'
            '<h3>場次</h3><ul><li><p>' + show
            + '</p></li></ul></div></main>').encode()


def inputs(ids=("2111", "2112")):
    raw = listing(ids)
    rr = receipt(ROOT, raw)
    details = {}
    for sid in ids:
        d = detail(sid)
        details[sid] = {"body": d, "receipt": receipt(ROOT + "/" + sid, d)}
    return raw, rr, details


def empty_prior():
    return {"kind": KIND, "events": {}}


class MultiEventRefreshTests(unittest.TestCase):
    def test_two_distinct_event_ids_generate_repeatable_review_snapshot(self):
        body, rr, details = inputs()
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        self.assertEqual(plan["decision"], "REVIEW_SNAPSHOT_READY_NOT_FORMAL")
        self.assertEqual(plan["qualified"], 2)
        self.assertEqual(plan["source_cards"], 2)
        self.assertEqual((plan["added"], plan["changed"], plan["unchanged"]), (2, 0, 0))
        self.assertEqual(set(plan["events"]), {"tpac:2111", "tpac:2112"})
        self.assertTrue(plan["source_coverage_complete"])
        self.assertEqual(plan["published"], 0)
        self.assertEqual(plan["release_state"], "HARD_HOLD_NO_PUBLICATION")
        for ev in plan["events"].values():
            self.assertFalse(ev["published"])
            self.assertFalse(ev["golden_accepted"])
            self.assertFalse(ev["formal_field_pass"])
            self.assertEqual(ev["price"], "")
            self.assertEqual(ev["_candidate"]["field_roles"]["date"]["role"], "EVENT_SHOW_START")
            self.assertIn("PRICE_NOT_VERIFIED", ev["_candidate"]["hold_reasons"])
            self.assertIn("HALL_NOT_VERIFIED", ev["_candidate"]["hold_reasons"])
            self.assertIn("LIST_DETAIL_PERIOD_CONFLICT_HOLD", ev["_candidate"]["hold_reasons"])
        again = refresh_plan(body, rr, details, {"kind": KIND, "events": plan["events"]}, NOW)
        self.assertEqual(again["added"], 0)
        self.assertEqual(again["changed"], 0)
        self.assertEqual(again["unchanged"], 2)

    def test_general_admission_price_is_reusable_review_field_not_formal(self):
        body, rr, details = inputs()
        price_html = (
            '<div class="page-program__aside-ticket">'
            '<div class="page-program__aside-ticket-price">'
            '<span>票價</span><strong>3500-1500 元</strong></div>'
            '<a href="https://www.opentix.life/event/2065059039769808896">購票去</a>'
            '</div>'
        ).encode()
        raw = details["2111"]["body"].replace(b"</main>", price_html + b"</main>")
        details["2111"] = {"body": raw, "receipt": receipt(ROOT + "/2111", raw)}
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        self.assertEqual(plan["decision"], "REVIEW_SNAPSHOT_READY_NOT_FORMAL")
        self.assertEqual(plan["qualified"], 2)
        entry = plan["events"]["tpac:2111"]
        self.assertIn("PRICE_REQUIRES_INDEPENDENT_FIELD_ACCEPTANCE", entry["_candidate"]["hold_reasons"])
        self.assertEqual(entry["_candidate"]["price_review"]["min_price_ntd"], 1500)
        self.assertEqual(entry["_candidate"]["price_review"]["max_price_ntd"], 3500)
        self.assertEqual(entry["_candidate"]["field_roles"]["price"]["decision"],
                         "REVIEW_REQUIRES_INDEPENDENT_ACCEPTANCE")
        self.assertEqual(entry["price"], "")
        self.assertFalse(entry["formal_field_pass"])
        self.assertFalse(entry["published"])
        self.assertIn("PRICE_NOT_VERIFIED",
                      plan["events"]["tpac:2112"]["_candidate"]["hold_reasons"])

    def test_partial_detail_failure_retains_prior_and_stages_good_id(self):
        body, rr, details = inputs()
        details["2112"]["receipt"]["http_status"] = 403
        old = {"kind": KIND, "events": {"tpac:2040": {"preserved": True}}}
        plan = refresh_plan(body, rr, details, old, NOW)
        self.assertEqual(plan["decision"], "REVIEW_SNAPSHOT_READY_NOT_FORMAL")
        self.assertEqual(plan["qualified"], 1)
        self.assertFalse(plan["source_coverage_complete"])
        self.assertIn("2112", plan["rejected"])
        self.assertIn("tpac:2040", plan["events"])
        self.assertIn("tpac:2111", plan["events"])
        self.assertNotIn("tpac:2112", plan["events"])

    def test_full_detail_failure_and_missing_details_never_erase_lkg(self):
        body, rr, details = inputs()
        old = {"kind": KIND, "events": {"tpac:2040": {"kept": True}}}
        for v in details.values():
            v["receipt"]["http_status"] = 403
        plan = refresh_plan(body, rr, details, old, NOW)
        self.assertEqual(plan["decision"], "HOLD_NO_QUALIFIED_DETAILS_PRESERVE_LKG")
        self.assertEqual(plan["events"], old["events"])
        self.assertEqual(plan["new_count"], 1)
        plan = refresh_plan(body, rr, {}, old, NOW)
        self.assertEqual(plan["events"], old["events"])
        self.assertEqual(plan["published"], 0)

    def test_zero_or_denied_list_never_erases_lkg(self):
        old = {"kind": KIND, "events": {"tpac:2040": {"kept": True}}}
        for body, rr in [
            (listing(()), receipt(ROOT, listing(()))),
            (listing(), receipt(ROOT, listing(), status=403)),
            (listing(), receipt(ROOT, listing(), robots=False)),
        ]:
            result = refresh_plan(body, rr, {}, old, NOW)
            self.assertTrue(result["decision"].startswith("HOLD_LIST_"))
            self.assertEqual(result["events"], old["events"])

    def test_duplicate_source_identity_and_wrong_title_are_not_promoted(self):
        body, rr, details = inputs(("2111", "2111"))
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        self.assertIn("DUPLICATE_SOURCE_ID", plan["decision"])
        self.assertEqual(plan["qualified"], 0)
        body, rr, details = inputs()
        bad = detail("2112", title="另個活動")
        details["2112"] = {"body": bad, "receipt": receipt(ROOT + "/2112", bad)}
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        self.assertEqual(plan["qualified"], 1)
        self.assertIn("TPAC_EXACT_ID_TITLE_PARITY_HOLD", plan["rejected"]["2112"])

    def test_show_role_conflict_and_stale_receipt_hold(self):
        body, rr, details = inputs()
        bad = detail("2111", show="2026-11-21 開賣 19:30")
        details["2111"] = {"body": bad, "receipt": receipt(ROOT + "/2111", bad)}
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        self.assertEqual(plan["qualified"], 1)
        self.assertIn("TPAC_SHOW_LABEL_OR_ROLE_HOLD", plan["rejected"]["2111"])
        body, rr, details = inputs()
        details["2111"]["receipt"]["observed_at"] = "2026-11-04T13:00:00Z"
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        self.assertIn("TPAC_SOURCE_STALE_OR_FUTURE_HOLD", plan["rejected"]["2111"])

    def test_source_body_sha_mismatch_does_not_validate(self):
        body, rr, details = inputs()
        details["2112"]["body"] += b"\n<!--changed-->"
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        self.assertIn("TPAC_RECEIPT_STATUS_URL_ROBOTS_SHA_HOLD", plan["rejected"]["2112"])

    def test_hidden_cards_not_counted_as_valid_source(self):
        card = listing(("2111",))
        body = b"<main><template>" + card + b"</template></main>"
        old = {"kind": KIND, "events": {"tpac:2040": {"kept": True}}}
        plan = refresh_plan(body, receipt(ROOT, body), {}, old, NOW)
        self.assertRegex(plan["decision"], r"HOLD_LIST_TPAC_(EMPTY_OR_OVER_CAP_LIST|NO_VALID_FIRST_PARTY_CARD)_HOLD")
        self.assertEqual(plan["events"], old["events"])

    def test_atomic_lkg_cas_success_retry_and_concurrent_stale_rejected(self):
        body, rr, details = inputs()
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = write_isolated_plan(plan, root, expected_sha=None)
            self.assertEqual(report["rows"], 2)
            self.assertEqual(report["decision"], "ISOLATED_REVIEW_LKG_COMMITTED_NOT_FORMAL")
            target = root / "_isolated_review" / "tpac" / "tpac_multi_event_lkg.json"
            original = target.read_bytes()
            with self.assertRaisesRegex(ValueError, "CAS_HOLD"):
                write_isolated_plan(plan, root, expected_sha=None)
            self.assertEqual(target.read_bytes(), original)
            again = write_isolated_plan(plan, root, expected_sha=report["sha256"])
            self.assertEqual(again["sha256"], report["sha256"])
            self.assertFalse((root / "docs" / "data.json").exists())


    def test_event_namespace_real_role_shape_and_two_cycle_cas(self):
        # Synthetic structure exercises the same code used for sealed native
        # archive replay; no HTTP and no formal field acceptance.
        from test_p30_tpac_event_detail_review import (
            detail as event_detail, receipt as event_receipt,
        )
        observed = datetime(2026, 11, 8, 14, 54, tzinfo=timezone.utc)
        names = {"1301": "「親．建築」計畫：高德亮《晚風》",
                 "2072": "2026北藝夜遊：Beats到天臺"}
        categories = {"1301": "展覽", "2072": "專題導覽"}
        periods = {"1301": "2025-07-23 - 2026-12-30",
                   "2072": "2026-11-10 - 2026-11-12"}
        raw = "".join(
            '<a class="card-event" title="連結到' + names[sid] +
            '" href="/event/' + sid + '"><div class="card-event__text-title">' +
            names[sid] + '</div><div class="card-event__text-datecate"><p>' +
            periods[sid] + '</p><p>' + categories[sid] + '</p></div></a>'
            for sid in names
        ).encode()
        details = {}
        for sid in names:
            data = event_detail(
                names[sid], categories[sid],
                "2025-07-24 - 2026-12-31" if sid == "1301"
                else "2026-11-11 - 2026-11-13",
                [] if sid == "1301" else [
                    "2026-11-11 (三) 19:00", "2026-11-12 (四) 19:00",
                    "2026-11-13 (五) 19:00"])
            details[sid] = {"body": data,
                            "receipt": event_receipt(
                                "https://tpac.org.taipei/event/" + sid, data)}
        listing_receipt = event_receipt("https://tpac.org.taipei/event", raw)
        plan = refresh_event_plan(raw, listing_receipt, details, empty_prior(), observed)
        self.assertEqual((plan["qualified"], plan["added"]), (2, 2))
        self.assertEqual(set(plan["events"]), {"tpac:event:1301", "tpac:event:2072"})
        self.assertEqual(plan["events"]["tpac:event:1301"]["date"], "")
        self.assertEqual(plan["events"]["tpac:event:2072"]["date"], "2026-11-11 19:00")
        self.assertIn("LIST_DETAIL_ACTIVITY_PERIOD_CONFLICT_HOLD",
                      plan["events"]["tpac:event:1301"]["_candidate"]["hold_reasons"])
        self.assertFalse(plan["events"]["tpac:event:2072"]["formal_field_pass"])
        with tempfile.TemporaryDirectory() as root:
            first = write_isolated_plan(plan, root, expected_sha=None)
            second_plan = refresh_event_plan(
                raw, listing_receipt, details,
                {"kind": KIND, "events": plan["events"]}, observed)
            self.assertEqual((second_plan["added"], second_plan["changed"],
                              second_plan["unchanged"]), (0, 0, 2))
            second = write_isolated_plan(second_plan, root, expected_sha=first["sha256"])
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertFalse((Path(root) / "docs" / "data.json").exists())
        details["2072"]["receipt"]["http_status"] = 403
        partial = refresh_event_plan(raw, listing_receipt, details,
                                     {"kind": KIND, "events": plan["events"]}, observed)
        self.assertEqual(partial["qualified"], 1)
        self.assertIn("2072", partial["rejected"])
        self.assertIn("tpac:event:2072", partial["events"])

    def test_event_and_program_numeric_ids_do_not_collide(self):
        from test_p30_tpac_event_detail_review import (
            detail as event_detail, receipt as event_receipt,
        )
        observed = datetime(2026, 11, 8, 14, 54, tzinfo=timezone.utc)
        name = "2026北藝夜遊：Beats到天臺"
        raw = ('<a class="card-event" title="連結到' + name +
               '" href="/event/2072"><div class="card-event__text-title">' +
               name + '</div><div class="card-event__text-datecate"><p>'
               '2026-11-10 - 2026-11-12</p><p>專題導覽</p></div></a>').encode()
        data = event_detail(name, "專題導覽", "2026-11-11 - 2026-11-13",
                            ["2026-11-11 (三) 19:00"])
        previous = {"kind": KIND, "events": {"tpac:2072": {"legacy_program": True}}}
        plan = refresh_event_plan(raw, event_receipt("https://tpac.org.taipei/event", raw),
                                  {"2072": {"body": data, "receipt": event_receipt(
                                      "https://tpac.org.taipei/event/2072", data)}},
                                  previous, observed)
        self.assertEqual(plan["qualified"], 1)
        self.assertIn("tpac:2072", plan["events"])
        self.assertIn("tpac:event:2072", plan["events"])


    def test_nonqualified_writes_and_foreign_symlink_rejected(self):
        body, rr, details = inputs()
        plan = refresh_plan(body, rr, {}, empty_prior(), NOW)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "UNQUALIFIED"):
                write_isolated_plan(plan, d)
            src = Path(d) / "_isolated_review"
            src.mkdir()
            (src / "tpac").symlink_to(Path(d), target_is_directory=True)
            valid = refresh_plan(body, rr, inputs()[2], empty_prior(), NOW)
            with self.assertRaisesRegex(ValueError, "SYMLINK"):
                write_isolated_plan(valid, d)


    def test_cli_event_manifest_dispatch_cas_and_cross_catalog_hold(self):
        # One repeatable CLI entrypoint must handle /event without treating
        # exhibition/guide rows as /program SHOW or altering formal JSON.
        from scripts.p30_tpac_multi_event_refresh import main as refresh_cli
        from test_p30_tpac_event_detail_review import (
            detail as event_detail, receipt as event_receipt,
        )
        from contextlib import redirect_stdout
        from io import StringIO
        observed = datetime(2026, 11, 8, 14, 54, tzinfo=timezone.utc)
        name = "2026北藝夜遊：Beats到天臺"
        raw = ('<a class="card-event" title="連結到' + name +
               '" href="/event/2072"><div class="card-event__text-title">' +
               name + '</div><div class="card-event__text-datecate"><p>'
               '2026-11-10 - 2026-11-12</p><p>專題導覽</p></div></a>').encode()
        detail_raw = event_detail(name, "專題導覽",
                                  "2026-11-11 - 2026-11-13",
                                  ["2026-11-11 (三) 19:00"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "list.html").write_bytes(raw)
            (root / "detail.html").write_bytes(detail_raw)
            manifest = {
                "catalog": "event", "list_file": str(root / "list.html"),
                "list_receipt": event_receipt("https://tpac.org.taipei/event", raw),
                "details": {"2072": {
                    "detail_file": str(root / "detail.html"),
                    "receipt": event_receipt(
                        "https://tpac.org.taipei/event/2072", detail_raw)}},
                "prior": empty_prior(), "now": observed.isoformat(),
            }
            source = root / "manifest.json"
            source.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            stage = root / "isolated"
            with self.assertRaisesRegex(ValueError, "CATALOG_MISMATCH_HOLD"):
                refresh_cli(["--catalog", "program", "--input", str(source),
                             "--repo-root", str(stage)])
            self.assertFalse(stage.exists())
            with redirect_stdout(StringIO()) as captured:
                rc = refresh_cli(["--catalog", "event", "--input", str(source),
                                  "--repo-root", str(stage)])
            self.assertEqual(rc, 0)
            result = json.loads(captured.getvalue())
            self.assertEqual(result["counts"]["qualified"], 1)
            self.assertEqual(result["published"], 0)
            target = stage / "_isolated_review" / "tpac" / "tpac_multi_event_lkg.json"
            saved = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(set(saved["events"]), {"tpac:event:2072"})
            self.assertFalse(saved["events"]["tpac:event:2072"]["published"])
            self.assertFalse((stage / "docs" / "data.json").exists())
            manifest["prior"] = saved
            source.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            with redirect_stdout(StringIO()) as captured:
                rc = refresh_cli(["--catalog", "event", "--input", str(source),
                                  "--repo-root", str(stage), "--expected-sha",
                                  result["result"]["sha256"]])
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(captured.getvalue())["counts"]["unchanged"], 1)


    def test_durable_version_diff_rollback_and_no_unverified_location(self):
        raw, rr, details = inputs()
        plan = refresh_plan(raw, rr, details, empty_prior(), NOW)
        self.assertEqual(plan["events"]["tpac:2111"]["location"], "")
        self.assertIn("LOCATION_NOT_EVENT_VERIFIED",
                      plan["events"]["tpac:2111"]["_candidate"]["hold_reasons"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = write_isolated_plan(plan, root)
            target = root / "_isolated_review/tpac/tpac_multi_event_lkg.json"
            original = target.read_bytes()
            changed = json.loads(original)["events"]
            changed["tpac:2111"]["description"] += " isolated version"
            second = write_isolated_plan(dict(plan, events=changed), root, first["sha256"])
            self.assertEqual(second["diff"]["changed"], ["tpac:2111"])
            self.assertEqual(second["diff"]["removed"], [])
            archive = root / "_isolated_review/tpac/versions" / (first["sha256"] + ".json")
            self.assertEqual(archive.read_bytes(), original)
            with self.assertRaisesRegex(ValueError, "CAS_HOLD"):
                restore_isolated_version(root, first["sha256"], first["sha256"])
            restored = restore_isolated_version(root, first["sha256"], second["sha256"])
            self.assertEqual(restored["sha256"], first["sha256"])
            self.assertEqual(target.read_bytes(), original)
            self.assertTrue((root / "_isolated_review/tpac/versions" /
                             (second["sha256"] + ".json")).exists())
            self.assertFalse((root / "docs/data.json").exists())

    def test_unapproved_expiry_and_tampered_rollback_fail_closed(self):
        raw, rr, details = inputs()
        plan = refresh_plan(raw, rr, details, empty_prior(), NOW)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = write_isolated_plan(plan, root)
            target = root / "_isolated_review/tpac/tpac_multi_event_lkg.json"
            original = target.read_bytes()
            partial = dict(plan, events={"tpac:2111": plan["events"]["tpac:2111"]})
            with self.assertRaisesRegex(ValueError, "UNAUTHORIZED_REMOVAL"):
                write_isolated_plan(partial, root, first["sha256"])
            self.assertEqual(target.read_bytes(), original)
            repeated = write_isolated_plan(plan, root, first["sha256"])
            archive = root / "_isolated_review/tpac/versions" / (first["sha256"] + ".json")
            archive.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "ROLLBACK_ARCHIVE_SHA_HOLD"):
                restore_isolated_version(root, first["sha256"], repeated["sha256"])
            self.assertEqual(target.read_bytes(), original)

    def test_boolean_rollback_bypass_and_forged_archive_cannot_remove_lkg(self):
        raw, rr, details = inputs()
        full = refresh_plan(raw, rr, details, empty_prior(), NOW)
        partial = dict(full, events={"tpac:2111": full["events"]["tpac:2111"]})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = write_isolated_plan(full, root)
            target = root / "_isolated_review/tpac/tpac_multi_event_lkg.json"
            before = target.read_bytes()
            with self.assertRaisesRegex(ValueError, "ROLLBACK_BOOLEAN_BYPASS_HOLD"):
                write_isolated_plan(partial, root, first["sha256"],
                                    allow_archived_rollback=True)
            with self.assertRaisesRegex(ValueError, "ROLLBACK_ARCHIVE_AUTHORITY_HOLD"):
                write_isolated_plan(partial, root, first["sha256"],
                                    rollback_archive_sha="a" * 64)
            self.assertEqual(target.read_bytes(), before)
            self.assertFalse((root / "docs/data.json").exists())

    def test_verified_archived_rollback_may_remove_only_to_exact_old_snapshot(self):
        raw, rr, details = inputs()
        old_plan = refresh_plan(raw, rr, {"2111": details["2111"]},
                                empty_prior(), NOW)
        full_plan = refresh_plan(raw, rr, details, empty_prior(), NOW)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = write_isolated_plan(old_plan, root)
            target = root / "_isolated_review/tpac/tpac_multi_event_lkg.json"
            archived_bytes = target.read_bytes()
            second = write_isolated_plan(full_plan, root, first["sha256"])
            self.assertEqual(second["diff"]["added"], ["tpac:2112"])
            restored = restore_isolated_version(root, first["sha256"], second["sha256"])
            self.assertEqual(restored["diff"]["removed"], ["tpac:2112"])
            self.assertEqual(target.read_bytes(), archived_bytes)
            self.assertEqual(restored["sha256"], first["sha256"])
            self.assertFalse((root / "docs/data.json").exists())

    def test_noncanonical_archive_cannot_write_then_fail(self):
        raw, rr, details = inputs()
        plan = refresh_plan(raw, rr, details, empty_prior(), NOW)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = write_isolated_plan(plan, root)
            target = root / "_isolated_review/tpac/tpac_multi_event_lkg.json"
            before = target.read_bytes()
            noncanonical = json.dumps(json.loads(before), ensure_ascii=False,
                                      indent=2).encode("utf-8")
            self.assertNotEqual(noncanonical, before)
            digest = hashlib.sha256(noncanonical).hexdigest()
            versions = target.parent / "versions"
            versions.mkdir(exist_ok=True)
            (versions / (digest + ".json")).write_bytes(noncanonical)
            with self.assertRaisesRegex(ValueError, "NONCANONICAL_ARCHIVE_HOLD"):
                restore_isolated_version(root, digest, first["sha256"])
            self.assertEqual(target.read_bytes(), before)


    def test_auto_prior_two_realizable_cycles_without_manifest_state(self):
        # A fixed caller can replay two separately supplied source snapshots
        # into the same isolated CAS LKG without manually injecting prior/SHA.
        # Fixture bytes are NOT independent native GET or formal acceptance.
        from scripts.p30_tpac_multi_event_refresh import main as refresh_cli
        from contextlib import redirect_stdout
        from io import StringIO
        raw, rr, details = inputs()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "list.html").write_bytes(raw)
            rows = {}
            for sid, item in details.items():
                file = root / (sid + ".html")
                file.write_bytes(item["body"])
                rows[sid] = {"detail_file": str(file), "receipt": item["receipt"]}
            manifest = {"catalog": "program", "list_file": str(root / "list.html"),
                        "list_receipt": rr, "details": rows, "now": NOW.isoformat()}
            path = root / "manifest.json"
            path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            stage = root / "stage"
            args = ["--catalog", "program", "--input", str(path),
                    "--repo-root", str(stage), "--prior-from-lkg"]
            with redirect_stdout(StringIO()) as out:
                self.assertEqual(refresh_cli(args), 0)
            first = json.loads(out.getvalue())
            self.assertEqual(first["counts"]["added"], 2)
            self.assertEqual(first["published"], 0)
            target = stage / "_isolated_review/tpac/tpac_multi_event_lkg.json"
            original = target.read_bytes()
            with redirect_stdout(StringIO()) as out:
                self.assertEqual(refresh_cli(args), 0)
            second = json.loads(out.getvalue())
            self.assertEqual(second["counts"]["unchanged"], 2)
            self.assertEqual(second["result"]["sha256"], first["result"]["sha256"])
            self.assertEqual(target.read_bytes(), original)
            self.assertFalse((stage / "docs/data.json").exists())
            self.assertFalse((stage / "docs/platform_status.json").exists())

            manifest["prior"] = empty_prior()
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "AUTO_PRIOR_AMBIGUOUS_HOLD"):
                refresh_cli(args)
            del manifest["prior"]
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "AUTO_PRIOR_AMBIGUOUS_HOLD"):
                refresh_cli(args + ["--expected-sha", first["result"]["sha256"]])
            self.assertEqual(target.read_bytes(), original)

    def test_auto_prior_tamper_noncanonical_and_symlink_hold(self):
        from scripts.p30_tpac_multi_event_refresh import load_isolated_prior
        raw, rr, details = inputs()
        plan = refresh_plan(raw, rr, details, empty_prior(), NOW)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = write_isolated_plan(plan, root)
            target = root / "_isolated_review/tpac/tpac_multi_event_lkg.json"
            original = target.read_bytes()
            prior, sha = load_isolated_prior(root)
            self.assertEqual(sha, first["sha256"])
            self.assertEqual(prior["kind"], KIND)
            target.write_bytes(json.dumps(prior, indent=2).encode())
            with self.assertRaisesRegex(ValueError, "AUTO_PRIOR_NONCANONICAL_HOLD"):
                load_isolated_prior(root)
            target.write_bytes(b"not json")
            with self.assertRaisesRegex(ValueError, "AUTO_PRIOR_JSON_HOLD"):
                load_isolated_prior(root)
            target.unlink()
            outside = root / "foreign.json"
            outside.write_bytes(original)
            target.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "AUTO_PRIOR_SYMLINK_HOLD"):
                load_isolated_prior(root)
            self.assertEqual(outside.read_bytes(), original)



class VenueRoleReviewTests(unittest.TestCase):
    """Fixture regressions are not first-party native field acceptance."""

    def test_event_owned_venue_and_start_area_stay_review_only(self):
        raw, list_receipt, details = inputs()
        sid = "2111"
        markup = ('<div class="page-program__aside-place">'
                  '<div class="page-program__aside-place-venue">'
                  '<h3>場地</h3><p>藍盒子</p>'
                  '<div>本演出將於一樓小戲台開演</div>'
                  '</div></div>')
        body = details[sid]["body"].replace(b"</main>", markup.encode("utf-8") + b"</main>")
        details[sid] = {"body": body, "receipt": receipt(ROOT + "/" + sid, body)}
        plan = refresh_plan(raw, list_receipt, details, empty_prior(), NOW)
        event = plan["events"]["tpac:" + sid]
        role = event["_candidate"]["field_roles"]["venue_space"]
        self.assertEqual(role["value"], "藍盒子")
        self.assertEqual(role["start_area_note"], "本演出將於一樓小戲台開演")
        self.assertEqual(role["role"], "EVENT_VENUE_SPACE")
        self.assertEqual(role["source_body_sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(event["location"], "")
        self.assertFalse(event["formal_field_pass"])
        self.assertFalse(event["published"])
        self.assertIn("VENUE_SPACE_REQUIRES_INDEPENDENT_FIELD_ACCEPTANCE",
                      event["_candidate"]["hold_reasons"])

    def test_venue_wrong_label_duplicate_and_hidden_are_field_holds(self):
        from bs4 import BeautifulSoup
        from scripts.p30_tpac_multi_event_refresh import _venue_role_review
        good = ('<div class="page-program__aside-place">'
                '<div class="page-program__aside-place-venue">'
                '<h3>場地</h3><p>藍盒子</p>'
                '<div>本演出將於一樓小戲台開演</div></div></div>')
        cases = [
            (good.replace("場地", "票價"), "TPAC_VENUE_LABEL_OR_ROLE_HOLD"),
            (good + good, "TPAC_VENUE_EXACT_EVENT_SCOPE_HOLD"),
            (good.replace('page-program__aside-place-venue"',
                          'page-program__aside-place-venue" hidden'),
             "TPAC_VENUE_EXACT_EVENT_SCOPE_HOLD"),
        ]
        for markup, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(ValueError, reason):
                    _venue_role_review(BeautifulSoup(markup, "html.parser"))



class PersistentInventoryContractTests(unittest.TestCase):
    """Offline contract: no HTTP, no publication, no mutation of REVIEW LKG."""

    def test_dual_catalog_fairness_cas_and_restart(self):
        import tempfile
        from pathlib import Path
        from scripts.p30_tpac_multi_event_refresh import (
            INVENTORY_KIND, select_pending_details, write_detail_inventory,
            load_detail_inventory,
        )
        rows = {}
        for kind in ("program", "event"):
            for sid in ("1301", "2072"):
                key = f"tpac:{kind}:{sid}"
                rows[key] = {
                    "source_namespace": kind, "source_event_id": sid,
                    "detail_url": f"https://tpac.org.taipei/{kind}/{sid}",
                    "list_url": f"https://tpac.org.taipei/{kind}",
                    "list_sha": "a" * 64, "last_observed": OBS,
                    "status": "PENDING_DETAIL_BUDGET", "attempts": 0,
                    "last_attempt": None, "reason": "DETAIL_BYTES_NOT_CAPTURED",
                }
        inventory = {"kind": INVENTORY_KIND, "items": rows}
        selected = select_pending_details(inventory)
        self.assertEqual(len(selected), 2)
        self.assertEqual([rows[key]["source_namespace"] for key in selected],
                         ["program", "event"])
        with tempfile.TemporaryDirectory() as root:
            first = write_detail_inventory(inventory, root)
            restored, sha = load_detail_inventory(root)
            self.assertEqual(sha, first["sha256"])
            self.assertEqual(restored, inventory)
            with self.assertRaisesRegex(ValueError, "CAS_HOLD"):
                write_detail_inventory(inventory, root, expected_sha=None)
            self.assertFalse((Path(root) / "docs" / "data.json").exists())


    def test_real_cli_offline_two_catalog_inventory_restart_and_cas(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            program = listing(("2111", "2112"))
            event = ('<a class="card-event" title="連結到2026北藝夜遊：Beats到天臺" '
                     'href="/event/2072"><div class="card-event__text-title">'
                     '2026北藝夜遊：Beats到天臺</div>'
                     '<div class="card-event__text-datecate">'
                     '<p>2026-11-10 - 2026-11-12</p><p>專題導覽</p>'
                     '</div></a>').encode()
            (root / "program.html").write_bytes(program)
            (root / "event.html").write_bytes(event)
            manifest = {"now": NOW.isoformat(), "catalogs": {
                "program": {"list_file": str(root / "program.html"),
                            "list_receipt": receipt(ROOT, program), "details": {}},
                "event": {"list_file": str(root / "event.html"),
                          "list_receipt": receipt("https://tpac.org.taipei/event", event),
                          "details": {}}}}
            # Seed actual REVIEW LKG; inventory CLI must never overwrite it.
            from scripts.p30_tpac_multi_event_refresh import write_isolated_plan
            source_raw, source_receipt, source_details = inputs()
            seeded = refresh_plan(source_raw, source_receipt, source_details, empty_prior(), NOW)
            write_isolated_plan(seeded, root)
            lkg_path = root / "_isolated_review/tpac/tpac_multi_event_lkg.json"
            lkg_before = lkg_path.read_bytes()
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            command = [sys.executable, "-m", "scripts.p30_tpac_multi_event_refresh",
                       "--inventory-input", str(root / "manifest.json"),
                       "--repo-root", str(root)]
            first = subprocess.run(command, capture_output=True, text=True, check=True)
            doc = json.loads(first.stdout)
            self.assertEqual(doc["counts"]["source_cards"], 3)
            self.assertEqual(doc["counts"]["pending_detail_budget"], 3)
            self.assertEqual(doc["counts"]["parse_hold"], 0)
            self.assertEqual(doc["published"], 0)
            self.assertEqual(len(doc["next_detail_ids"]), 2)
            second = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(second.stdout)["inventory"]["sha256"],
                             doc["inventory"]["sha256"])
            self.assertFalse((root / "docs/data.json").exists())
            self.assertEqual(lkg_path.read_bytes(), lkg_before)
            # Invalid DETAIL cannot pass solely because its identity exists in LKG.
            bad_detail = b"<html>invalid detail</html>"
            (root / "bad-detail.html").write_bytes(bad_detail)
            manifest["catalogs"]["program"]["details"] = {
                "2111": {"detail_file": str(root / "bad-detail.html"),
                         "receipt": receipt(ROOT + "/2111", bad_detail)}}
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            invalid = subprocess.run(command, capture_output=True, text=True, check=True)
            invalid_doc = json.loads(invalid.stdout)
            self.assertEqual(invalid_doc["counts"]["parse_hold"], 1)
            self.assertEqual(invalid_doc["diagnostics"]["tpac:program:2111"]["status"], "PARSE_HOLD")
            self.assertEqual(lkg_path.read_bytes(), lkg_before)
            manifest["catalogs"]["event"]["list_receipt"]["http_status"] = 403
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            failed = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("TPAC_RECEIPT_STATUS_URL_ROBOTS_SHA_HOLD", failed.stderr)
            from scripts.p30_tpac_multi_event_refresh import load_detail_inventory
            _, sha = load_detail_inventory(root)
            self.assertEqual(sha, doc["inventory"]["sha256"])

    def test_cross_namespace_url_conflict_fails_closed(self):
        from scripts.p30_tpac_multi_event_refresh import (
            INVENTORY_KIND, select_pending_details,
        )
        bad = {"kind": INVENTORY_KIND, "items": {
            "tpac:event:1301": {
                "source_namespace": "event", "source_event_id": "1301",
                "detail_url": "https://tpac.org.taipei/program/1301",
                "status": "PENDING_DETAIL_BUDGET",
            },
        }}
        with self.assertRaisesRegex(ValueError, "IDENTITY_HOLD"):
            select_pending_details(bad)

if __name__ == "__main__":
    unittest.main()

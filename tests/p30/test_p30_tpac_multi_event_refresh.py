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

    def test_corrupt_prior_event_semantics_isolated_without_batch_abort(self):
        # A damaged persisted REVIEW record cannot overwrite itself or
        # prevent an independent valid event from entering isolated LKG.
        body, rr, details = inputs()
        corrupt = {"source_event_id": "2111", "_candidate": {
            "field_roles": {"date": None}, "hold_reasons": []}}
        old = {"kind": KIND, "events": {"tpac:2111": corrupt}}
        plan = refresh_plan(body, rr, details, old, NOW)
        self.assertEqual(plan["decision"], "REVIEW_SNAPSHOT_READY_NOT_FORMAL")
        self.assertEqual(plan["events"]["tpac:2111"], corrupt)
        self.assertIn("TPAC_PRIOR_EVENT_SEMANTIC_HOLD", plan["rejected"]["2111"])
        self.assertEqual(plan["qualified"], 1)
        self.assertEqual(plan["added"], 1)
        self.assertEqual(plan["events"]["tpac:2112"]["source_event_id"], "2112")
        self.assertFalse(plan["source_coverage_complete"])
        self.assertEqual(plan["published"], 0)

        only_body, only_rr, only_details = inputs(("2111",))
        held = refresh_plan(only_body, only_rr, only_details, old, NOW)
        self.assertEqual(held["decision"], "HOLD_NO_QUALIFIED_DETAILS_PRESERVE_LKG")
        self.assertEqual(held["events"], old["events"])
        self.assertEqual(held["published"], 0)

    def test_out_of_range_showtime_hours_fail_closed(self):
        # The official-looking show label must HOLD before datetime parsing;
        # 24:00 through 29:59 are invalid, never a REVIEW candidate.
        body, rr, details = inputs(("2111",))
        for hour in (24, 25, 29):
            with self.subTest(hour=hour):
                raw = detail("2111", show=f"2026-11-21 (六) {hour:02d}:30")
                details["2111"] = {"body": raw, "receipt": receipt(ROOT + "/2111", raw)}
                plan = refresh_plan(body, rr, details, empty_prior(), NOW)
                self.assertEqual(plan["qualified"], 0)
                self.assertEqual(plan["rejected"]["2111"], "TPAC_SHOW_LABEL_OR_ROLE_HOLD")
                self.assertEqual(plan["published"], 0)
        valid = detail("2111", show="2026-11-21 (六) 23:30")
        details["2111"] = {"body": valid, "receipt": receipt(ROOT + "/2111", valid)}
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        self.assertEqual(plan["qualified"], 1)
        self.assertEqual(plan["published"], 0)

    def test_hidden_showtime_cannot_become_review_event(self):
        body, rr, details = inputs(("2111",))
        original = details["2111"]["body"]
        # The hidden node has a valid-looking earlier date. It must never
        # override the actual visible event schedule.
        injected = original.replace(
            b"<ul><li><p>",
            b'<ul><li hidden><p>2026-11-20 (\\xe4\\xba\\x94) 12:30</p></li><li><p>',
        )
        details["2111"] = {"body": injected, "receipt": receipt(ROOT + "/2111", injected)}
        plan = refresh_plan(body, rr, details, empty_prior(), NOW)
        self.assertEqual(plan["qualified"], 0)
        self.assertEqual(plan["decision"], "HOLD_NO_QUALIFIED_DETAILS_PRESERVE_LKG")
        self.assertEqual(plan["rejected"]["2111"], "TPAC_HIDDEN_SHOWTIME_EVIDENCE_HOLD")
        self.assertEqual(plan["published"], 0)


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



class ReviewRoleDeltaRegressionTests(unittest.TestCase):
    """REVIEW source role changes are meaningful even when formal fields are blank."""

    def test_venue_and_price_review_changes_are_not_discarded(self):
        from scripts.p30_tpac_multi_event_refresh import _semantic_event_payload
        import copy
        base = {"source_event_id": "2040", "title": "北藝演出", "url": ROOT + "/2040",
                "date": "2026-11-20 19:30", "location": "", "price": "",
                "_candidate": {"field_roles": {"venue_space": {
                    "role": "EVENT_VENUE_SPACE", "value": "藍盒子",
                    "source_body_sha256": "a" * 64, "observed_at": OBS,
                    "decision": "REVIEW_REQUIRES_INDEPENDENT_ACCEPTANCE"}}}}
        changed = copy.deepcopy(base)
        changed["_candidate"]["field_roles"]["venue_space"]["value"] = "球劇場"
        self.assertNotEqual(_semantic_event_payload(base), _semantic_event_payload(changed))
        receipt_only = copy.deepcopy(base)
        receipt_only["_candidate"]["field_roles"]["venue_space"]["observed_at"] = "2026-11-17T13:00:00Z"
        receipt_only["_candidate"]["field_roles"]["venue_space"]["source_body_sha256"] = "b" * 64
        self.assertEqual(_semantic_event_payload(base), _semantic_event_payload(receipt_only))
        price = copy.deepcopy(base)
        price["_candidate"]["field_roles"]["price"] = {
            "role": "EVENT_GENERAL_ADMISSION_PRICE_RANGE", "min_price_ntd": 1500,
            "max_price_ntd": 3500, "decision": "REVIEW_REQUIRES_INDEPENDENT_ACCEPTANCE"}
        self.assertNotEqual(_semantic_event_payload(base), _semantic_event_payload(price))
        self.assertEqual(base["price"], "")


    def test_malformed_persisted_review_role_fails_closed(self):
        # Persisted REVIEW evidence with a scalar role must not crash with
        # AttributeError or silently be classified as unchanged.
        from scripts.p30_tpac_multi_event_refresh import _semantic_event_payload
        base = {"source_event_id": "2040", "title": "北藝演出",
                "_candidate": {"field_roles": {"venue_space": "invalid"}}}
        with self.assertRaisesRegex(ValueError, "TPAC_SEMANTIC_FIELD_ROLE_SCHEMA_HOLD:venue_space"):
            _semantic_event_payload(base)
        base["_candidate"]["field_roles"] = {"price": None}
        with self.assertRaisesRegex(ValueError, "TPAC_SEMANTIC_FIELD_ROLE_SCHEMA_HOLD:price"):
            _semantic_event_payload(base)
        base["_candidate"]["field_roles"] = {"venue_space": {"role": "EVENT_VENUE_SPACE", "value": "藍盒子"}}
        self.assertIsInstance(_semantic_event_payload(base), tuple)

    def test_list_detail_conflict_resolution_and_reappearance_are_not_discarded(self):
        """A quality HOLD transition must update REVIEW even with same display date."""
        body, list_receipt, details = inputs(("2111",))
        first = refresh_plan(body, list_receipt, details, empty_prior(), NOW)
        self.assertEqual(first["qualified"], 1)
        previous = first["events"]["tpac:2111"]
        self.assertIn("LIST_DETAIL_PERIOD_CONFLICT_HOLD",
                      previous["_candidate"]["hold_reasons"])

        # Actual showtime/official DETAIL stays identical; only official LIST
        # period is brought into alignment with the same-event DETAIL.
        aligned_list = body.replace(
            b"2026-11-19 - 2026-11-28",
            b"2026-11-20 - 2026-11-30")
        self.assertNotEqual(aligned_list, body)
        aligned_receipt = receipt(ROOT, aligned_list)
        resolved = refresh_plan(
            aligned_list, aligned_receipt, details,
            {"kind": KIND, "events": first["events"]}, NOW)
        self.assertEqual((resolved["added"], resolved["changed"],
                          resolved["unchanged"]), (0, 1, 0))
        current = resolved["events"]["tpac:2111"]
        self.assertNotIn("LIST_DETAIL_PERIOD_CONFLICT_HOLD",
                         current["_candidate"]["hold_reasons"])
        self.assertEqual(current["date"], previous["date"])
        self.assertEqual(current["title"], previous["title"])
        self.assertEqual(current["price"], "")
        self.assertEqual(current["location"], "")
        self.assertFalse(current["published"])
        self.assertFalse(current["formal_field_pass"])
        self.assertFalse(current["golden_accepted"])
        self.assertEqual(resolved["release_state"], "HARD_HOLD_NO_PUBLICATION")

        replay = refresh_plan(
            aligned_list, aligned_receipt, details,
            {"kind": KIND, "events": resolved["events"]}, NOW)
        self.assertEqual((replay["changed"], replay["unchanged"]), (0, 1))
        self.assertEqual(replay["events"], resolved["events"])
        regression = refresh_plan(
            body, list_receipt, details,
            {"kind": KIND, "events": resolved["events"]}, NOW)
        self.assertEqual((regression["changed"], regression["unchanged"]), (1, 0))
        self.assertIn("LIST_DETAIL_PERIOD_CONFLICT_HOLD",
                      regression["events"]["tpac:2111"]["_candidate"]["hold_reasons"])
        self.assertEqual(regression["published"], 0)

    def test_hold_reason_order_and_receipt_only_change_do_not_create_deltas(self):
        from scripts.p30_tpac_multi_event_refresh import _semantic_event_payload
        import copy
        body, list_receipt, details = inputs(("2111",))
        event = refresh_plan(body, list_receipt, details, empty_prior(), NOW)[
            "events"]["tpac:2111"]
        shuffled = copy.deepcopy(event)
        shuffled["_candidate"]["hold_reasons"] = list(
            reversed(event["_candidate"]["hold_reasons"]))
        shuffled["_candidate"]["hold_reasons"].append(
            shuffled["_candidate"]["hold_reasons"][0])
        shuffled["_candidate"]["source_list_sha256"] = "f" * 64
        shuffled["_candidate"]["observed_at"] = "2026-11-17T15:00:00+00:00"
        self.assertEqual(_semantic_event_payload(event),
                         _semantic_event_payload(shuffled))
        tampered_hold = copy.deepcopy(event)
        tampered_hold["_candidate"]["hold_reasons"] = [None]
        with self.assertRaisesRegex(ValueError, "TPAC_SEMANTIC_HOLD_REASONS_SCHEMA_HOLD"):
            _semantic_event_payload(tampered_hold)


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


    def test_list_reappearance_restores_pending_detail_without_losing_history(self):
        # SOURCE backlog regression: disappearance must not permanently strand
        # an ID when the same official catalog lists it again. No GET or publish.
        from scripts.p30_tpac_multi_event_refresh import (
            build_detail_inventory, select_pending_details,
        )
        first_list = listing(("2111", "2112"))
        first = build_detail_inventory("program", first_list,
                                       receipt(ROOT, first_list), NOW)
        pending = first["items"]["tpac:program:2111"]
        pending["attempts"] = 2
        pending["last_attempt"] = OBS
        pending["reason"] = "PREVIOUS_DETAIL_TRANSIENT_HOLD"
        verified = first["items"]["tpac:program:2112"]
        verified["status"] = "REVIEW_DETAIL_PARSED"
        verified["reason"] = "REVIEW_FIELDS_NOT_FORMALLY_ACCEPTED"

        missing_list = listing(("2112",))
        missing = build_detail_inventory("program", missing_list,
                                         receipt(ROOT, missing_list), NOW, first)
        self.assertEqual(missing["items"]["tpac:program:2111"]["status"],
                         "NOT_IN_LATEST_LIST_REVIEW")
        self.assertNotIn("tpac:program:2111", select_pending_details(missing))

        returned = build_detail_inventory("program", first_list,
                                          receipt(ROOT, first_list), NOW, missing)
        recovered = returned["items"]["tpac:program:2111"]
        self.assertEqual(recovered["status"], "PENDING_DETAIL_BUDGET")
        self.assertEqual(recovered["reason"], "REAPPEARED_DETAIL_RECHECK_REQUIRED")
        self.assertEqual(recovered["attempts"], 2)
        self.assertEqual(recovered["last_attempt"], OBS)
        self.assertIn("tpac:program:2111", select_pending_details(returned))
        self.assertEqual(returned["items"]["tpac:program:2112"]["status"],
                         "REVIEW_DETAIL_PARSED")

    def test_per_event_list_semantic_change_requeues_only_affected_detail(self):
        # Existing REVIEW detail cannot remain current when its *own* LIST
        # title/period changes. An unrelated card or decoration is not drift.
        from scripts.p30_tpac_multi_event_refresh import (
            build_detail_inventory, select_pending_details,
        )
        first_raw = listing(("2111", "2112"))
        initial = build_detail_inventory("program", first_raw,
                                         receipt(ROOT, first_raw), NOW)
        for sid in ("2111", "2112"):
            row = initial["items"]["tpac:program:" + sid]
            row["status"] = "REVIEW_DETAIL_PARSED"
            row["reason"] = "REVIEW_FIELDS_NOT_FORMALLY_ACCEPTED"
            row["attempts"] = 3
            row["last_attempt"] = OBS
        old_first_sha = initial["items"]["tpac:program:2111"]["list_card_sha256"]
        old_other_sha = initial["items"]["tpac:program:2112"]["list_card_sha256"]

        changed = first_raw.replace(b"2026-11-19 - 2026-11-28",
                                    b"2026-11-20 - 2026-11-29", 1)
        updated = build_detail_inventory("program", changed,
                                         receipt(ROOT, changed), NOW, initial)
        moved = updated["items"]["tpac:program:2111"]
        other = updated["items"]["tpac:program:2112"]
        self.assertEqual(moved["status"], "PENDING_DETAIL_BUDGET")
        self.assertEqual(moved["reason"], "LIST_CARD_SEMANTIC_DRIFT_RECHECK_REQUIRED")
        self.assertNotEqual(moved["list_card_sha256"], old_first_sha)
        self.assertEqual((moved["attempts"], moved["last_attempt"]), (3, OBS))
        self.assertEqual(other["status"], "REVIEW_DETAIL_PARSED")
        self.assertEqual(other["list_card_sha256"], old_other_sha)
        self.assertEqual(select_pending_details(updated), ["tpac:program:2111"])
        # Idempotent after the new snapshot is committed; no repeated recapture.
        replay = build_detail_inventory("program", changed,
                                        receipt(ROOT, changed), NOW, updated)
        self.assertEqual(replay, updated)

        # Legacy inventories did not persist a per-card signature. Recheck
        # rather than silently treating an unproven REVIEW as current.
        legacy = {"kind": initial["kind"], "items": {
            key: dict(value) for key, value in initial["items"].items()}}
        legacy["items"]["tpac:program:2112"].pop("list_card_sha256")
        migrated = build_detail_inventory("program", first_raw,
                                           receipt(ROOT, first_raw), NOW, legacy)
        self.assertEqual(migrated["items"]["tpac:program:2112"]["status"],
                         "PENDING_DETAIL_BUDGET")
        self.assertEqual(migrated["items"]["tpac:program:2112"]["reason"],
                         "LIST_CARD_SEMANTIC_DRIFT_RECHECK_REQUIRED")

    def test_event_list_category_period_drift_requeues_without_get(self):
        from scripts.p30_tpac_multi_event_refresh import (
            build_detail_inventory, select_pending_details,
        )
        url = "https://tpac.org.taipei/event"
        raw = ('<a class="card-event" title="連結到官方專題導覽" href="/event/2072">'
               '<div class="card-event__text-title">官方專題導覽</div>'
               '<div class="card-event__text-datecate">'
               '<p>2026-11-10 - 2026-11-12</p><p>專題導覽</p>'
               '</div></a>').encode("utf-8")
        original = build_detail_inventory("event", raw, receipt(url, raw), NOW)
        original["items"]["tpac:event:2072"]["status"] = "REVIEW_DETAIL_PARSED"
        original["items"]["tpac:event:2072"]["reason"] = "REVIEW_FIELDS_NOT_FORMALLY_ACCEPTED"

        # A non-event navigation anchor changes LIST bytes but not owned data.
        decorated = raw + b'<a href="/about">About</a>'
        stable = build_detail_inventory("event", decorated,
                                        receipt(url, decorated), NOW, original)
        self.assertEqual(stable["items"]["tpac:event:2072"]["status"],
                         "REVIEW_DETAIL_PARSED")
        self.assertNotEqual(stable["items"]["tpac:event:2072"]["list_sha"],
                            original["items"]["tpac:event:2072"]["list_sha"])

        changed = decorated.replace("專題導覽</p>".encode("utf-8"),
                                    "藝術工作坊</p>".encode("utf-8"))
        newer = build_detail_inventory("event", changed,
                                       receipt(url, changed), NOW, stable)
        self.assertEqual(newer["items"]["tpac:event:2072"]["status"],
                         "PENDING_DETAIL_BUDGET")
        self.assertEqual(select_pending_details(newer), ["tpac:event:2072"])
        self.assertEqual(newer["items"]["tpac:event:2072"]["reason"],
                         "LIST_CARD_SEMANTIC_DRIFT_RECHECK_REQUIRED")

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
            # A legitimate offline PARSE_HOLD transition advances inventory CAS;
            # a subsequent denied LIST must preserve that latest committed version.
            self.assertNotEqual(invalid_doc["inventory"]["sha256"], doc["inventory"]["sha256"])
            self.assertEqual(invalid_doc["diagnostics"]["tpac:program:2111"]["status"], "PARSE_HOLD")
            self.assertEqual(lkg_path.read_bytes(), lkg_before)
            manifest["catalogs"]["event"]["list_receipt"]["http_status"] = 403
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            failed = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("TPAC_RECEIPT_STATUS_URL_ROBOTS_SHA_HOLD", failed.stderr)
            from scripts.p30_tpac_multi_event_refresh import load_detail_inventory
            _, sha = load_detail_inventory(root)
            self.assertEqual(sha, invalid_doc["inventory"]["sha256"])

    def test_offline_missing_detail_requeues_prior_review_without_mutating_lkg(self):
        # A persisted REVIEW row alone cannot prove that the current manifest
        # contains replayable DETAIL bytes. Requeue it without touching LKG.
        from scripts.p30_tpac_multi_event_refresh import (
            build_detail_inventory, write_detail_inventory,
            offline_inventory_cli, load_detail_inventory,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            program = listing(("2111",))
            event = ('<a class="card-event" title="連結到2026北藝夜遊：Beats到天臺" '
                     'href="/event/2072"><div class="card-event__text-title">'
                     '2026北藝夜遊：Beats到天臺</div>'
                     '<div class="card-event__text-datecate">'
                     '<p>2026-11-10 - 2026-11-12</p><p>專題導覽</p>'
                     '</div></a>').encode()
            (root / "program.html").write_bytes(program)
            (root / "event.html").write_bytes(event)
            first = build_detail_inventory("program", program,
                                           receipt(ROOT, program), NOW)
            row = first["items"]["tpac:program:2111"]
            row["status"] = "REVIEW_DETAIL_PARSED"
            row["reason"] = "REVIEW_FIELDS_NOT_FORMALLY_ACCEPTED"
            row["attempts"] = 3
            row["last_attempt"] = OBS
            write_detail_inventory(first, root)
            manifest = {"now": NOW.isoformat(), "catalogs": {
                "program": {"list_file": str(root / "program.html"),
                            "list_receipt": receipt(ROOT, program), "details": {}},
                "event": {"list_file": str(root / "event.html"),
                          "list_receipt": receipt("https://tpac.org.taipei/event", event),
                          "details": {}}}}
            path = root / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = offline_inventory_cli(path, root)
            updated, _ = load_detail_inventory(root)
            row = updated["items"]["tpac:program:2111"]
            self.assertEqual(row["status"], "PENDING_DETAIL_BUDGET")
            self.assertEqual(row["reason"], "DETAIL_BYTES_NOT_REPLAYED_HOLD")
            self.assertEqual(row["attempts"], 3)
            self.assertEqual(row["last_attempt"], OBS)
            self.assertEqual(result["counts"]["pending_detail_budget"], 2)
            self.assertIn("tpac:program:2111", result["next_detail_ids"])
            # Inventory CAS legitimately creates _isolated_review/tpac; only
            # the independent REVIEW LKG must remain absent.
            self.assertTrue((root / "_isolated_review" / "tpac" / "tpac_detail_inventory.json").is_file())
            self.assertFalse((root / "_isolated_review" / "tpac" / "tpac_multi_event_lkg.json").exists())
            self.assertFalse((root / "docs/data.json").exists())

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



class ArchivedDetailIdentityBindingTests(unittest.TestCase):
    """OFFLINE same-ID LIST→DETAIL contract; positive/negative and no GET."""

    def archived_receipt(self, url, raw):
        return {"evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                "source_url": url,
                "body_sha256": hashlib.sha256(raw).hexdigest(),
                "body_bytes": len(raw), "capture_started_at": OBS,
                "observed_at": None, "http_status": None, "robots_allowed": None}

    def sources(self, catalog, sid):
        title = "封存測試同一活動"
        attr = ("連結到" + title) if catalog == "event" else title
        cls = "card-" + catalog
        list_raw = (f'<a class="{cls}" href="/{catalog}/{sid}" title="{attr}">'
                    f'<div class="{cls}__text-title">{title}</div></a>').encode()
        detail_raw = (f'<article class="page-{catalog}__article">'
                      f'<h1>{title}</h1></article>').encode()
        root = "https://tpac.org.taipei/" + catalog
        return (list_raw, self.archived_receipt(root, list_raw),
                detail_raw, self.archived_receipt(root + "/" + sid, detail_raw))

    def test_both_catalog_namespaces_bind_real_html_title_without_publication(self):
        from scripts.p30_tpac_multi_event_refresh import bind_archived_detail_identity
        for catalog, sid in (("program", "2040"), ("event", "1301")):
            with self.subTest(catalog=catalog):
                args = self.sources(catalog, sid)
                result = bind_archived_detail_identity(
                    catalog, args[0], args[1], sid, args[2], args[3])
                self.assertEqual(result["identity"], f"tpac:{catalog}:{sid}")
                self.assertEqual(result["field_roles"]["title"]["role"], "EVENT_TITLE")
                self.assertEqual(result["detail_body_sha256"], hashlib.sha256(args[2]).hexdigest())
                self.assertEqual(result["decision"], "ARCHIVED_LIST_DETAIL_IDENTITY_REVIEW_ONLY")
                self.assertIsNone(result["observed_at"])
                self.assertEqual(result["accepted_fields"], 0)
                self.assertEqual(result["source_requests_performed"], 0)
                self.assertFalse(result["native_get_allowed"])
                self.assertFalse(result["published"])
                self.assertEqual(result["release_state"], "HARD_HOLD_NO_PUBLICATION")

    def test_detail_swaps_title_host_id_or_role_fail_without_acceptance(self):
        from scripts.p30_tpac_multi_event_refresh import bind_archived_detail_identity
        args = self.sources("event", "1301")
        with self.assertRaisesRegex(ValueError, "NOT_IN_SAME_LIST_HOLD"):
            bind_archived_detail_identity("event", args[0], args[1],
                                          "2072", args[2], args[3])
        with self.assertRaisesRegex(ValueError, "DETAIL_ID_SCOPE_HOLD"):
            bind_archived_detail_identity("other", args[0], args[1],
                                          "1301", args[2], args[3])
        swapped = args[2].replace("封存測試同一活動".encode(),
                                  "不同的活動標題".encode())
        with self.assertRaisesRegex(ValueError, "ARCHIVE_BYTES_SHA_HOLD"):
            bind_archived_detail_identity("event", args[0], args[1],
                                          "1301", swapped, args[3])
        new_receipt = self.archived_receipt("https://tpac.org.taipei/event/1301", swapped)
        with self.assertRaisesRegex(ValueError, "TITLE_PARITY_HOLD"):
            bind_archived_detail_identity("event", args[0], args[1],
                                          "1301", swapped, new_receipt)
        wrong_article = args[2].replace(b"page-event__article", b"page-program__article")
        wrong_receipt = self.archived_receipt(
            "https://tpac.org.taipei/event/1301", wrong_article)
        with self.assertRaisesRegex(ValueError, "OWNED_ARTICLE_HOLD"):
            bind_archived_detail_identity("event", args[0], args[1],
                                          "1301", wrong_article, wrong_receipt)
        copied_receipt = dict(args[3], source_url="https://tpac.org.taipei/event/2072")
        with self.assertRaisesRegex(ValueError, "ARCHIVE_IDENTITY_URL_HOLD"):
            bind_archived_detail_identity("event", args[0], args[1],
                                          "1301", args[2], copied_receipt)
        escalated = dict(args[3], http_status=200)
        with self.assertRaisesRegex(ValueError, "ARCHIVE_AUTHORITY_ESCALATION_HOLD"):
            bind_archived_detail_identity("event", args[0], args[1],
                                          "1301", args[2], escalated)




    def test_archive_date_roles_real_dom_value_not_only_source_string(self):
        from scripts.p30_tpac_multi_event_refresh import bind_archived_detail_identity
        scenarios = (
            ("program", "2040",
             '<div class="page-program__article-top">2026-11-20 - 2026-11-30</div>',
             '<div class="page-program__aside-place-showtimes"><h3>場次</h3>'
             '<ul><li><p>2026-11-21 (六) 19:30</p></li></ul></div>',
             "EVENT_SHOW_START"),
            ("event", "1301",
             '<div class="page-event__article-top-text"><div>展覽</div>'
             '<div>2026-11-20 - 2026-11-30</div></div>',
             '', "EXHIBITION_PERIOD"),
            ("event", "2072",
             '<div class="page-event__article-top-text"><div>導覽</div>'
             '<div>2026-11-20 - 2026-11-30</div></div>',
             '<div class="page-event__aside-place-showtimes"><h3>場次</h3>'
             '<ul><li><p>2026-11-21 (六) 19:30</p></li></ul></div>',
             "EVENT_SHOW_START"))
        for catalog, sid, period, showtimes, expected_role in scenarios:
            with self.subTest(catalog=catalog, sid=sid):
                list_raw, list_rec, _, _ = self.sources(catalog, sid)
                title = "封存測試同一活動"
                detail_raw = (
                    f'<main><article class="page-{catalog}__article">'
                    f'<h1>{title}</h1>{period}</article>{showtimes}</main>'
                ).encode()
                receipt = self.archived_receipt(
                    f"https://tpac.org.taipei/{catalog}/{sid}", detail_raw)
                row = bind_archived_detail_identity(
                    catalog, list_raw, list_rec, sid, detail_raw, receipt)
                roles = row["field_roles"]
                self.assertTrue(
                    any(r["role"] == expected_role for r in roles.values()), roles)
                self.assertEqual(row["accepted_fields"], 0)
                self.assertFalse(row["formal_field_pass"])
                self.assertFalse(row["published"])
                self.assertEqual(row["field_holds"]["date"]["decision"], "HOLD")
                self.assertEqual(row["field_holds"]["price"]["value"], None)
                self.assertEqual(row["field_holds"]["venue"]["value"], None)
                self.assertEqual(row["field_holds"]["date"]["hold_reason"],
                                 "ARCHIVED_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE")
                for candidate in roles.values():
                    self.assertEqual(candidate["source_url"], row["detail_url"])
                    self.assertEqual(candidate["source_body_sha256"],
                                     hashlib.sha256(detail_raw).hexdigest())
                    self.assertNotEqual(candidate["decision"], "FIELD_ACCEPTED")
                if expected_role == "EXHIBITION_PERIOD":
                    self.assertNotIn("show_start", roles)
                    self.assertEqual(roles["activity_period"]["value"],
                                     ["2026-11-20", "2026-11-30"])
                else:
                    self.assertEqual(roles["show_start"]["value"],
                                     "2026-11-21T19:30:00+08:00")

    def test_archived_malformed_show_or_period_never_promotes_date(self):
        from scripts.p30_tpac_multi_event_refresh import bind_archived_detail_identity
        list_raw, list_rec, _, _ = self.sources("program", "2040")
        for period, show, expected in (
            ("2026-11-30 - 2026-11-20", "2026-11-21 (六) 19:30", False),
            ("2026-11-20 - 2026-11-30", "2026-11-21 (日) 19:30", False),
            ("2026-11-20 - 2026-11-30", "2026-11-21 (六) 25:30", False),
            ("2026-11-20 - 2026-11-30", "2026-12-21 (一) 19:30", False)):
            with self.subTest(period=period, show=show):
                raw = (
                    '<main><article class="page-program__article">'
                    '<h1>封存測試同一活動</h1>'
                    f'<div class="page-program__article-top">{period}</div>'
                    '</article><div class="page-program__aside-place-showtimes">'
                    f'<h3>場次</h3><ul><li><p>{show}</p></li></ul></div></main>'
                ).encode()
                rec = self.archived_receipt(
                    "https://tpac.org.taipei/program/2040", raw)
                row = bind_archived_detail_identity(
                    "program", list_raw, list_rec, "2040", raw, rec)
                self.assertNotIn("show_start", row["field_roles"])
                self.assertEqual(row["field_holds"]["date"]["value"], None)
                self.assertEqual(row["field_holds"]["date"]["decision"], "HOLD")
                self.assertEqual(row["accepted_fields"], 0)
                self.assertEqual(row["field_roles"]["title"]["value"],
                                 "封存測試同一活動")

    def test_archived_identity_never_promotes_unverified_field_roles(self):
        # Historical identity parity is not a date/price/venue/description receipt.
        import inspect
        from scripts.p30_tpac_multi_event_refresh import bind_archived_detail_identity
        source = inspect.getsource(bind_archived_detail_identity)
        self.assertIn("ARCHIVED_FIELD_SEMANTICS_NOT_VERIFIED", source)
        self.assertIn('"field_holds"', source)
        self.assertIn('"source_body_sha256"', source)
        self.assertIn('"accepted_fields": 0', source)


class ArchivedProvenanceCliTests(unittest.TestCase):
    """Archive-only CLI is an evidence inventory, never a LIVE attestation."""

    # Reuse the source-byte fixtures for the real archived CLI→CAS regression.
    # Previously this class called self.sources() without owning that helper.
    archived_receipt = ArchivedDetailIdentityBindingTests.archived_receipt
    sources = ArchivedDetailIdentityBindingTests.sources

    def test_archived_real_event_link_prefix_preserves_source_owned_title(self):
        # Official /event title attrs begin with a navigation prefix, but the
        # event-owned visible title itself does not contain that prefix.
        from scripts.p30_tpac_multi_event_refresh import _archived_cards
        title = "北藝散步導覽"
        raw = (f'<a class="card-event" href="/event/1301" title="連結到{title}">'
               f'<div class="card-event__text-title">{title}</div></a>').encode()
        url = "https://tpac.org.taipei/event"
        receipt = {"evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                   "source_url": url, "body_sha256": hashlib.sha256(raw).hexdigest(),
                   "body_bytes": len(raw), "capture_started_at": None,
                   "observed_at": OBS, "http_status": None, "robots_allowed": None}
        cards = _archived_cards("event", raw, receipt)
        self.assertEqual(set(cards), {"1301"})
        self.assertEqual(cards["1301"]["identity"], "tpac:event:1301")
        modified = raw.replace(title.encode(), "另一場活動".encode(), 1)
        forged = dict(receipt, body_sha256=hashlib.sha256(modified).hexdigest(),
                      body_bytes=len(modified))
        with self.assertRaisesRegex(ValueError, "TPAC_CATALOG_TITLE_CONFLICT_HOLD"):
            _archived_cards("event", modified, forged)

    def test_archived_cli_subprocess_cas_restart_and_negative_authority(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bodies = {}
            catalogs = {}
            for catalog in ("program", "event"):
                sid = "2040" if catalog == "program" else "1301"
                title = "測試封存活動"
                cls = "card-program" if catalog == "program" else "card-event"
                text_cls = cls + "__text-title"
                raw = (f'<a class="{cls}" href="/{catalog}/{sid}" title="{title}">'
                       f'<div class="{text_cls}">{title}</div></a>').encode()
                path = root / (catalog + ".html")
                path.write_bytes(raw)
                url = "https://tpac.org.taipei/" + catalog
                receipt = {"evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                           "source_url": url, "body_sha256": hashlib.sha256(raw).hexdigest(),
                           "body_bytes": len(raw), "capture_started_at": OBS,
                           "observed_at": None, "http_status": None, "robots_allowed": None}
                bodies[catalog] = receipt
                catalogs[catalog] = {"list_file": str(path), "list_receipt": receipt, "details": {}}
            manifest = {"mode": "archived", "catalogs": catalogs}
            path = root / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            command = [sys.executable, "-m", "scripts.p30_tpac_multi_event_refresh",
                       "--inventory-input", str(path), "--repo-root", str(root)]
            first = subprocess.run(command, capture_output=True, text=True, check=True)
            output = json.loads(first.stdout)
            self.assertEqual(output["counts"]["source_cards"], 2)
            self.assertEqual(output["counts"]["pending_detail_budget"], 2)
            self.assertEqual(output["accepted_fields"], 0)
            self.assertEqual(output["published"], 0)
            second = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(second.stdout)["inventory"]["sha256"],
                             output["inventory"]["sha256"])
            self.assertFalse((root / "docs/data.json").exists())
            for field, value in (("observed_at", OBS), ("http_status", 200),
                                 ("robots_allowed", True)):
                manifest["catalogs"]["program"]["list_receipt"][field] = value
                path.write_text(json.dumps(manifest), encoding="utf-8")
                denied = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(denied.returncode, 0)
                self.assertIn("TPAC_ARCHIVE_AUTHORITY_ESCALATION_HOLD", denied.stderr)
                manifest["catalogs"]["program"]["list_receipt"][field] = None
            # An archived body without its original capture timestamp cannot
            # acquire provenance merely by passing the byte hash checks.
            program_receipt = manifest["catalogs"]["program"]["list_receipt"]
            original_stamp = program_receipt.pop("capture_started_at")
            path.write_text(json.dumps(manifest), encoding="utf-8")
            missing_stamp = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(missing_stamp.returncode, 0)
            self.assertIn("TPAC_ARCHIVE_CAPTURE_TIMESTAMP_MISSING_HOLD", missing_stamp.stderr)
            program_receipt["capture_started_at"] = original_stamp
            manifest["catalogs"]["program"]["list_receipt"]["body_sha256"] = "0" * 64
            path.write_text(json.dumps(manifest), encoding="utf-8")
            denied = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn("TPAC_ARCHIVE_BYTES_SHA_HOLD", denied.stderr)


    def test_archived_cli_requires_list_detail_article_title_parity(self):
        # Same URL and caller-consistent digest must not inflate archive coverage
        # when the source-owned article H1 disagrees with the sealed LIST card.
        from scripts.p30_tpac_multi_event_refresh import archived_inventory_cli
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalogs = {}
            for catalog, sid in (("program", "2040"), ("event", "1301")):
                title = "封存活動"
                cls = "card-program" if catalog == "program" else "card-event"
                raw = (f'<a class="{cls}" href="/{catalog}/{sid}" title="{title}">'
                       f'<span class="{cls}__text-title">{title}</span></a>').encode()
                path = root / (catalog + "_list.html")
                path.write_bytes(raw)
                url = "https://tpac.org.taipei/" + catalog
                receipt = {"evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                           "source_url": url, "body_sha256": hashlib.sha256(raw).hexdigest(),
                           "body_bytes": len(raw), "capture_started_at": OBS,
                           "observed_at": None, "http_status": None, "robots_allowed": None}
                catalogs[catalog] = {"list_file": str(path), "list_receipt": receipt,
                                     "details": {}}
            manifest = root / "manifest.json"
            def save():
                manifest.write_text(json.dumps({"mode": "archived", "catalogs": catalogs}),
                                    encoding="utf-8")
            save()
            self.assertEqual(archived_inventory_cli(manifest, root)["counts"]["detail_available"], 0)
            for title, expected in (("不同文章", "TPAC_ARCHIVE_LIST_DETAIL_TITLE_PARITY_HOLD"),
                                    ("封存活動", None)):
                raw = (f'<article class="page-program__article"><h1>{title}</h1>'
                       '</article>').encode()
                detail_path = root / "program_detail.html"
                detail_path.write_bytes(raw)
                catalogs["program"]["details"]["2040"] = {
                    "detail_file": str(detail_path),
                    "receipt": {"evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                                "source_url": "https://tpac.org.taipei/program/2040",
                                "body_sha256": hashlib.sha256(raw).hexdigest(),
                                "body_bytes": len(raw), "capture_started_at": OBS,
                                "observed_at": None, "http_status": None,
                                "robots_allowed": None}}
                save()
                if expected:
                    with self.assertRaisesRegex(ValueError, expected):
                        archived_inventory_cli(manifest, root)
                else:
                    result = archived_inventory_cli(manifest, root)
                    self.assertEqual(result["counts"]["detail_available"], 1)
                    self.assertEqual(result["accepted_fields"], 0)
                    self.assertEqual(result["published"], 0)

    def test_archived_field_evidence_survives_cas_restart_and_missing_replay(self):
        # The real source-owned archive binding must flow into persisted CAS,
        # not just return from an isolated parser helper.
        from scripts.p30_tpac_multi_event_refresh import (
            archived_inventory_cli, load_detail_inventory,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalogs = {}
            for catalog, sid in (("program", "2040"), ("event", "1301")):
                raw, rr, detail_raw, dr = self.sources(catalog, sid)
                list_file = root / (catalog + "_list.html")
                detail_file = root / (catalog + "_detail.html")
                list_file.write_bytes(raw)
                detail_file.write_bytes(detail_raw)
                catalogs[catalog] = {
                    "list_file": str(list_file), "list_receipt": rr,
                    "details": {sid: {"detail_file": str(detail_file), "receipt": dr}},
                }
            manifest = root / "archive_manifest.json"
            def save():
                manifest.write_text(json.dumps({"mode": "archived", "catalogs": catalogs}),
                                    encoding="utf-8")
            save()
            first = archived_inventory_cli(manifest, root)
            inventory, sha = load_detail_inventory(root / "_isolated_archive_replay")
            self.assertEqual(first["inventory"]["sha256"], sha)
            self.assertEqual(first["counts"]["detail_available"], 2)
            for catalog, sid in (("program", "2040"), ("event", "1301")):
                evidence = inventory["items"][f"tpac:{catalog}:{sid}"]["archive_field_evidence"]
                self.assertEqual(evidence["field_roles"]["title"]["role"], "EVENT_TITLE")
                self.assertEqual(evidence["accepted_fields"], 0)
                self.assertFalse(evidence["published"])
                self.assertEqual(evidence["detail_body_sha256"],
                                 catalogs[catalog]["details"][sid]["receipt"]["body_sha256"])
            self.assertEqual(archived_inventory_cli(manifest, root)["inventory"]["sha256"], sha)
            # Missing DETAIL on restart never erases last body-bound review evidence.
            catalogs["event"]["details"] = {}
            save()
            archived_inventory_cli(manifest, root)
            retained, _ = load_detail_inventory(root / "_isolated_archive_replay")
            row = retained["items"]["tpac:event:1301"]
            self.assertEqual(row["status"], "PENDING_DETAIL_BUDGET")
            self.assertEqual(row["archive_field_evidence"]["detail_body_sha256"],
                             inventory["items"]["tpac:event:1301"]["archive_field_evidence"]["detail_body_sha256"])
            self.assertEqual(row["archive_field_evidence"]["accepted_fields"], 0)
            # Corrupt original bytes fail before CAS commit.
            catalogs["event"]["details"] = {
                "1301": {"detail_file": catalogs["event"]["list_file"],
                         "receipt": catalogs["program"]["details"]["2040"]["receipt"]}}
            save()
            before = load_detail_inventory(root / "_isolated_archive_replay")[1]
            with self.assertRaises(ValueError):
                archived_inventory_cli(manifest, root)
            self.assertEqual(load_detail_inventory(root / "_isolated_archive_replay")[1], before)


    def test_persisted_archive_field_receipt_tamper_is_rejected_before_cas(self):
        # JSON canonical form and its CAS hash alone do not establish that
        # archived FIELD REVIEW has never been promoted to LIVE/accepted.
        from copy import deepcopy
        from scripts.p30_tpac_multi_event_refresh import (
            _canonical, archived_inventory_cli, load_detail_inventory,
            write_detail_inventory,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_root = root / "_isolated_archive_replay"
            catalogs = {}
            for catalog, sid in (("program", "2040"), ("event", "1301")):
                list_raw, list_rec, detail_raw, detail_rec = self.sources(catalog, sid)
                list_file = root / (catalog + "_list.html")
                detail_file = root / (catalog + "_detail.html")
                list_file.write_bytes(list_raw)
                detail_file.write_bytes(detail_raw)
                catalogs[catalog] = {
                    "list_file": str(list_file), "list_receipt": list_rec,
                    "details": {sid: {"detail_file": str(detail_file),
                                       "receipt": detail_rec}},
                }
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(
                {"mode": "archived", "catalogs": catalogs}), encoding="utf-8")
            initial = archived_inventory_cli(manifest, root)
            stored, sha = load_detail_inventory(archive_root)
            self.assertEqual(sha, initial["inventory"]["sha256"])
            target = archive_root / "_isolated_review/tpac/tpac_detail_inventory.json"
            original = target.read_bytes()
            row_key = "tpac:program:2040"

            def mutate(doc, name):
                row = doc["items"][row_key]
                evidence = row.get("archive_field_evidence", {})
                if name == "accepted":
                    evidence["accepted_fields"] = 1
                elif name == "published":
                    evidence["published"] = True
                elif name == "wrong_url":
                    evidence["field_roles"]["title"]["source_url"] = (
                        "https://tpac.org.taipei/program/777")
                elif name == "accepted_role":
                    evidence["field_roles"]["title"]["decision"] = "FIELD_ACCEPTED"
                elif name == "price_value":
                    evidence["field_holds"]["price"]["value"] = "NT$500"
                elif name == "title_empty":
                    evidence["field_roles"]["title"]["value"] = ""
                elif name == "body_sha":
                    evidence["detail_body_sha256"] = "0" * 64
                elif name == "stale_claim_current":
                    row["status"] = "PENDING_DETAIL_BUDGET"
                elif name == "bad_flag":
                    row["archive_field_evidence_current"] = "true"
                elif name == "orphan_flag":
                    row.pop("archive_field_evidence")
                elif name == "bad_timestamp":
                    evidence["capture_started_at"] = "not-a-date"
                else:
                    raise AssertionError(name)

            for bad in ("accepted", "published", "wrong_url", "accepted_role",
                        "price_value", "title_empty", "body_sha",
                        "stale_claim_current", "bad_flag", "orphan_flag",
                        "bad_timestamp"):
                with self.subTest(tamper=bad):
                    forged = deepcopy(stored)
                    mutate(forged, bad)
                    forged_bytes = _canonical(forged)
                    target.write_bytes(forged_bytes)
                    # Reading this perfectly canonical JSON must FAIL.
                    with self.assertRaisesRegex(ValueError, "TPAC_ARCHIVE_FIELD_"):
                        load_detail_inventory(archive_root)
                    # Replaying fresh manifest must not overwrite the tampered
                    # LKG silently; the operator must reconcile the corruption.
                    with self.assertRaisesRegex(ValueError, "TPAC_ARCHIVE_FIELD_"):
                        archived_inventory_cli(manifest, root)
                    self.assertEqual(target.read_bytes(), forged_bytes)
                    target.write_bytes(original)
            self.assertEqual(load_detail_inventory(archive_root)[1], sha)
            # The normal, unchanged re-run is idempotent.
            self.assertEqual(archived_inventory_cli(
                manifest, root)["inventory"]["sha256"], sha)
            self.assertFalse((root / "docs/data.json").exists())


    def test_archived_cli_cannot_downgrade_existing_live_inventory(self):
        import subprocess
        import sys
        from scripts.p30_tpac_multi_event_refresh import (
            INVENTORY_KIND, write_detail_inventory, load_detail_inventory,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = {"kind": INVENTORY_KIND, "items": {
                "tpac:program:2040": {
                    "source_namespace": "program", "source_event_id": "2040",
                    "list_url": "https://tpac.org.taipei/program",
                    "detail_url": "https://tpac.org.taipei/program/2040",
                    "list_sha": "a" * 64, "last_observed": OBS,
                    "status": "REVIEW_DETAIL_PARSED", "attempts": 0,
                    "last_attempt": None, "reason": "REVIEW_FIELDS_NOT_FORMALLY_ACCEPTED",
                },
            }}
            before = write_detail_inventory(live, root)["sha256"]
            catalogs = {}
            for catalog, sid in (("program", "2040"), ("event", "1301")):
                cls = "card-" + catalog
                title = "封存隔離回歸活動"
                raw = (f'<a class="{cls}" href="/{catalog}/{sid}" title="{title}">'
                       f'<div class="{cls}__text-title">{title}</div></a>').encode()
                path = root / (catalog + ".html")
                path.write_bytes(raw)
                url = "https://tpac.org.taipei/" + catalog
                catalogs[catalog] = {
                    "list_file": str(path), "details": {},
                    "list_receipt": {
                        "evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                        "source_url": url, "body_sha256": hashlib.sha256(raw).hexdigest(),
                        "body_bytes": len(raw), "capture_started_at": OBS,
                        "observed_at": None, "http_status": None, "robots_allowed": None,
                    },
                }
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"mode": "archived", "catalogs": catalogs}),
                                encoding="utf-8")
            command = [sys.executable, "-m", "scripts.p30_tpac_multi_event_refresh",
                       "--inventory-input", str(manifest), "--repo-root", str(root)]
            first = subprocess.run(command, capture_output=True, text=True, check=True)
            second = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(first.stdout)["inventory"]["sha256"],
                             json.loads(second.stdout)["inventory"]["sha256"])
            restored, after = load_detail_inventory(root)
            self.assertEqual(after, before)
            self.assertEqual(restored, live)
            archived, archived_sha = load_detail_inventory(root / "_isolated_archive_replay")
            self.assertIsNotNone(archived_sha)
            self.assertEqual(len(archived["items"]), 2)
            self.assertEqual(archived["items"]["tpac:program:2040"]["status"],
                             "PENDING_DETAIL_BUDGET")
            self.assertFalse((root / "docs" / "data.json").exists())

    def test_archived_cli_rejects_new_list_snapshot_without_mutating_cas(self):
        # Regression: an immutable archive replay must never replace a sealed
        # LIST snapshot for the same event ID with different source bytes.
        import subprocess
        import sys
        from scripts.p30_tpac_multi_event_refresh import load_detail_inventory
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalogs = {}
            for catalog, sid in (("program", "2040"), ("event", "1301")):
                cls = "card-" + catalog
                title = "封存快照不可變驗證"
                raw = (f'<a class="{cls}" href="/{catalog}/{sid}" title="{title}">'
                       f'<div class="{cls}__text-title">{title}</div></a>').encode()
                path = root / (catalog + ".html")
                path.write_bytes(raw)
                url = "https://tpac.org.taipei/" + catalog
                catalogs[catalog] = {"list_file": str(path), "details": {},
                    "list_receipt": {"evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                        "source_url": url, "body_sha256": hashlib.sha256(raw).hexdigest(),
                        "body_bytes": len(raw), "capture_started_at": OBS,
                        "observed_at": None, "http_status": None, "robots_allowed": None}}
            manifest = root / "archive.json"
            manifest.write_text(json.dumps({"mode": "archived", "catalogs": catalogs}), encoding="utf-8")
            cmd = [sys.executable, "-m", "scripts.p30_tpac_multi_event_refresh",
                   "--inventory-input", str(manifest), "--repo-root", str(root)]
            first = subprocess.run(cmd, capture_output=True, text=True, check=True)
            original_sha = json.loads(first.stdout)["inventory"]["sha256"]
            source = root / "program.html"
            changed = source.read_bytes().replace("封存快照不可變驗證".encode(), "另一份封存快照驗證".encode())
            source.write_bytes(changed)
            receipt = catalogs["program"]["list_receipt"]
            receipt["body_sha256"] = hashlib.sha256(changed).hexdigest()
            receipt["body_bytes"] = len(changed)
            manifest.write_text(json.dumps({"mode": "archived", "catalogs": catalogs}), encoding="utf-8")
            denied = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn("TPAC_ARCHIVE_SNAPSHOT_DRIFT_HOLD", denied.stderr)
            _, after_sha = load_detail_inventory(root / "_isolated_archive_replay")
            self.assertEqual(after_sha, original_sha)

    def test_archived_cli_rejects_archive_root_symlink_before_any_write(self):
        # Regression: the archive CAS namespace must not resolve through a
        # symlink into an unrelated directory, even when receipts are valid.
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            foreign = root / "foreign"
            foreign.mkdir()
            archive_link = root / "_isolated_archive_replay"
            try:
                archive_link.symlink_to(foreign, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this host")
            catalogs = {}
            for catalog, sid in (("program", "2040"), ("event", "1301")):
                cls = "card-" + catalog
                title = "封存符號連結回歸"
                raw = (f'<a class="{cls}" href="/{catalog}/{sid}" title="{title}">'
                       f'<div class="{cls}__text-title">{title}</div></a>').encode()
                source = root / (catalog + ".html")
                source.write_bytes(raw)
                url = "https://tpac.org.taipei/" + catalog
                catalogs[catalog] = {
                    "list_file": str(source), "details": {},
                    "list_receipt": {
                        "evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                        "source_url": url, "body_sha256": hashlib.sha256(raw).hexdigest(),
                        "body_bytes": len(raw), "capture_started_at": OBS,
                        "observed_at": None, "http_status": None,
                        "robots_allowed": None,
                    },
                }
            manifest = root / "archive.json"
            manifest.write_text(json.dumps({"mode": "archived", "catalogs": catalogs}),
                                encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "scripts.p30_tpac_multi_event_refresh",
                 "--inventory-input", str(manifest), "--repo-root", str(root)],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("TPAC_ARCHIVE_ROOT_SYMLINK_HOLD", result.stderr)
            self.assertEqual(list(foreign.iterdir()), [])
            self.assertFalse((root / "docs/data.json").exists())


    def test_original_event_archive_observation_without_capture_start(self):
        # Native /event receipt contains per-body observed_at, not capture_started_at.
        # Preserve that distinction and reject any fabricated LIVE authority.
        from scripts.p30_tpac_multi_event_refresh import _archived_body
        raw = b"<html><body>Original event evidence</body></html>"
        url = "https://tpac.org.taipei/event/1301"
        receipt = {"evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                   "source_url": url, "body_sha256": hashlib.sha256(raw).hexdigest(),
                   "body_bytes": len(raw), "capture_started_at": None,
                   "observed_at": "2026-11-08T14:49:08.662855+00:00",
                   "http_status": None, "robots_allowed": None}
        self.assertIsNotNone(_archived_body(raw, receipt, url, "event", "1301"))
        for changes in ({"http_status": 200}, {"robots_allowed": True},
                        {"capture_started_at": "2026-11-08T14:49:00+00:00"}):
            bad = dict(receipt, **changes)
            with self.assertRaisesRegex(ValueError, "TPAC_ARCHIVE_AUTHORITY_ESCALATION_HOLD"):
                _archived_body(raw, bad, url, "event", "1301")
        missing = dict(receipt, observed_at=None)
        with self.assertRaisesRegex(ValueError, "TPAC_ARCHIVE_CAPTURE_TIMESTAMP_MISSING_HOLD"):
            _archived_body(raw, missing, url, "event", "1301")
        program_url = "https://tpac.org.taipei/program/1301"
        program_receipt = dict(receipt, source_url=program_url)
        with self.assertRaisesRegex(ValueError, "TPAC_ARCHIVE_CAPTURE_TIMESTAMP_MISSING_HOLD"):
            _archived_body(raw, program_receipt, program_url, "program", "1301")



    def test_partial_archived_manifest_requires_raw_detail_replay(self):
        # Prior archive status alone must not masquerade as replayable DETAIL bytes.
        from scripts.p30_tpac_multi_event_refresh import archived_inventory_cli, load_detail_inventory
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalogs = {}
            for catalog, sid in (("program", "2040"), ("event", "1301")):
                cls = "card-" + catalog
                raw = (f'<a class="{cls}" href="/{catalog}/{sid}" title="封存活動">'
                       f'<div class="{cls}__text-title">封存活動</div></a>').encode()
                path = root / (catalog + ".html")
                path.write_bytes(raw)
                url = "https://tpac.org.taipei/" + catalog
                catalogs[catalog] = {"list_file": str(path), "details": {},
                    "list_receipt": {"evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                        "source_url": url, "body_sha256": hashlib.sha256(raw).hexdigest(),
                        "body_bytes": len(raw), "capture_started_at": OBS,
                        "observed_at": None, "http_status": None, "robots_allowed": None}}
            # Archived DETAIL coverage now requires same-ID, source-owned H1,
            # not merely a caller-consistent SHA for arbitrary HTML.
            body = (b'<article class="page-program__article">'
                    + " <h1>封存活動</h1>".encode("utf-8")
                    + b"</article>")
            detail_path = root / "detail.html"
            detail_path.write_bytes(body)
            detail_url = "https://tpac.org.taipei/program/2040"
            catalogs["program"]["details"]["2040"] = {"detail_file": str(detail_path),
                "receipt": {"evidence_class": "VERIFIED_ARCHIVED_BODY_ONLY",
                    "source_url": detail_url, "body_sha256": hashlib.sha256(body).hexdigest(),
                    "body_bytes": len(body), "capture_started_at": OBS,
                    "observed_at": None, "http_status": None, "robots_allowed": None}}
            manifest = root / "archive.json"
            manifest.write_text(json.dumps({"mode": "archived", "catalogs": catalogs}), encoding="utf-8")
            first = archived_inventory_cli(manifest, root)
            self.assertEqual(first["counts"]["detail_available"], 1)
            verified_record = catalogs["program"]["details"]["2040"]
            catalogs["program"]["details"] = {}
            manifest.write_text(json.dumps({"mode": "archived", "catalogs": catalogs}), encoding="utf-8")
            second = archived_inventory_cli(manifest, root)
            saved, second_sha = load_detail_inventory(root / "_isolated_archive_replay")
            self.assertEqual(saved["items"]["tpac:program:2040"]["status"],
                             "PENDING_DETAIL_BUDGET")
            self.assertEqual(saved["items"]["tpac:program:2040"]["reason"],
                             "PRIOR_ARCHIVED_DETAIL_BYTES_NOT_REPLAYED_HOLD")
            self.assertFalse(saved["items"]["tpac:program:2040"]["archive_field_evidence_current"])
            self.assertEqual(saved["items"]["tpac:program:2040"]["archive_field_hold_reason"],
                             "DETAIL_BYTES_NOT_REPLAYED_HOLD")
            self.assertEqual(second["counts"]["detail_available"], 0)
            self.assertEqual(second["counts"]["pending_detail_budget"], 2)
            self.assertEqual(second["counts"]["source_cards"], 2)
            self.assertNotEqual(first["inventory"]["sha256"], second_sha)
            self.assertIn("tpac:program:2040", second["next_detail_ids"])
            # The historical CAS remains auditable, but only a re-supplied
            # identical raw body/receipt may restore current archive coverage.
            catalogs["program"]["details"]["2040"] = verified_record
            manifest.write_text(json.dumps({"mode": "archived", "catalogs": catalogs}),
                                encoding="utf-8")
            third = archived_inventory_cli(manifest, root)
            self.assertEqual(third["counts"]["detail_available"], 1)
            self.assertEqual(third["counts"]["pending_detail_budget"], 1)
            self.assertEqual(third["inventory"]["sha256"], first["inventory"]["sha256"])
            # A tampered body may not promote a forged archive status or mutate CAS.
            detail_path.write_bytes(b"<html>tampered archive body</html>")
            with self.assertRaisesRegex(ValueError, "TPAC_ARCHIVE_BYTES_SHA_HOLD"):
                archived_inventory_cli(manifest, root)
            _, after_tamper_sha = load_detail_inventory(root / "_isolated_archive_replay")
            self.assertEqual(after_tamper_sha, third["inventory"]["sha256"])
            self.assertFalse((root / "docs" / "data.json").exists())

class PersistedHoldSchemaRegressionTests(unittest.TestCase):
    def test_falsey_malformed_hold_values_fail_closed(self):
        # A corrupt persisted HOLD field must not be silently normalized to
        # an empty list, which would hide a LIST/DETAIL quality conflict.
        from scripts.p30_tpac_multi_event_refresh import _semantic_event_payload
        for malformed in (None, "", 0, False, {}, ()):
            with self.subTest(malformed=repr(malformed)):
                event = {"_candidate": {"field_roles": {},
                                        "hold_reasons": malformed}}
                with self.assertRaisesRegex(
                        ValueError, "TPAC_SEMANTIC_HOLD_REASONS_SCHEMA_HOLD"):
                    _semantic_event_payload(event)

    def test_absent_and_valid_hold_semantics_remain_stable(self):
        from scripts.p30_tpac_multi_event_refresh import _semantic_event_payload
        absent = {"_candidate": {"field_roles": {}}}
        empty = {"_candidate": {"field_roles": {}, "hold_reasons": []}}
        self.assertEqual(_semantic_event_payload(absent),
                         _semantic_event_payload(empty))
        a = {"_candidate": {"field_roles": {},
                            "hold_reasons": ["LIST_DETAIL_PERIOD_CONFLICT", "VENUE_HOLD"]}}
        b = {"_candidate": {"field_roles": {},
                            "hold_reasons": ["VENUE_HOLD", "LIST_DETAIL_PERIOD_CONFLICT",
                                             "VENUE_HOLD"]}}
        self.assertEqual(_semantic_event_payload(a), _semantic_event_payload(b))
        self.assertNotEqual(_semantic_event_payload(a), _semantic_event_payload(empty))

class EventCoreRoleSemanticRegressionTests(unittest.TestCase):
    def test_event_owned_core_role_change_is_not_discarded(self):
        # A /event verified period may change while public display fields
        # remain empty. The REVIEW LKG must see this as a real source delta.
        from scripts.p30_tpac_multi_event_refresh import _semantic_event_payload
        base = {"source_namespace": "event", "date": "", "_candidate": {
            "field_roles": {"EVENT_ACTIVITY_PERIOD": {
                "role": "EVENT_ACTIVITY_PERIOD", "value": "2026-11-20 - 2026-11-21",
                "source_body_sha256": "old", "observed_at": "2026-11-08T00:00:00Z"}}}}
        import copy
        changed = copy.deepcopy(base)
        changed["_candidate"]["field_roles"]["EVENT_ACTIVITY_PERIOD"]["value"] = "2026-11-20 - 2026-11-22"
        self.assertNotEqual(_semantic_event_payload(base), _semantic_event_payload(changed))
        receipt_only = copy.deepcopy(base)
        receipt_only["_candidate"]["field_roles"]["EVENT_ACTIVITY_PERIOD"]["source_body_sha256"] = "new"
        receipt_only["_candidate"]["field_roles"]["EVENT_ACTIVITY_PERIOD"]["observed_at"] = "2026-11-09T00:00:00Z"
        self.assertEqual(_semantic_event_payload(base), _semantic_event_payload(receipt_only))


class EventPriorLkgIsolationRegressionTests(unittest.TestCase):
    def test_corrupt_event_lkg_does_not_abort_other_verified_detail(self):
        # Two independent /event identities: corrupted persisted semantics
        # must not prevent the second valid archived DETAIL from being staged.
        from unittest.mock import patch
        from datetime import datetime, timezone
        from scripts.p30_tpac_multi_event_refresh import (
            KIND, refresh_event_plan,
        )
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        old_bad = {"source_event_id": "1301", "_candidate": {
            "field_roles": {"EVENT_ACTIVITY_PERIOD": None}}}
        prior = {"kind": KIND, "events": {"tpac:event:1301": old_bad}}
        cards = {sid: {"source_event_id": sid, "title": "隔離活動" + sid}
                 for sid in ("1301", "2072")}
        def inspect(card, body, receipt, clock):
            sid = card["source_event_id"]
            import hashlib
            return {
                "identity": "tpac:event:" + sid, "source_event_id": sid,
                "url": "https://tpac.org.taipei/event/" + sid,
                "detail_body_sha256": hashlib.sha256(body).hexdigest(),
                "decision": "SOURCE_OWNED_PARTIAL_FIELDS_REQUIRE_INDEPENDENT_ACCEPTANCE",
                "verified_core_roles": {"EVENT_ACTIVITY_PERIOD": "2026-11-20 - 2026-11-21"},
                "observed_at": "2026-11-18T00:00:00+00:00",
                "title": card["title"], "activity_kind": "展覽",
                "held_fields": ["FORMAL_FIELD_HOLD"],
                "list_period": "2026-11-20 - 2026-11-21",
                "detail_period": "2026-11-20 - 2026-11-21",
            }
        pairs = {sid: {"body": b"sealed archive detail", "receipt": {}}
                 for sid in cards}
        with patch("scripts.p30_tpac_catalog_topology.discover_catalog",
                   return_value=cards), patch(
                   "scripts.p30_tpac_event_detail_review.inspect_event_detail",
                   side_effect=inspect):
            report = refresh_event_plan(b"sealed archive list", {}, pairs, prior, now)
        self.assertEqual(report["decision"], "REVIEW_SNAPSHOT_READY_NOT_FORMAL")
        self.assertEqual(report["qualified"], 1)
        self.assertEqual(report["added"], 1)
        self.assertEqual(report["changed"], 0)
        self.assertEqual(report["retained_previous"], 1)
        self.assertFalse(report["source_coverage_complete"])
        self.assertIn("TPAC_PRIOR_EVENT_SEMANTIC_HOLD", report["rejected"]["1301"])
        self.assertEqual(report["events"]["tpac:event:1301"], old_bad)
        self.assertIn("tpac:event:2072", report["events"])
        self.assertFalse(report["events"]["tpac:event:2072"]["published"])

    def test_all_corrupt_event_lkg_preserves_original_snapshot(self):
        from unittest.mock import patch
        from datetime import datetime, timezone
        from scripts.p30_tpac_multi_event_refresh import KIND, refresh_event_plan
        bad = {"_candidate": {"field_roles": {"EVENT_ACTIVITY_PERIOD": None}}}
        prior = {"kind": KIND, "events": {"tpac:event:1301": bad}}
        card = {"source_event_id": "1301", "title": "封存活動"}
        import hashlib
        body = b"archived detail"
        review = {"identity": "tpac:event:1301", "source_event_id": "1301",
                  "url": "https://tpac.org.taipei/event/1301",
                  "detail_body_sha256": hashlib.sha256(body).hexdigest(),
                  "decision": "SOURCE_OWNED_PARTIAL_FIELDS_REQUIRE_INDEPENDENT_ACCEPTANCE",
                  "verified_core_roles": {}, "observed_at": "2026-11-18T00:00:00+00:00",
                  "title": "封存活動", "activity_kind": "展覽",
                  "held_fields": [], "list_period": "", "detail_period": ""}
        with patch("scripts.p30_tpac_catalog_topology.discover_catalog",
                   return_value={"1301": card}), patch(
                   "scripts.p30_tpac_event_detail_review.inspect_event_detail",
                   return_value=review):
            result = refresh_event_plan(b"archive", {},
                                        {"1301": {"body": body, "receipt": {}}},
                                        prior, datetime(2026, 11, 18, tzinfo=timezone.utc))
        self.assertEqual(result["decision"], "HOLD_NO_QUALIFIED_EVENT_DETAILS_PRESERVE_LKG")
        self.assertEqual(result["events"], prior["events"])
        self.assertEqual(result["qualified"], 0)
        self.assertEqual(result["added"], 0)
        self.assertEqual(result["changed"], 0)

class EventPeriodSemanticDriftRegressionTests(unittest.TestCase):
    def test_changed_list_period_is_not_receipt_only(self):
        # Source-owned LIST period drift must be retained as a semantic change,
        # even when DETAIL and accepted core roles are otherwise identical.
        import copy
        from scripts.p30_tpac_multi_event_refresh import _semantic_event_payload
        prior = {
            "source_namespace": "event", "identity": "tpac:event:1301",
            "source_event_id": "1301",
            "_candidate": {
                "field_roles": {"EVENT_ACTIVITY_PERIOD": {
                    "role": "EVENT_ACTIVITY_PERIOD", "value": "2026-11-20 - 2026-11-21"}},
                "hold_reasons": ["LIST_DETAIL_PERIOD_CONFLICT_HOLD"],
                "list_period": "2026-11-19 - 2026-11-21",
                "detail_period": "2026-11-20 - 2026-11-21",
                "observed_at": "2026-11-08T00:00:00Z",
            },
        }
        drift = copy.deepcopy(prior)
        drift["_candidate"]["list_period"] = "2026-11-18 - 2026-11-21"
        self.assertNotEqual(_semantic_event_payload(prior),
                            _semantic_event_payload(drift))
        receipt_only = copy.deepcopy(prior)
        receipt_only["_candidate"]["observed_at"] = "2026-11-09T00:00:00Z"
        self.assertEqual(_semantic_event_payload(prior),
                         _semantic_event_payload(receipt_only))

    def test_changed_detail_period_is_not_receipt_only(self):
        import copy
        from scripts.p30_tpac_multi_event_refresh import _semantic_event_payload
        prior = {"source_event_id": "2072", "_candidate": {
            "field_roles": {}, "hold_reasons": ["FIELD_REVIEW_HOLD"],
            "list_period": "2026-11-20 - 2026-11-21",
            "detail_period": "2026-11-20 - 2026-11-21"}}
        changed = copy.deepcopy(prior)
        changed["_candidate"]["detail_period"] = "2026-11-20 - 2026-11-22"
        self.assertNotEqual(_semantic_event_payload(prior),
                            _semantic_event_payload(changed))


if __name__ == "__main__":
    unittest.main()


class ArchivedInventoryVersionRecoveryTests(unittest.TestCase):
    def test_real_disk_cas_versions_restart_and_corruption_hold(self):
        # The previous complete inventory survives restart, while a corrupt
        # version cannot be loaded or silently replace the current CAS.
        import tempfile
        from pathlib import Path
        from scripts.p30_tpac_multi_event_refresh import (
            INVENTORY_KIND, write_detail_inventory, load_detail_inventory,
            read_detail_inventory_version,
        )
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            initial = {"kind": INVENTORY_KIND, "items": {}}
            first = write_detail_inventory(initial, root)
            row = {"source_namespace": "program", "source_event_id": "2040",
                   "detail_url": "https://tpac.org.taipei/program/2040",
                   "status": "PENDING_DETAIL_BUDGET", "attempts": 0}
            second_document = {"kind": INVENTORY_KIND,
                               "items": {"tpac:program:2040": row}}
            second = write_detail_inventory(second_document, root, first["sha256"])
            saved, saved_sha = read_detail_inventory_version(root, first["sha256"])
            self.assertEqual(saved, initial)
            self.assertEqual(saved_sha, first["sha256"])
            current, current_sha = load_detail_inventory(root)
            self.assertEqual(current, second_document)
            self.assertEqual(current_sha, second["sha256"])
            # A second unchanged replay is idempotent.
            repeat = write_detail_inventory(second_document, root, second["sha256"])
            self.assertEqual(repeat["sha256"], second["sha256"])
            history = root / "_isolated_review" / "tpac" / "inventory_versions"
            self.assertEqual(len(list(history.glob("*.json"))), 1)
            with self.assertRaisesRegex(ValueError, "TPAC_INVENTORY_VERSION_SHA_HOLD"):
                read_detail_inventory_version(root, "../escape")
            predecessor = history / (first["sha256"] + ".json")
            predecessor.write_bytes(b"corrupted")
            with self.assertRaisesRegex(ValueError, "TPAC_INVENTORY_HISTORY_CORRUPT_HOLD"):
                read_detail_inventory_version(root, first["sha256"])
            # Bad historical evidence cannot contaminate the current snapshot.
            current_again, current_again_sha = load_detail_inventory(root)
            self.assertEqual(current_again, second_document)
            self.assertEqual(current_again_sha, second["sha256"])
            # Replaying the valid current version is still safe and idempotent;
            # recovery of the corrupted predecessor remains explicitly denied.
            self.assertEqual(write_detail_inventory(second_document, root,
                             second["sha256"])["sha256"], second["sha256"])
            self.assertEqual(load_detail_inventory(root)[1], second["sha256"])

    def test_history_link_failure_keeps_current_cas_and_no_partial_version(self):
        # Simulate failure at the atomic history publication boundary.
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts.p30_tpac_multi_event_refresh import (
            INVENTORY_KIND, write_detail_inventory, load_detail_inventory,
        )
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            initial = {"kind": INVENTORY_KIND, "items": {}}
            first = write_detail_inventory(initial, root)
            changed = {"kind": INVENTORY_KIND, "items": {
                "tpac:event:1301": {
                    "source_namespace": "event", "source_event_id": "1301",
                    "detail_url": "https://tpac.org.taipei/event/1301",
                    "status": "PENDING_DETAIL_BUDGET", "attempts": 0,
                }
            }}
            with patch("scripts.p30_tpac_multi_event_refresh.os.link",
                       side_effect=OSError("simulated crash before publication")):
                with self.assertRaisesRegex(OSError, "simulated crash"):
                    write_detail_inventory(changed, root, first["sha256"])
            self.assertEqual(load_detail_inventory(root), (initial, first["sha256"]))
            history = root / "_isolated_review" / "tpac" / "inventory_versions"
            self.assertEqual(list(history.glob("*.json")), [])
            self.assertEqual(list(history.glob(".history-*")), [])
            second = write_detail_inventory(changed, root, first["sha256"])
            self.assertEqual(load_detail_inventory(root)[1], second["sha256"])
            self.assertTrue((history / (first["sha256"] + ".json")).is_file())

    def test_stale_cas_cannot_create_history_or_change_snapshot(self):
        import tempfile
        from pathlib import Path
        from scripts.p30_tpac_multi_event_refresh import (
            INVENTORY_KIND, write_detail_inventory, load_detail_inventory,
        )
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            document = {"kind": INVENTORY_KIND, "items": {}}
            first = write_detail_inventory(document, root)
            with self.assertRaisesRegex(ValueError, "TPAC_INVENTORY_CAS_HOLD"):
                write_detail_inventory(document, root, "0" * 64)
            self.assertEqual(load_detail_inventory(root)[1], first["sha256"])
            self.assertFalse((root / "_isolated_review" / "tpac" /
                              "inventory_versions").exists())

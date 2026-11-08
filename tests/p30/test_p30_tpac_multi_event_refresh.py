"""Deterministic two-ID positive/negative TPAC fixed multi-event refresh tests."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.p30_tpac_multi_event_refresh import (
    KIND, ROOT, discover_list, refresh_plan, write_isolated_plan,
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


if __name__ == "__main__":
    unittest.main()

"""Integration tests reuse historical #217/#221 reader contracts, no HTTP."""
import base64
import copy
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import p30_venue02bo_tainex_exhibition as tainex
from scripts import p30_l9dc_famiticket_teca as fami
from scripts.p30_multisource_review_lkg import (
    REGISTRY, inspect_raw_pair, plan, write_isolated, load_previous_snapshot)
from scripts.p30_tainex_archived_native_bridge import archived_inputs

NOW = datetime(2026, 11, 10, 5, 55, tzinfo=timezone.utc)
TAINEX_STAMP = "2026-11-02T06:57:00+08:00"
FAMI_STAMP = "2026-11-02T06:55:00+08:00"


def tainex_packet():
    obs = dict(list_url=tainex.LIST, list_detail_href=tainex.DETAIL,
               detail_url=tainex.DETAIL, list_title=tainex.TITLE,
               detail_title=tainex.TITLE, period_label="展覽活動期間",
               period_start=tainex.START, period_end=tainex.END,
               venue_label="活動地點", venue_hall=tainex.HALL,
               floors=list(tainex.FLOORS), organizer_label="主辦單位",
               organizer=tainex.ORGANIZER, external_website_label="官方網站",
               external_website=tainex.ORGANIZER_SITE)
    return {"source": "tainex", "observation": obs, "observed_at": TAINEX_STAMP}


def fami_packet():
    obs = dict(list_url=fami.LIST, list_detail_href=fami.DETAIL,
               detail_url=fami.DETAIL, list_title=fami.TITLE,
               detail_title=fami.TITLE, period_start=fami.PERIOD[0],
               period_end=fami.PERIOD[1], exhibition_hours="10:00-18:00",
               venue=fami.VENUE, prices=dict(fami.PRICES),
               purchase_control="我要購票")
    return {"source": "famiticket", "observation": obs, "observed_at": FAMI_STAMP}


class MultiSourceBridge(unittest.TestCase):
    def test_two_real_historical_source_reader_contracts_to_common_core(self):
        r = plan([tainex_packet(), fami_packet()], as_of=NOW)
        self.assertEqual(r["source_reader_qualified"], 2)
        self.assertEqual(r["source_platforms"], ["FAMITICKET", "TAINEX"])
        self.assertEqual(r["source_gates"], ["P30-L9-DC", "P30-VENUE-02BO"])
        self.assertEqual(r["new_review"], 2)
        self.assertEqual(len(r["review_rows"]), 2)
        self.assertEqual(r["independently_accepted_fields"], 0)
        self.assertEqual(r["independent_native_detail_new"], 0)
        self.assertEqual(r["native_get"], r["published_delta"])
        self.assertFalse(r["commit_permitted"])
        for row in r["review_rows"]:
            self.assertEqual(row["date"], "未確認")
            self.assertEqual(row["price"], "未確認")
            self.assertEqual(row["location"], "未確認")
            self.assertEqual(row["_candidate"]["decision"], "REVIEW_WITH_HOLD")
            self.assertFalse(row["_candidate"]["published"])
            self.assertIn("SOURCE_READER_NOT_INDEPENDENT_NATIVE_ATTESTATION",
                          row["_candidate"]["hold_reasons"])

    def test_duplicate_same_id_cannot_override_lkg(self):
        p = tainex_packet()
        r = plan([p, copy.deepcopy(p)], as_of=NOW)
        self.assertEqual(len(r["review_rows"]), 1)
        self.assertEqual(r["source_reader_qualified"], 1)
        self.assertEqual(r["new_review"], 1)
        self.assertEqual(len(r["rejected"]), 1)

    def test_prior_lkg_retained_on_source_failure(self):
        old = plan([tainex_packet()], as_of=NOW)["review_rows"]
        bad = fami_packet()
        bad["observation"]["detail_title"] = "unrelated"
        r = plan([bad], previous=old, as_of=NOW)
        self.assertEqual(r["decision"], "HOLD_NO_VALID_NEW_SOURCE")
        self.assertEqual(r["retained_lkg"], 1)
        self.assertEqual(r["review_rows"], old)
        self.assertEqual(len(r["rejected"]), 1)

    def test_source_namespace_and_role_fail_closed(self):
        for key, value in [
            ("list_detail_href", tainex.DETAIL.replace("691", "690")),
            ("period_label", "演出開始"),
            ("venue_hall", "南港展覽館2館"),
            ("ticket_session_id", "691"),
            ("admission_price", 100),
        ]:
            p = tainex_packet()
            p["observation"][key] = value
            r = plan([p], as_of=NOW)
            self.assertEqual(r["source_reader_qualified"], 0, key)
            self.assertEqual(len(r["rejected"]), 1, key)

    def test_famiticket_presale_not_general_minimum(self):
        for key, value in [
            ("list_detail_href", fami.DETAIL + "#bad"),
            ("prices", {"presale_single_day": 150}),
            ("general_admission_price", 150),
            ("ticket_session_id", "fake"),
        ]:
            p = fami_packet()
            p["observation"][key] = value
            r = plan([p], as_of=NOW)
            self.assertEqual(r["source_reader_qualified"], 0, key)

    def test_future_time_and_unregistered_source(self):
        p = tainex_packet()
        p["observed_at"] = "2026-11-11T00:00:00Z"
        self.assertEqual(plan([p], as_of=NOW)["source_reader_qualified"], 0)
        p = tainex_packet()
        p["source"] = "unknown"
        self.assertEqual(plan([p], as_of=NOW)["source_reader_qualified"], 0)

    def test_historical_replay_cannot_masquerade_as_new_live_observation(self):
        # Same historical content with a 2026-11-10 clock must never replace LKG.
        old = plan([tainex_packet()], as_of=NOW)["review_rows"]
        replay = tainex_packet()
        replay["observed_at"] = "2026-11-10T12:00:00+08:00"
        r = plan([replay], previous=old, as_of=NOW)
        self.assertEqual(r["source_reader_qualified"], 0)
        self.assertEqual(r["changed_review"], 0)
        self.assertEqual(r["retained_lkg"], 1)
        self.assertEqual(r["review_rows"], old)
        self.assertIn("HISTORICAL_REPLAY_CLOCK_ESCALATION_HOLD", r["rejected"][0]["reason"])
        fami_replay = fami_packet()
        fami_replay["observed_at"] = "2026-11-03T00:00:00+08:00"
        r2 = plan([fami_replay], as_of=NOW)
        self.assertEqual(r2["source_reader_qualified"], 0)
        self.assertEqual(r2["new_review"], 0)

    def test_reconstructed_replay_clock_is_exactly_bound_not_only_day_bounded(self):
        # Neither a fabricated later clock nor a backdated clock may create
        # a new REVIEW LKG revision from the same unaudited source packet.
        old = plan([tainex_packet(), fami_packet()], as_of=NOW)["review_rows"]
        for make, stamp in ((tainex_packet, "2026-11-02T15:59:00+08:00"),
                            (tainex_packet, "2026-11-01T06:57:00+08:00"),
                            (fami_packet, "2026-11-02T07:55:00+08:00"),
                            (fami_packet, "2026-11-01T06:55:00+08:00")):
            packet = make()
            packet["observed_at"] = stamp
            result = plan([packet], previous=old, as_of=NOW)
            self.assertEqual(result["changed_review"], 0)
            self.assertEqual(result["new_review"], 0)
            self.assertEqual(result["review_rows"], old)
            self.assertIn("HISTORICAL_REPLAY_CLOCK_BINDING_HOLD",
                          result["rejected"][0]["reason"])
        for key, stamp in (("TAINEX", "2026-11-02T07:57:00+08:00"),
                           ("FAMITICKET", "2026-11-01T06:55:00+08:00")):
            altered = copy.deepcopy(old)
            row = next(r for r in altered if r["_candidate"]["platform_id"] == key)
            row["scraped_at"] = stamp
            with self.assertRaisesRegex(ValueError, "PRIOR_LKG_SOURCE_BINDING_HOLD"):
                plan([], previous=altered, as_of=NOW)

    def test_prior_replay_clock_escalation_rejected_on_restart(self):
        old = plan([tainex_packet()], as_of=NOW)["review_rows"]
        old[0]["scraped_at"] = "2026-11-03T00:00:00+08:00"
        with self.assertRaisesRegex(ValueError, "PRIOR_LKG_SOURCE_BINDING_HOLD"):
            plan([], previous=old, as_of=NOW)

    def test_prior_lkg_tampering_is_hard_failure(self):
        old = plan([tainex_packet()], as_of=NOW)["review_rows"]
        old[0]["_candidate"]["published"] = True
        with self.assertRaisesRegex(ValueError, "PRIOR_LKG_INTEGRITY_HOLD"):
            plan([fami_packet()], previous=old, as_of=NOW)

    def test_replay_does_not_claim_native_or_field_authority(self):
        r = plan([fami_packet()], as_of=NOW)
        self.assertEqual(r["source_platforms"], ["FAMITICKET"])
        self.assertEqual(r["review_rows"][0]["_candidate"]["field_evidence"], {})
        self.assertFalse(r["cross_host_cas_attested"])
        self.assertFalse(r["formal_data_mutated"])
        self.assertFalse(r["scheduler_enabled"])

    def test_atomic_isolated_output_and_docs_forbidden(self):
        r = plan([tainex_packet(), fami_packet()], as_of=NOW)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "_isolated_review" / "multi" / "plan.json"
            digest = write_isolated(r, out, root)
            self.assertEqual(len(digest), 64)
            self.assertTrue(out.is_file())
            with self.assertRaisesRegex(ValueError, "ISOLATED_OUTPUT_ONLY_HOLD"):
                write_isolated(r, root / "docs" / "data.json", root)
            self.assertFalse((root / "docs" / "data.json").exists())


    def test_source_owned_role_receipts_survive_core_normalization(self):
        r = plan([tainex_packet(), fami_packet()], as_of=NOW)
        self.assertEqual(r["source_review_field_count"], 15)
        self.assertEqual(len(r["source_review_receipts"]), 2)
        roles = {f["role"] for item in r["source_review_receipts"]
                 for f in item["source_reader_fields"]}
        self.assertIn("EXHIBITION_PERIOD_START", roles)
        self.assertIn("PRESALE_PRICE", roles)
        self.assertIn("VENUE_HALL", roles)
        for item in r["source_review_receipts"]:
            self.assertEqual(len(item["source_reader_fields_sha256"]), 64)
            self.assertFalse(item["native_http_attested"])
            self.assertFalse(item["formal_field_accepted"])
            self.assertTrue(all(f["decision"] == "REVIEW"
                                for f in item["source_reader_fields"]))
        self.assertEqual(r["independently_accepted_fields"], 0)
        self.assertEqual(r["published_delta"], 0)

    def test_prior_lkg_rejects_foreign_identity_and_role_forgery(self):
        old = plan([tainex_packet()], as_of=NOW)["review_rows"]
        changes = [
            ("url", "https://example.com/event/691"),
            ("title", "Other event title"),
            ("platform", "Other platform"),
            ("date", "2026-11-13"),
        ]
        for key, value in changes:
            altered = copy.deepcopy(old)
            altered[0][key] = value
            with self.assertRaisesRegex(
                ValueError,
                "PRIOR_LKG_(?:SOURCE_BINDING|INTEGRITY|NONCANONICAL)_HOLD"
            ):
                plan([fami_packet()], previous=altered, as_of=NOW)
        for key, value in [
            ("source_event_id", "690"),
            ("record_id", "TAINEX:event:690"),
            ("source_class", "NATIVE_ATTESTED"),
            ("sources", ["https://example.com", tainex.DETAIL]),
            ("field_evidence", {"price": {"decision": "ACCEPTED"}}),
            ("hold_reasons", ["OTHER_HOLD"]),
        ]:
            altered = copy.deepcopy(old)
            altered[0]["_candidate"][key] = value
            with self.assertRaisesRegex(
                ValueError,
                "PRIOR_LKG_(?:SOURCE_BINDING|INTEGRITY|NONCANONICAL)_HOLD"
            ):
                plan([fami_packet()], previous=altered, as_of=NOW)

    def test_prior_future_lkg_cannot_poison_isolated_snapshot(self):
        old = plan([fami_packet()], as_of=NOW)["review_rows"]
        old[0]["scraped_at"] = "2026-11-11T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "PRIOR_LKG_SOURCE_BINDING_HOLD"):
            plan([tainex_packet()], previous=old, as_of=NOW)


    def test_persisted_real_historical_four_id_lkg_resume(self):
        """Persist real historical receipt review, restart with no source GET."""
        fixture_dir = Path(__file__).parent / "fixtures"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            first = plan([tainex_packet(), fami_packet()], as_of=NOW,
                         archived_native=archived_inputs(fixture_dir))
            self.assertEqual(first["new_review"], 4)
            path = root / "_isolated_review" / "multi" / "first.json"
            sha = write_isolated(first, path, root)
            previous = load_previous_snapshot(path, sha, root)
            second = plan([], previous=previous, as_of=NOW)
            self.assertEqual(second["new_review"], 0)
            self.assertEqual(second["retained_lkg"], 4)
            self.assertEqual(second["review_rows"], first["review_rows"])
            self.assertEqual(second["decision"], "HOLD_NO_VALID_NEW_SOURCE")
            self.assertEqual(second["native_get"], 0)
            self.assertEqual(second["published_delta"], 0)
            self.assertFalse(second["commit_permitted"])
            out = root / "_isolated_review" / "multi" / "second.json"
            self.assertEqual(len(write_isolated(second, out, root)), 64)
            self.assertNotEqual(path.read_bytes(), out.read_bytes())

    def test_persisted_snapshot_integrity_and_authority_fail_closed(self):
        fixture_dir = Path(__file__).parent / "fixtures"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            first = plan([tainex_packet(), fami_packet()], as_of=NOW,
                         archived_native=archived_inputs(fixture_dir))
            path = root / "_isolated_review" / "multi" / "first.json"
            sha = write_isolated(first, path, root)
            with self.assertRaisesRegex(ValueError, "PRIOR_SNAPSHOT_SHA_FORMAT_HOLD"):
                load_previous_snapshot(path, "bad", root)
            with self.assertRaisesRegex(ValueError, "PRIOR_SNAPSHOT_ISOLATION_HOLD"):
                load_previous_snapshot(root / "docs" / "data.json", sha, root)
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "PRIOR_SNAPSHOT_SHA_MISMATCH_HOLD"):
                load_previous_snapshot(path, sha, root)
            import hashlib
            import json
            forged = copy.deepcopy(first)
            forged["commit_permitted"] = True
            raw = (json.dumps(forged, sort_keys=True) + "\n").encode("utf-8")
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "PRIOR_SNAPSHOT_AUTHORITY_HOLD"):
                load_previous_snapshot(path, hashlib.sha256(raw).hexdigest(), root)
            forged = copy.deepcopy(first)
            forged["review_rows"].append(copy.deepcopy(forged["review_rows"][0]))
            raw = (json.dumps(forged, sort_keys=True) + "\n").encode("utf-8")
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "PRIOR_SNAPSHOT_IDENTITY_HOLD"):
                load_previous_snapshot(path, hashlib.sha256(raw).hexdigest(), root)



def raw_pair_packet(source):
    """Synthetic HTML tests parser behavior; not native HTTP evidence."""
    module = REGISTRY[source]["module"]
    list_html = ('<html><body><a href="' + module.DETAIL + '">' +
                 module.TITLE + '</a></body></html>').encode("utf-8")
    detail_html = ('<html><body><h1>' + module.TITLE +
                   '</h1></body></html>').encode("utf-8")
    return {
        "source": source, "list_url": module.LIST, "detail_url": module.DETAIL,
        "observed_at": "2026-11-09T08:00:00Z",
        "list_html_b64": base64.b64encode(list_html).decode("ascii"),
        "detail_html_b64": base64.b64encode(detail_html).decode("ascii"),
    }


class RawPairIdentityAdapter(unittest.TestCase):
    def test_two_source_raw_bytes_identity_only_no_authority(self):
        import hashlib
        for source in ("tainex", "famiticket"):
            p = raw_pair_packet(source)
            receipt = inspect_raw_pair(p, NOW)
            self.assertEqual(receipt["decision"], "REVIEW_RAW_PAIR_IDENTITY_ONLY")
            self.assertEqual(receipt["source_authority"], "CALLER_SUPPLIED_UNATTESTED_BYTES")
            self.assertEqual(receipt["source_time_authority"], "UNATTESTED")
            self.assertFalse(receipt["native_http_attested"])
            self.assertFalse(receipt["raw_html_retention_verified"])
            self.assertEqual(receipt["accepted_fields"], 0)
            self.assertFalse(receipt["lkg_promoted"])
            self.assertFalse(receipt["commit_permitted"])
            self.assertEqual(receipt["raw_bodies"][0]["sha256"], hashlib.sha256(
                base64.b64decode(p["list_html_b64"])).hexdigest())
        result = plan([], as_of=NOW, raw_pairs=[
            raw_pair_packet("tainex"), raw_pair_packet("famiticket")])
        self.assertEqual(result["raw_pair_identity_parsed_unattested"], 2)
        self.assertEqual(result["new_review"], 0)
        self.assertEqual(result["independently_accepted_fields"], 0)
        self.assertEqual(result["native_get"], 0)
        self.assertEqual(result["review_rows"], [])
        self.assertFalse(result["commit_permitted"])

    def test_cross_source_wrong_link_and_detail_title_fail_closed(self):
        p = raw_pair_packet("tainex")
        other = REGISTRY["famiticket"]["module"].DETAIL
        p["list_html_b64"] = base64.b64encode(
            ('<a href="' + other + '">' + tainex.TITLE + '</a>').encode()
        ).decode("ascii")
        self.assertIn("RAW_LIST_EXACT_ID_TITLE_HOLD",
                      plan([], as_of=NOW, raw_pairs=[p])["rejected"][0]["reason"])
        p = raw_pair_packet("famiticket")
        p["detail_html_b64"] = base64.b64encode(
            b"<h1>Unrelated exhibition</h1>").decode("ascii")
        self.assertIn("RAW_DETAIL_EXACT_TITLE_HOLD",
                      plan([], as_of=NOW, raw_pairs=[p])["rejected"][0]["reason"])

    def test_untrusted_bytes_clock_script_and_duplicate_edges_fail_closed(self):
        p = raw_pair_packet("tainex")
        p["native_http_attested"] = True  # Caller claims cannot grant authority.
        p["published"] = True
        self.assertFalse(inspect_raw_pair(p, NOW)["native_http_attested"])
        self.assertFalse(inspect_raw_pair(p, NOW)["published"])
        for change, expected in (
            ({"observed_at": "2026-11-11T00:00:00Z"}, "RAW_CLOCK_FUTURE_HOLD"),
            ({"list_html_b64": "not-base64!"}, "RAW_BODY_ENCODING_HOLD"),
            ({"list_html_b64": base64.b64encode(b"\xff").decode()}, "RAW_BODY_ENCODING_HOLD"),
            ({"list_url": "https://example.org/event"}, "RAW_URL_EXACT_HOLD"),
        ):
            damaged = dict(p, **change)
            with self.assertRaisesRegex(ValueError, expected):
                inspect_raw_pair(damaged, NOW)
        title = tainex.TITLE
        href = tainex.DETAIL
        for markup in (
            '<script><a href="' + href + '">' + title + '</a></script>',
            ('<a href="' + href + '">' + title + '</a>') * 2,
        ):
            damaged = dict(p, list_html_b64=base64.b64encode(
                markup.encode("utf-8")).decode("ascii"))
            with self.assertRaisesRegex(ValueError, "RAW_LIST_EXACT_ID_TITLE_HOLD"):
                inspect_raw_pair(damaged, NOW)

    def test_raw_pair_cannot_override_prior_review_lkg(self):
        old = plan([tainex_packet()], as_of=NOW)["review_rows"]
        result = plan([], previous=old, as_of=NOW,
                      raw_pairs=[raw_pair_packet("tainex")])
        self.assertEqual(result["raw_pair_identity_parsed_unattested"], 1)
        self.assertEqual(result["retained_lkg"], 1)
        self.assertEqual(result["new_review"], 0)
        self.assertEqual(result["review_rows"], old)
        self.assertEqual(result["independently_accepted_fields"], 0)


if __name__ == "__main__":
    unittest.main()

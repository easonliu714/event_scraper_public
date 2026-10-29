#!/usr/bin/env python3
"""P30-L9-Z offline fail-closed contracts; no network, no publication."""
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

m = load(ROOT / "scripts/p30_l9z_kham_list_detail_identity.py", "l9z")
x = load(ROOT / "scripts/p30_l9x_kham_original_parser_parity.py", "l9x")
y = load(ROOT / "scripts/p30_l9y_kham_event_object_boundary.py", "l9y")
F = y.frozen_functions((ROOT / "scraper.py").read_bytes())
URL = "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=A123"

def link(title="測試音樂會", pid="A123", href=None):
    target = href if href is not None else "/application/UTK02/UTK0201_.aspx?PRODUCT_ID=" + pid
    return '<a href="' + target + '">' + title + '</a>'

def candidates(html):
    return m.list_candidates(html, F, x.allowed)

def frame(ready="complete", headings=1, matches=1):
    return {"ready": ready, "headingCandidates": headings, "exactHeadingMatches": matches}

def detail(frames=None, http=200, safe=True, same=True):
    return {"http": http, "finalAllowed": safe, "sameProductId": same,
            "frames": [frame()] * m.SNAPSHOTS if frames is None else frames}

def report(count=2, samples=None, http=200, safe=True, unsafe=0):
    rows = [{"decision": "REVIEW_EXACT_SAME_ID_STABLE_H1H2"}] * 2 if samples is None else samples
    return {"listHttp": http, "listFinalAllowed": safe,
            "listCounts": {"provisionalObjects": count, "unsafeSelected": unsafe,
                           "nonCanonical": 0}, "samples": rows}

def valid_parent():
    return (json.dumps({"production": {"eventFeedReleaseState": m.RELEASE,
                                       "goldenAccepted": 0}}).encode(),
            json.dumps({"kind": "EVENTRADAR_P30_L9Y_KHAM_EVENT_OBJECT_BOUNDARY_V1",
                        "releaseState": m.RELEASE, "published": False,
                        "decision": "REVIEW_CURRENT_PROVISIONAL_OBJECTS_HISTORIC_ZERO",
                        "static": {"acceptedObjects": 10},
                        "rendered": {"acceptedObjects": 10}}).encode())

class Contracts(unittest.TestCase):
    def test_01_kind(self):
        self.assertEqual(m.KIND, "EVENTRADAR_P30_L9Z_KHAM_LIST_DETAIL_IDENTITY_V1")
    def test_02_release(self):
        self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_03_parent(self):
        self.assertEqual(m.PARENT, "b8bd1905a875d62d131cd8db1fec814437b2fcb5")
    def test_04_frozen_source(self):
        self.assertEqual(m.git_blob((ROOT / "scraper.py").read_bytes()), m.SOURCE_BLOB)
    def test_05_exact_product_id(self):
        self.assertEqual(m.product_id(URL, x.allowed), "A123")
    def test_06_offsite_id(self):
        self.assertIsNone(m.product_id(URL.replace("kham.com.tw", "example.invalid"), x.allowed))
    def test_07_extra_query(self):
        self.assertIsNone(m.product_id(URL + "&foo=bar", x.allowed))
    def test_08_duplicate_query(self):
        self.assertIsNone(m.product_id(URL + "&PRODUCT_ID=B123", x.allowed))
    def test_09_bad_path(self):
        self.assertIsNone(m.product_id(URL.replace("UTK0201_.aspx", "UTK0202_.aspx"), x.allowed))
    def test_10_fragment(self):
        self.assertIsNone(m.product_id(URL + "#frag", x.allowed))
    def test_11_invalid_id(self):
        self.assertIsNone(m.product_id(URL.replace("A123", "A-123"), x.allowed))
    def test_12_long_id(self):
        self.assertIsNone(m.product_id(URL.replace("A123", "A" * 33), x.allowed))
    def test_13_one_provisional(self):
        rows, d = candidates(link("測試音樂會"))
        self.assertEqual((len(rows), d["selected"], d["provisionalObjects"]), (1, 1, 1))
    def test_14_duplicate_product(self):
        rows, d = candidates(link() + link())
        self.assertEqual((len(rows), d["duplicateProductId"]), (1, 1))
    def test_15_noise_rejection(self):
        rows, d = candidates(link("立即購票"))
        self.assertEqual((len(rows), d["rejectedObjects"]), (0, 1))
    def test_16_offsite_link(self):
        rows, d = candidates(link(href="https://example.invalid/UTK0201_.aspx?PRODUCT_ID=A123"))
        self.assertEqual((len(rows), d["unsafeSelected"]), (0, 1))
    def test_17_missing_product_id(self):
        rows, d = candidates(link(href="/application/UTK02/UTK0201_.aspx?OTHER=A123"))
        self.assertEqual((len(rows), d["nonCanonical"]), (0, 1))
    def test_18_anchor_cap(self):
        with self.assertRaisesRegex(ValueError, "HOLD_LIST_ANCHOR_CAP"):
            candidates(link() * (m.MAX_ANCHORS + 1))
    def test_19_exact_heading(self):
        f = m.heading_state("<h1>測試音樂會</h1><h2>其他資訊</h2>", "complete", "測試音樂會")
        self.assertEqual((f["headingCandidates"], f["exactHeadingMatches"]), (2, 1))
    def test_20_no_substring(self):
        f = m.heading_state("<h1>測試音樂會 立即購票</h1>", "complete", "測試音樂會")
        self.assertEqual(f["exactHeadingMatches"], 0)
    def test_21_unicode_nfc(self):
        self.assertEqual(m.normalize_title("Cafe\u0301   音樂會"), "Café 音樂會")
    def test_22_stable_tail(self):
        self.assertEqual(m.classify_detail(detail()), "REVIEW_EXACT_SAME_ID_STABLE_H1H2")
    def test_23_not_complete(self):
        self.assertEqual(m.classify_detail(detail(frames=[frame(ready="interactive")] * 4)),
                         "HOLD_H1H2_NOT_STABLE")
    def test_24_detail_http(self):
        self.assertEqual(m.classify_detail(detail(http=403)), "HOLD_DETAIL_HTTP_NOT_200")
    def test_25_detail_offsite(self):
        self.assertEqual(m.classify_detail(detail(safe=False)), "HOLD_UNSAFE_DETAIL_FINAL")
    def test_26_detail_id_drift(self):
        self.assertEqual(m.classify_detail(detail(same=False)), "HOLD_DETAIL_PRODUCT_ID_DRIFT")
    def test_27_no_heading(self):
        self.assertEqual(m.classify_detail(detail(frames=[frame(headings=0, matches=0)] * 4)),
                         "HOLD_NO_H1H2_CANDIDATE")
    def test_28_wrong_heading(self):
        self.assertEqual(m.classify_detail(detail(frames=[frame(matches=0)] * 4)),
                         "HOLD_H1H2_TITLE_NONMATCH")
    def test_29_ambiguous_heading(self):
        self.assertEqual(m.classify_detail(detail(frames=[frame(matches=2)] * 4)),
                         "HOLD_AMBIGUOUS_HEADING")
    def test_30_incomplete_snapshots(self):
        self.assertEqual(m.classify_detail(detail(frames=[frame()])), "HOLD_INCOMPLETE_DETAIL_SNAPSHOTS")
    def test_31_review_two(self):
        self.assertEqual(m.decision(report()), "REVIEW_TWO_CURRENT_SAME_ID_TITLE_MATCHES_NO_FIELD_PROMOTION")
    def test_32_list_http_hold(self):
        self.assertEqual(m.decision(report(http=403)), "HOLD_LIST_HTTP_NOT_200")
    def test_33_list_offsite_hold(self):
        self.assertEqual(m.decision(report(safe=False)), "HOLD_UNSAFE_LIST_FINAL")
    def test_34_list_unsafe_hold(self):
        self.assertEqual(m.decision(report(unsafe=1)), "HOLD_LIST_UNSAFE_OR_NONCANONICAL")
    def test_35_insufficient_candidates(self):
        self.assertEqual(m.decision(report(count=1)), "HOLD_INSUFFICIENT_LIST_CANDIDATES")
    def test_36_detail_nonmatch_hold(self):
        self.assertEqual(m.decision(report(samples=[{"decision": "HOLD_H1H2_TITLE_NONMATCH"}] * 2)),
                         "HOLD_DETAIL_IDENTITY_OR_TITLE_PARITY")
    def test_37_parent_sha_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "HOLD_FORMAL_STATUS_SHA"):
            m.parent_check(b"{}", b"{}")
    def test_38_parent_report_sha_fail_closed(self):
        s, p = valid_parent()
        with patch.object(m, "git_blob", return_value=m.STATUS_BLOB):
            with self.assertRaisesRegex(ValueError, "HOLD_L9Y_PARENT_REPORT_SHA"):
                m.parent_check(s, p)
    def test_39_valid_parent_contract(self):
        s, p = valid_parent()
        with patch.object(m, "git_blob", return_value=m.STATUS_BLOB), \
             patch.object(m, "sha", return_value=m.PARENT_REPORT_SHA256):
            self.assertTrue(m.parent_check(s, p))
    def test_40_malformed_parent_fail_closed(self):
        s, _ = valid_parent()
        with patch.object(m, "git_blob", return_value=m.STATUS_BLOB), \
             patch.object(m, "sha", return_value=m.PARENT_REPORT_SHA256):
            with self.assertRaisesRegex(ValueError, "HOLD_MALFORMED_PARENT"):
                m.parent_check(s, b"{}")
    def test_41_no_publication_api(self):
        self.assertFalse(hasattr(m, "publish"))
        self.assertEqual(m.MAX_DETAILS, 2)
    def test_42_only_four_snapshots(self):
        self.assertEqual(m.SNAPSHOTS, 4)
    def test_43_unsafe_title_not_retained(self):
        rows, counts = candidates(link("測試私有標題"))
        self.assertEqual(len(rows), 1)
        self.assertNotIn("測試私有標題", json.dumps(counts, ensure_ascii=False))
    def test_44_list_missing(self):
        r = report()
        r["listCounts"] = None
        self.assertEqual(m.decision(r), "HOLD_LIST_PARSE_MISSING")
    def test_45_list_timeout_first_failure(self):
        r = report(safe=False, http=None)
        r.update(sourceException=True, sourceErrorKind="TIMEOUT")
        self.assertEqual(m.decision(r), "HOLD_LIST_SOURCE_TIMEOUT")
    def test_46_detail_network_first_failure(self):
        d = detail(safe=False, http=None)
        d.update(sourceException=True, sourceErrorKind="CONNECTION")
        self.assertEqual(m.classify_detail(d), "HOLD_DETAIL_SOURCE_CONNECTION")
    def test_47_error_dns_redacted(self):
        self.assertEqual(m.error_kind(Exception("net::ERR_NAME_NOT_RESOLVED at https://example.invalid/private")), "DNS")
    def test_48_error_timeout_redacted(self):
        self.assertEqual(m.error_kind(Exception("Timeout 18000ms exceeded; url=secret")), "TIMEOUT")
    def test_49_error_unknown_redacted(self):
        self.assertEqual(m.error_kind(Exception("unclassified detail error at secret")), "OTHER")

if __name__ == "__main__":
    unittest.main()

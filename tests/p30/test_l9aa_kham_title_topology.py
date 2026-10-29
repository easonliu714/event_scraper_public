#!/usr/bin/env python3
"""L9-AA offline contracts: strict source identity, bounded topology and no release."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import p30_l9aa_kham_title_topology as m

TITLE = "測試音樂會"
def snap(html="", ready="complete"):
    return m.region_snapshot(html, TITLE, ready)
def frame(ready="complete", visible=1, meta=0, overflow=False, iframe=0):
    counts = {k: 0 for k, *_ in m.ZONES}
    matches = counts.copy()
    matches["h3h6"] = visible
    matches["openGraph"] = meta
    return dict(ready=ready, candidateCounts=counts, exactMatches=matches,
                zoneOverflow=overflow, iframeCount=iframe, h1h2Count=0, mainScopeCount=0)
def sample(frames=None, **kw):
    d = dict(http=200, finalAllowed=True, sameProductId=True, frames=frames or [frame()] * 6,
             sourceException=False, sourceErrorKind="NONE")
    d.update(kw)
    return d
def report(samples=None, **kw):
    r = dict(listHttp=200, listFinalAllowed=True, listCounts={
        "unsafeSelected": 0, "nonCanonical": 0, "provisionalObjects": 10},
        samples=samples if samples is not None else [dict(decision="REVIEW_ONE_EXACT_VISIBLE_REGION_NO_IDENTITY_PROMOTION")] * 2,
        sourceException=False, sourceErrorKind="NONE")
    r.update(kw)
    return r

class Contracts(unittest.TestCase):
    def test_01_kind(self): self.assertEqual(m.KIND, "EVENTRADAR_P30_L9AA_KHAM_TITLE_TOPOLOGY_V1")
    def test_02_hold(self): self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_03_parent(self): self.assertEqual(m.PARENT, "18d9a28c4b3235a5aa7b722b447f7588a707911d")
    def test_04_bound(self): self.assertEqual((m.MAX_DETAILS, m.SNAPSHOTS), (2, 6))
    def test_05_title(self): self.assertEqual(snap("<title>測試音樂會</title>")["exactMatches"]["headTitle"], 1)
    def test_06_og_title(self): self.assertEqual(snap("<meta property='og:title' content='測試音樂會'>")["exactMatches"]["openGraph"], 1)
    def test_07_twitter(self): self.assertEqual(snap("<meta name='twitter:title' content='測試音樂會'>")["exactMatches"]["twitter"], 1)
    def test_08_h3(self): self.assertEqual(snap("<h3>測試音樂會</h3>")["exactMatches"]["h3h6"], 1)
    def test_09_h4(self): self.assertEqual(snap("<h4>測試音樂會</h4>")["exactMatches"]["h3h6"], 1)
    def test_10_h1_not_promoted(self): self.assertEqual(snap("<h1>測試音樂會</h1>")["exactMatches"]["h3h6"], 0)
    def test_11_scoped_title(self): self.assertEqual(snap("<main><span class='event-title'>測試音樂會</span></main>")["exactMatches"]["scopedTitle"], 1)
    def test_12_scoped_text(self): self.assertEqual(snap("<article><p>測試音樂會</p></article>")["exactMatches"]["scopedText"], 1)
    def test_13_unscoped_text(self): self.assertEqual(snap("<footer><p>測試音樂會</p></footer>")["exactMatches"]["scopedText"], 0)
    def test_14_semantic_name(self): self.assertEqual(snap("<main><b itemprop='name'>測試音樂會</b></main>")["exactMatches"]["semanticName"], 1)
    def test_15_img_alt_hint(self): self.assertEqual(snap("<main><img alt='測試音樂會'>")["exactMatches"]["scopedImageAlt"], 1)
    def test_16_substring_rejected(self): self.assertEqual(snap("<h3>測試音樂會 立即購票</h3>")["exactMatches"]["h3h6"], 0)
    def test_17_nfc(self): self.assertEqual(m.z.normalize_title("Cafe\u0301"), "Café")
    def test_18_missing_expected(self):
        with self.assertRaisesRegex(ValueError, "HOLD_EMPTY_EXPECTED_TITLE"): m.region_snapshot("<h3>x</h3>", "", "complete")
    def test_19_html_cap(self):
        with self.assertRaisesRegex(ValueError, "HOLD_HTML_SIZE"): m.region_snapshot("a" * (m.MAX_BYTES + 1), TITLE, "complete")
    def test_20_region_cap(self):
        f = snap("<main>" + "<p>noise</p>" * (m.MAX_ZONE_NODES + 1) + "</main>")
        self.assertTrue(f["zoneOverflow"])
    def test_21_no_raw_title(self):
        f = snap("<h3>測試音樂會</h3>")
        self.assertNotIn(TITLE, json.dumps(f, ensure_ascii=False))
    def test_22_review_visible(self): self.assertEqual(m.classify(sample()), "REVIEW_ONE_EXACT_VISIBLE_REGION_NO_IDENTITY_PROMOTION")
    def test_23_metadata_only(self): self.assertEqual(m.classify(sample(frames=[frame(visible=0, meta=1)] * 6)), "HOLD_METADATA_OR_IMAGE_ONLY")
    def test_24_not_complete(self): self.assertEqual(m.classify(sample(frames=[frame(ready="interactive")] * 6)), "HOLD_RENDER_NOT_COMPLETE")
    def test_25_no_region(self): self.assertEqual(m.classify(sample(frames=[frame(visible=0)] * 6)), "HOLD_NO_EXACT_TITLE_REGION")
    def test_26_iframe(self): self.assertEqual(m.classify(sample(frames=[frame(visible=0, iframe=1)] * 6)), "HOLD_NO_EXACT_REGION_IFRAME_PRESENT")
    def test_27_multiple(self): self.assertEqual(m.classify(sample(frames=[frame(visible=2)] * 6)), "HOLD_MULTIPLE_EXACT_VISIBLE_REGIONS")
    def test_28_overflow(self): self.assertEqual(m.classify(sample(frames=[frame(overflow=True)] * 6)), "HOLD_REGION_CAP")
    def test_29_http(self): self.assertEqual(m.classify(sample(http=403)), "HOLD_DETAIL_HTTP_NOT_200")
    def test_30_offsite(self): self.assertEqual(m.classify(sample(finalAllowed=False)), "HOLD_UNSAFE_DETAIL_FINAL")
    def test_31_id_drift(self): self.assertEqual(m.classify(sample(sameProductId=False)), "HOLD_DETAIL_PRODUCT_ID_DRIFT")
    def test_32_timeout(self): self.assertEqual(m.classify(sample(sourceException=True, sourceErrorKind="TIMEOUT")), "HOLD_DETAIL_SOURCE_TIMEOUT")
    def test_33_missing_frames(self): self.assertEqual(m.classify(sample(frames=[frame()] * 5)), "HOLD_INCOMPLETE_SNAPSHOTS")
    def test_34_report_review(self): self.assertEqual(m.decide(report()), "REVIEW_TWO_REGION_MATCHES_NO_FORMAL_PROMOTION")
    def test_35_report_one_hold(self): self.assertEqual(m.decide(report(samples=[{"decision":"HOLD_NO_EXACT_TITLE_REGION"}]*2)), "HOLD_TITLE_REGION_TOPOLOGY_UNRESOLVED")
    def test_36_report_list_http(self): self.assertEqual(m.decide(report(listHttp=403)), "HOLD_LIST_HTTP_NOT_200")
    def test_37_report_list_exception(self): self.assertEqual(m.decide(report(sourceException=True,sourceErrorKind="DNS")), "HOLD_LIST_SOURCE_DNS")
    def test_38_report_list_unsafe(self): self.assertEqual(m.decide(report(listFinalAllowed=False)), "HOLD_UNSAFE_LIST_FINAL")
    def test_39_report_list_count(self): self.assertEqual(m.decide(report(listCounts={"unsafeSelected":0,"nonCanonical":0,"provisionalObjects":1})), "HOLD_LIST_IDENTITY_OR_COUNT")
    def test_40_report_unsafe_candidate(self): self.assertEqual(m.decide(report(listCounts={"unsafeSelected":1,"nonCanonical":0,"provisionalObjects":10})), "HOLD_LIST_IDENTITY_OR_COUNT")
    def test_41_no_publish(self): self.assertFalse(hasattr(m,"publish"))
    def test_42_parent_sha(self):
        with self.assertRaisesRegex(ValueError, "HOLD_FORMAL_STATUS_SHA"): m.verify_parent(b"{}",b"{}",b"{}")
    def test_43_source_sha(self):
        with patch.object(m.z,"git_blob",side_effect=[m.STATUS_BLOB,"wrong"]):
            with self.assertRaisesRegex(ValueError,"HOLD_FROZEN_SOURCE_SHA"): m.verify_parent(b"{}",b"{}",b"{}")
    def test_44_parent_report_sha(self):
        with patch.object(m.z,"git_blob",side_effect=[m.STATUS_BLOB,m.SOURCE_BLOB]):
            with self.assertRaisesRegex(ValueError,"HOLD_L9Z_PARENT_REPORT_SHA"): m.verify_parent(b"{}",b"{}",b"{}")
    def test_45_allowed_source(self): self.assertFalse(m.x.allowed("https://example.invalid/"))
    def test_46_exact_id(self): self.assertIsNone(m.z.product_id("https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=X&EXTRA=Y",m.x.allowed))
    def test_47_no_global_body_scan(self):
        f=snap("<body><div>測試音樂會</div></body>")
        self.assertEqual(sum(f["exactMatches"].values()),0)
    def test_48_iframe_count(self): self.assertEqual(snap("<iframe></iframe>")["iframeCount"],1)

if __name__ == "__main__":
    unittest.main()

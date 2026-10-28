#!/usr/bin/env python3
"""P30-L9-Y offline fail-closed tests; never request a live source."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("l9y", ROOT / "scripts/p30_l9y_kham_event_object_boundary.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
spec_x = importlib.util.spec_from_file_location("l9x", ROOT / "scripts/p30_l9x_kham_original_parser_parity.py")
x = importlib.util.module_from_spec(spec_x)
spec_x.loader.exec_module(x)
F = m.frozen_functions((ROOT / "scraper.py").read_bytes())

def h(title="測試音樂會", pid="A123", href=None):
    link = href if href is not None else "/application/UTK02/UTK0201_.aspx?PRODUCT_ID=" + pid
    return '<a href="' + link + '">' + title + '</a>'

def stage(html):
    return m.stages(html.encode("utf-8"), F, x.allowed)

def probe(http=200, safe=True, static=None, rendered=None):
    base = stage(h())
    return {"http": http, "finalAllowed": safe,
            "static": base if static is None else static,
            "rendered": base if rendered is None else rendered}

class Contract(unittest.TestCase):
    def test_01_kind(self): self.assertEqual(m.KIND, "EVENTRADAR_P30_L9Y_KHAM_EVENT_OBJECT_BOUNDARY_V1")
    def test_02_hold(self): self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_03_parent(self): self.assertEqual(m.PARENT, "b90a6af4f6bb2bab4a6570a025e7068cd1c69093")
    def test_04_source_blob(self): self.assertEqual(m.git_blob((ROOT / "scraper.py").read_bytes()), m.SOURCE_BLOB)
    def test_05_ast_no_module_execution(self): self.assertTrue(callable(F["create_event_obj"]))
    def test_06_missing_frozen_sha(self):
        with self.assertRaisesRegex(ValueError, "HOLD_FROZEN_SCRAPER_SHA"):
            m.frozen_functions(b"def create_event_obj(): pass")
    def test_07_exact_provisional(self):
        d=stage(h()); self.assertEqual((d["selected"],d["productGate"],d["acceptedObjects"]),(1,1,1))
    def test_08_noise_exact_rejected(self):
        d=stage(h("立即購票")); self.assertEqual((d["rejectedObjects"],d["exactNoiseRejected"]),(1,1))
    def test_09_short_rejected(self):
        d=stage(h("A")); self.assertEqual((d["rejectedObjects"],d["shortOrNumericRejected"]),(1,1))
    def test_10_numeric_rejected(self):
        d=stage(h("12345")); self.assertEqual((d["rejectedObjects"],d["shortOrNumericRejected"]),(1,1))
    def test_11_empty_rejected(self):
        d=stage(h("")); self.assertEqual((d["emptyRawTitle"],d["rejectedObjects"]),(1,1))
    def test_12_normalization(self):
        d=stage(h("2026-01-01 測試音樂會")); self.assertEqual((d["acceptedObjects"],d["normalizedTitle"]),(1,1))
    def test_13_noise_substring(self):
        d=stage(h("演唱會立即購票")); self.assertEqual((d["acceptedObjects"],d["normalizedTitle"]),(1,1))
    def test_14_duplicate_accepted(self):
        d=stage(h()+h()); self.assertEqual((d["acceptedObjects"],d["duplicateAfterAccepted"]),(1,1))
    def test_15_rejected_not_seen(self):
        d=stage(h("立即購票")+h("測試音樂會")); self.assertEqual((d["rejectedObjects"],d["acceptedObjects"],d["duplicateAfterAccepted"]),(1,1,0))
    def test_16_missing_product_id(self):
        d=stage(h(href="/UTK0201_.aspx?X=1")); self.assertEqual((d["selected"],d["productGate"]),(1,0))
    def test_17_selector_case(self):
        d=stage(h(href="/utk0201_.aspx?PRODUCT_ID=A")); self.assertEqual(d["selected"],0)
    def test_18_offsite(self):
        d=stage(h(href="https://example.invalid/UTK0201_.aspx?PRODUCT_ID=A")); self.assertEqual(d["unsafeLinks"],1)
    def test_19_anchor_cap(self):
        with self.assertRaisesRegex(ValueError,"HOLD_ANCHOR_CAP"):
            stage(h()* (m.MAX_ANCHORS+1))
    def test_20_url_normalized(self):
        self.assertEqual(F["fix_utk_url"]("kham.com.tw","https://kham.com.tw/UTK0201_.aspx?PRODUCT_ID=ABC"),
                         "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=ABC")
    def test_21_review_provisional(self):
        self.assertEqual(m.decide(probe()),"REVIEW_CURRENT_PROVISIONAL_OBJECTS_HISTORIC_ZERO")
    def test_22_review_mixed(self):
        d=stage(h("立即購票")+h("測試音樂會",pid="B"))
        self.assertEqual(m.decide(probe(static=d,rendered=d)),"REVIEW_CURRENT_MIXED_OBJECT_FILTERING")
    def test_23_review_post_zero(self):
        d=stage(h("立即購票"))
        self.assertEqual(m.decide(probe(static=d,rendered=d)),"REVIEW_CURRENT_POST_OBJECT_ZERO")
    def test_24_http_hold(self): self.assertEqual(m.decide(probe(http=403)),"HOLD_HTTP_NOT_200")
    def test_25_unsafe_final(self): self.assertEqual(m.decide(probe(safe=False)),"HOLD_UNSAFE_FINAL")
    def test_26_unsafe_links(self):
        d=stage(h(href="https://example.invalid/UTK0201_.aspx?PRODUCT_ID=A"))
        self.assertEqual(m.decide(probe(static=d,rendered=d)),"HOLD_UNSAFE_LINKS")
    def test_27_missing_static(self):
        p=probe();p["static"]=None
        self.assertEqual(m.decide(p),"HOLD_INCOMPLETE_SOURCE")
    def test_28_missing_rendered(self):
        p=probe();p["rendered"]=None
        self.assertEqual(m.decide(p),"HOLD_INCOMPLETE_SOURCE")
    def test_29_parent_status_bad(self):
        with self.assertRaisesRegex(ValueError,"HOLD_FORMAL_STATUS_SHA"):
            m.parent_check(b"{}",b"{}")
    def test_30_parent_kind_bad(self):
        from unittest.mock import patch
        with patch.object(m,"git_blob",return_value=m.STATUS_BLOB):
            status={"production":{"eventFeedReleaseState":m.RELEASE,"goldenAccepted":0}}
            with self.assertRaisesRegex(ValueError,"HOLD_PARENT_KIND"):
                m.parent_check(json.dumps(status).encode(),b"{}")
    def test_31_no_date_field(self):
        self.assertNotIn("date",stage(h()))
    def test_32_no_title_persisted(self):
        self.assertNotIn("title",json.dumps(stage(h("私有測試標題"))))
    def test_33_accounting(self):
        d=stage(h("立即購票")+h("音樂會",pid="B"))
        self.assertEqual(d["preObject"],d["acceptedObjects"]+d["rejectedObjects"])
    def test_34_safe_source(self):
        self.assertTrue(x.allowed(x.ENTRY))
    def test_35_no_live_in_tests(self):
        self.assertEqual(m.MAX_BYTES,1500000)
    def test_36_no_publisher(self):
        self.assertFalse(hasattr(m,"publish"))
    def test_37_exact_noise(self):
        self.assertEqual(stage(h("報名"))["exactNoiseRejected"],1)
    def test_38_banner_normalized(self):
        self.assertEqual(stage(h("banner-演唱會"))["normalizedTitle"],1)

if __name__ == "__main__":
    unittest.main()

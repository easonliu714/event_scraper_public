#!/usr/bin/env python3
"""P30-L9-X offline fail-closed contracts. No network or browser."""
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

source = Path(__file__).resolve().parents[2] / "scripts/p30_l9x_kham_original_parser_parity.py"
spec = importlib.util.spec_from_file_location("l9x", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def html(href="/application/UTK02/UTK0201_.aspx?PRODUCT_ID=AB12", text="測試活動"):
    return ('<html><a href="' + href + '">' + text + '</a></html>').encode()

def frame(count=1, ready="complete"):
    return {"ready": ready, "stages": {"originalSelector": count}}

def decide(data=None, frames=None, http=200, allowed=True):
    return m.decide(http, allowed, data if data is not None else m.stages(html()),
                    frames if frames is not None else [frame(), frame(), frame()])

class Contracts(unittest.TestCase):
    def test_01_kind(self): self.assertEqual(m.KIND, "EVENTRADAR_P30_L9X_KHAM_ORIGINAL_PARSER_PARITY_V1")
    def test_02_release(self): self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_03_entry(self): self.assertTrue(m.allowed(m.ENTRY))
    def test_04_bad_http(self): self.assertFalse(m.allowed("http://kham.com.tw/"))
    def test_05_bad_host(self): self.assertFalse(m.allowed("https://kham.com.tw.evil.test/"))
    def test_06_bad_creds(self): self.assertFalse(m.allowed("https://a:b@kham.com.tw/"))
    def test_07_bad_port(self): self.assertFalse(m.allowed("https://kham.com.tw:444/"))
    def test_08_bad_scheme(self): self.assertFalse(m.allowed("javascript:alert(1)"))
    def test_09_bad_url(self): self.assertFalse(m.allowed("not a url"))
    def test_10_exact_selector(self):
        d = m.stages(html())
        self.assertEqual((d["originalSelector"], d["passedProductIdGate"], d["titleTextNonempty"]), (1, 1, 1))
    def test_11_url_pattern_no_underscore(self):
        d = m.stages(html("/UTK0201.aspx?PRODUCT_ID=A"))
        self.assertEqual((d["broadUtkLinks"], d["originalSelector"]), (1, 0))
    def test_12_product_id_missing(self):
        d = m.stages(html("/application/UTK02/UTK0201_.aspx?X=1"))
        self.assertEqual((d["originalSelector"], d["missingProductId"], d["passedProductIdGate"]), (1, 1, 0))
    def test_13_lowercase_selector_fail(self):
        d = m.stages(html("/application/UTK02/utk0201_.aspx?PRODUCT_ID=A"))
        self.assertEqual((d["broadUtkLinks"], d["originalSelector"]), (1, 0))
    def test_14_lowercase_product_id_normalized(self):
        d = m.stages(html("/application/UTK02/UTK0201_.aspx?product_id=A"))
        self.assertEqual(d["passedProductIdGate"], 1)
    def test_15_empty_title(self):
        d = m.stages(html(text=""))
        self.assertEqual((d["passedProductIdGate"], d["titleTextEmpty"]), (1, 1))
    def test_16_alt_is_not_original_anchor_text(self):
        d = m.stages('<a href="/UTK0201_.aspx?PRODUCT_ID=A"><img alt="活動名稱"></a>'.encode())
        self.assertEqual((d["imageAltPresent"], d["titleTextEmpty"]), (1, 1))
    def test_17_title_attr_not_original_anchor_text(self):
        d = m.stages('<a title="活動" href="/UTK0201_.aspx?PRODUCT_ID=A"></a>'.encode())
        self.assertEqual((d["titleAttributePresent"], d["titleTextEmpty"]), (1, 1))
    def test_18_duplicate(self):
        d = m.stages(html() + html())
        self.assertEqual((d["originalSelector"], d["uniqueAfterGate"], d["duplicateAfterGate"]), (2, 1, 1))
    def test_19_offsite(self):
        d = m.stages(html("https://evil.test/UTK0201_.aspx?PRODUCT_ID=A"))
        self.assertEqual((d["offsiteSelected"], d["passedProductIdGate"]), (1, 0))
    def test_20_cap(self):
        with self.assertRaisesRegex(ValueError, "HOLD_ANCHOR_CAP"):
            m.stages(("<a href='/'>x</a>" * (m.MAX_ANCHORS + 1)).encode())
    def test_21_selector_zero_review(self):
        self.assertEqual(decide(m.stages(html("/UTK0201.aspx?PRODUCT_ID=A"))), "REVIEW_CURRENT_ORIGINAL_SELECTOR_ZERO")
    def test_22_product_gate_review(self):
        self.assertEqual(decide(m.stages(html("/UTK0201_.aspx?X=1"))), "REVIEW_CURRENT_ORIGINAL_PRODUCT_ID_GATE_ZERO")
    def test_23_text_gate_review(self):
        self.assertEqual(decide(m.stages(html(text=""))), "REVIEW_CURRENT_ORIGINAL_ANCHOR_TEXT_ZERO")
    def test_24_pre_event_only(self):
        self.assertEqual(decide(), "REVIEW_CURRENT_PRE_EVENT_CANDIDATES_HISTORIC_ZERO")
    def test_25_http_403_hold(self):
        self.assertEqual(decide(http=403), "HOLD_HTTP_NOT_200")
    def test_26_unsafe_final_hold(self):
        self.assertEqual(decide(allowed=False), "HOLD_UNSAFE_FINAL")
    def test_27_missing_static_hold(self):
        self.assertEqual(decide(data=None, frames=[frame(),frame()]), "HOLD_INCOMPLETE_SOURCE")
    def test_28_incomplete_ready_hold(self):
        self.assertEqual(decide(frames=[frame(),frame(),frame(ready="interactive")]), "HOLD_RENDER_NOT_COMPLETE")
    def test_29_unstable_selector_hold(self):
        self.assertEqual(decide(frames=[frame(),frame(2),frame()]), "HOLD_RENDER_SELECTOR_UNSTABLE")
    def test_30_no_source_hold(self):
        self.assertEqual(decide(m.stages(b'<html></html>')), "HOLD_NO_CURRENT_SOURCE_CANDIDATES")
    def test_31_sha(self):
        self.assertEqual(m.sha(b"test"), hashlib.sha256(b"test").hexdigest())
    def test_32_blob(self):
        b=b"test"
        self.assertEqual(m.git_blob(b), "30d74d258442c7c65512eafab474568dd706c430")
    def test_33_status_bad(self):
        with self.assertRaisesRegex(ValueError, "HOLD_STATUS_BLOB"):
            m.verify_parents(b"{}", b"{}", b"{}")
    def test_34_fixed_url(self):
        self.assertEqual(m.fix_utk_url("kham.com.tw", "https://kham.com.tw/UTK0201_.aspx?PRODUCT_ID=XYZ"),
                         "https://kham.com.tw/application/UTK02/UTK0201_.aspx?PRODUCT_ID=XYZ")
    def test_35_not_date_regex(self):
        self.assertNotIn("date", m.stages(html()))
    def test_36_source_only(self):
        self.assertEqual(m.PARENT, "9bc37d326ee6e1b698e36061f8323e0894c98ad6")

if __name__ == "__main__":
    unittest.main()

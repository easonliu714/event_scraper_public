#!/usr/bin/env python3
"""Fail-closed FamiTicket iframe detail contract; no official GET in CI."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9aq_famiticket_iframe_boundary import classify_detail

URL = "https://www.famiticket.com.tw/Home/Activity/Info/MABvAE4ALwBxAEkAcQB3ADkAawB0AHUASgBlAGwAZwA3AGkAOQBsAEwAQwBkAHgAKwBFADUAUABOAHMAcgA5AGYAZgBTAGgATQA3ADAAUAAvAEwAOAA9AA2"
TITLE = "臺中市立美術館 蠍子與青蛙"

class FrameBoundaryTests(unittest.TestCase):
    def check(self, html, expected):
        r = classify_detail(html.encode(), TITLE, URL)
        self.assertEqual(r["decision"], expected)
        self.assertEqual(r["acceptedFields"], 0)
        self.assertEqual(r["goldenAccepted"], 0)
        self.assertFalse(r["published"])
        self.assertFalse(r["iframeFollowed"])
        self.assertEqual(r["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        return r
    def test_iframe_only(self):
        r = self.check('<html><iframe src="/Home/Activity/Embedded/123"></iframe></html>',
                       "HOLD_IFRAME_ONLY_NO_TITLE_IDENTITY")
        self.assertEqual((r["iframeCount"], r["iframeSameOriginCount"]), (1, 1))
    def test_external_frame_not_followed(self):
        r = self.check('<iframe src="https://elsewhere.example/x"></iframe>',
                       "HOLD_IFRAME_ONLY_NO_TITLE_IDENTITY")
        self.assertEqual(r["iframeSameOriginCount"], 0)
    def test_heading_and_iframe_still_hold(self):
        self.check(f'<h1>{TITLE}</h1><iframe src="/Home/Activity/Info/other"></iframe>',
                   "HOLD_IFRAME_PRESENT_EVEN_WITH_HEADING")
    def test_one_heading_only_review(self):
        self.check(f'<h1>{TITLE}</h1>', "REVIEW_EXACT_HEADING_ONLY_NO_FIELDS")
    def test_duplicate_heading_hold(self):
        self.check(f'<h1>{TITLE}</h1><h2>{TITLE}</h2>', "HOLD_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_other_heading_hold(self):
        self.check("<h1>不同活動</h1>", "HOLD_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_oversize_hold(self):
        r = classify_detail(b"x" * 800001, TITLE, URL)
        self.assertEqual(r["decision"], "HOLD_INPUT")
    def test_untrusted_url_hold(self):
        r = classify_detail(b"<h1>Test</h1>", TITLE, "http://evil.example/anything")
        self.assertEqual(r["decision"], "HOLD_INPUT")
    def test_frame_cap_hold(self):
        self.check("<iframe></iframe>" * 4, "HOLD_IFRAME_CAP")
    def test_empty_title_hold(self):
        r = classify_detail(b"<h1>Test</h1>", "", URL)
        self.assertEqual(r["decision"], "HOLD_INPUT")

if __name__ == "__main__":
    unittest.main()

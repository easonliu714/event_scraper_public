#!/usr/bin/env python3
"""Offline positive/negative FamiTicket HTML identity and release locks."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9as_famiticket_live_dom import inspect_html, URL, TITLE

GOOD = '<html><body><section><h4>CC同人創作展</h4><img alt="《活動資訊》"><p>2026.11.21-22</p><p>活動時間│10:30-16:00</p><p>活動票價│單日票200元</p></section></body></html>'
class LiveDomTests(unittest.TestCase):
    def check(self, html, decision, url=URL, title=TITLE):
        r = inspect_html(html, url, title)
        self.assertEqual(r["decision"], decision)
        self.assertEqual((r["acceptedFields"], r["goldenAccepted"], r["published"]), (0,0,False))
        self.assertEqual(r["releaseState"], "HARD_HOLD_NO_PUBLICATION")
        self.assertIsNone(r["ticketEventId"])
        self.assertFalse(r["eventDateAccepted"])
        return r
    def test_one_visible_heading_and_marker(self):
        r=self.check(GOOD, "REVIEW_LIVE_HTML_TITLE_AND_INFO_MARKER_NO_FIELD_ACCEPTANCE")
        self.assertEqual((r["headingMatches"],r["infoMarkers"]), (1,1))
    def test_iframe_only(self):
        self.check('<iframe src="/embed"></iframe>', "HOLD_IFRAME_ONLY_NO_TITLE")
    def test_missing_title(self):
        self.check('<h4>其他活動</h4><img alt="《活動資訊》">', "HOLD_NO_EXACT_TITLE")
    def test_wrong_expected_title(self):
        self.check(GOOD, "HOLD_NO_EXACT_TITLE", title="其他活動")
    def test_duplicate_heading(self):
        self.check(GOOD.replace('</section>', '<h2>CC同人創作展</h2></section>'),
                   "HOLD_DUPLICATE_EXACT_TITLE")
    def test_hidden_heading(self):
        self.check('<div style="display:none"><h4>CC同人創作展</h4></div><img alt="《活動資訊》">',
                   "HOLD_HIDDEN_TITLE")
    def test_aria_hidden(self):
        self.check('<div aria-hidden="true"><h4>CC同人創作展</h4></div><img alt="《活動資訊》">',
                   "HOLD_HIDDEN_TITLE")
    def test_no_marker(self):
        self.check('<h4>CC同人創作展</h4>', "HOLD_NO_VISIBLE_INFO_MARKER")
    def test_two_markers(self):
        self.check(GOOD.replace('</section>', '<b>《活動資訊》</b></section>'),
                   "HOLD_AMBIGUOUS_INFO_MARKERS")
    def test_hidden_marker(self):
        self.check('<h4>CC同人創作展</h4><div hidden><img alt="《活動資訊》"></div>',
                   "HOLD_NO_VISIBLE_INFO_MARKER")
    def test_external_url(self):
        self.check(GOOD, "HOLD_INPUT", url="https://evil.example/Home/Activity/Info/abc")
    def test_byte_cap(self):
        self.check(GOOD + "x"*220001, "HOLD_INPUT")
    def test_query_refused(self):
        self.check(GOOD, "HOLD_INPUT", url=URL+"?ref=other")
if __name__ == "__main__":
    unittest.main()

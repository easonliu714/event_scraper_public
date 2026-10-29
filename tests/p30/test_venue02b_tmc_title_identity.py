"""P30-VENUE-02B strict source-bound identity and negative tests, no network."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_venue02b_tmc_title_identity as m

URL = "https://www.tmc.taipei/tw/blog/show/ExampleEvent2026"
LIST = b'<main><a href="/tw/blog/show/ExampleEvent2026">Example title</a></main>'
DETAIL = b'<main><h1>Example title</h1><h3>Schedule</h3></main>'

class TitleContract(unittest.TestCase):
    def test_01_exact_list(self):
        r, target, title = m.candidate_title(LIST, 200, m.prior.LIST_URL, False)
        self.assertTrue(r["decision"].startswith("REVIEW_"))
        self.assertEqual((target, title), (URL, "Example title"))

    def test_02_exact_detail(self):
        r = m.assess_exact_detail(DETAIL, 200, URL, URL, False, "Example title")
        self.assertEqual(r["exactTitleMatches"], 1)
        self.assertTrue(r["decision"].startswith("REVIEW_"))

    def test_03_title_mismatch(self):
        r = m.assess_exact_detail(DETAIL, 200, URL, URL, False, "Other title")
        self.assertEqual(r["decision"], "HOLD_LIST_DETAIL_TITLE_MISMATCH")

    def test_04_heading_h3_not_accepted(self):
        r = m.assess_exact_detail(b'<h3>Example title</h3>', 200, URL, URL, False, "Example title")
        self.assertTrue(r["decision"].startswith("HOLD_"))

    def test_05_hidden_heading_not_accepted(self):
        body = b'<main hidden><h1>Example title</h1></main><h2>Other title</h2>'
        r = m.assess_exact_detail(body, 200, URL, URL, False, "Example title")
        self.assertEqual(r["decision"], "HOLD_LIST_DETAIL_TITLE_MISMATCH")

    def test_06_aria_hidden_heading_not_accepted(self):
        body = b'<div aria-hidden="true"><h1>Example title</h1></div><h2>Other title</h2>'
        r = m.assess_exact_detail(body, 200, URL, URL, False, "Example title")
        self.assertEqual(r["decision"], "HOLD_LIST_DETAIL_TITLE_MISMATCH")

    def test_07_duplicate_exact_heading_refused(self):
        r = m.assess_exact_detail(b'<h1>Example title</h1><h2>Example title</h2>',
                                  200, URL, URL, False, "Example title")
        self.assertEqual(r["decision"], "HOLD_MULTIPLE_EXACT_HEADINGS")

    def test_08_redirect_refused(self):
        r = m.assess_exact_detail(DETAIL, 200, URL, URL, True, "Example title")
        self.assertEqual(r["decision"], "HOLD_DETAIL_URL_OR_REDIRECT")

    def test_09_other_url_refused(self):
        r = m.assess_exact_detail(DETAIL, 200, URL + "2", URL, False, "Example title")
        self.assertEqual(r["decision"], "HOLD_DETAIL_URL_OR_REDIRECT")

    def test_10_http403_refused(self):
        r = m.assess_exact_detail(DETAIL, 403, URL, URL, False, "Example title")
        self.assertEqual(r["decision"], "HOLD_DETAIL_HTTP_OR_CAP")

    def test_11_ambiguous_list_title_refused(self):
        body = (b'<a href="/tw/blog/show/ExampleEvent2026">Example title</a>'
                b'<a href="/tw/blog/show/ExampleEvent2026">Different title</a>')
        r, target, title = m.candidate_title(body, 200, m.prior.LIST_URL, False)
        self.assertEqual(r["decision"], "HOLD_LIST_TITLE_AMBIGUOUS")
        self.assertIsNone(target)
        self.assertIsNone(title)

    def test_12_generic_list_title_refused(self):
        body = b'<a href="/tw/blog/show/ExampleEvent2026">More</a>'
        r, target, title = m.candidate_title(body, 200, m.prior.LIST_URL, False)
        self.assertEqual(r["decision"], "HOLD_LIST_TITLE_GENERIC_OR_CAP")

    def test_13_external_link_refused(self):
        body = b'<a href="https://evil.example/tw/blog/show/ExampleEvent2026">Example title</a>'
        r, target, title = m.candidate_title(body, 200, m.prior.LIST_URL, False)
        self.assertEqual(r["decision"], "HOLD_NO_OFFICIAL_DETAIL_LINK")

    def test_14_nfc_whitespace_exact(self):
        body = '<h1>Cafe\u0301  live</h1>'.encode("utf-8")
        r = m.assess_exact_detail(body, 200, URL, URL, False, "Caf\u00e9 live")
        self.assertEqual(r["exactTitleMatches"], 1)

    def test_15_title_cap(self):
        r = m.assess_exact_detail(DETAIL, 200, URL, URL, False, "X" * 181)
        self.assertEqual(r["decision"], "HOLD_LIST_TITLE_INVALID")

    def test_16_single_list_single_detail(self):
        with patch.object(m.prior, "get_once", side_effect=[
            (LIST, 200, m.prior.LIST_URL, False),
            (DETAIL, 200, URL, False)]) as getter:
            r = m.probe()
        self.assertEqual(getter.call_count, 2)
        self.assertTrue(r["decision"].startswith("REVIEW_"))
        self.assertEqual(r["acceptedFields"], 0)
        self.assertFalse(r["published"])
        self.assertIsNone(r["ticketEventId"])

    def test_17_no_detail_if_list_hold(self):
        with patch.object(m.prior, "get_once",
                          return_value=(None, 403, m.prior.LIST_URL, False)) as getter:
            r = m.probe()
        self.assertEqual(getter.call_count, 1)
        self.assertTrue(r["decision"].startswith("HOLD_"))

    def test_18_release_locked(self):
        self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
        self.assertEqual(m.probe.__name__, "probe")

if __name__ == "__main__":
    unittest.main()

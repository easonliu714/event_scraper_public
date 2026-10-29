"""VENUE-02C card-local heading and fail-closed identity regression."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_venue02c_tmc_card_heading as m

URL = "https://www.tmc.taipei/tw/blog/show/ExampleEvent2026"
CARD = b'<main><a href="/tw/blog/show/ExampleEvent2026"><span>Concert</span><h3>Example title</h3><time>2026-11-07</time><span>Hall</span></a></main>'
DETAIL = b'<main><h2>Example title</h2><h3>Schedule</h3></main>'

class CardHeadingTests(unittest.TestCase):
    def parse(self, body):
        return m.candidate_card_heading(body, 200, m.prior.prior.LIST_URL, False)

    def test_01_full_card_not_title(self):
        old, target, title = m.prior.candidate_title(CARD, 200, m.prior.prior.LIST_URL, False)
        self.assertNotEqual(title, "Example title")
        self.assertEqual(target, URL)

    def test_02_one_inner_heading(self):
        result, target, title = self.parse(CARD)
        self.assertTrue(result["decision"].startswith("REVIEW_"))
        self.assertEqual((target, title), (URL, "Example title"))

    def test_03_heading_detail_same_title(self):
        result, target, title = self.parse(CARD)
        detail = m.prior.assess_exact_detail(DETAIL, 200, URL, target, False, title)
        self.assertEqual(detail["exactTitleMatches"], 1)
        self.assertTrue(detail["decision"].startswith("REVIEW_"))

    def test_04_missing_card_heading_refused(self):
        body = CARD.replace(b"<h3>Example title</h3>", b"<span>Example title</span>")
        self.assertEqual(self.parse(body)[0]["decision"], "HOLD_CARD_HEADING_ABSENT_OR_AMBIGUOUS")

    def test_05_two_card_headings_refused(self):
        body = CARD.replace(b"</h3>", b"</h3><h4>Other</h4>")
        self.assertEqual(self.parse(body)[0]["decision"], "HOLD_CARD_HEADING_ABSENT_OR_AMBIGUOUS")

    def test_06_hidden_card_heading_refused(self):
        body = CARD.replace(b"<h3>", b"<h3 hidden>")
        self.assertTrue(self.parse(body)[0]["decision"].startswith("HOLD_"))

    def test_07_hidden_card_refused(self):
        body = CARD.replace(b"<a href=", b"<a hidden href=")
        self.assertEqual(self.parse(body)[0]["decision"], "HOLD_CARD_HIDDEN")

    def test_08_conflicting_titles_refused(self):
        body = CARD + CARD.replace(b"Example title", b"Different title")
        self.assertEqual(self.parse(body)[0]["decision"], "HOLD_CARD_TITLE_CONFLICT_OR_ABSENT")

    def test_09_other_host_refused(self):
        body = CARD.replace(b'/tw/blog/show/ExampleEvent2026', b'https://example.org/tw/blog/show/ExampleEvent2026')
        self.assertTrue(self.parse(body)[0]["decision"].startswith("HOLD_"))

    def test_10_bad_http_refused(self):
        result, target, title = m.candidate_card_heading(CARD, 403, m.prior.prior.LIST_URL, False)
        self.assertIsNone(target)
        self.assertTrue(result["decision"].startswith("HOLD_"))

    def test_11_two_get_cap_and_release_hold(self):
        with patch.object(m.prior.prior, "get_once", side_effect=[
            (CARD, 200, m.prior.prior.LIST_URL, False),
            (DETAIL, 200, URL, False)]) as getter:
            report = m.probe()
        self.assertEqual(getter.call_count, 2)
        self.assertTrue(report["decision"].startswith("REVIEW_"))
        self.assertEqual(report["acceptedFields"], 0)
        self.assertEqual(report["goldenAccepted"], 0)
        self.assertFalse(report["published"])
        self.assertIsNone(report["ticketEventId"])

    def test_12_no_detail_if_list_hold(self):
        with patch.object(m.prior.prior, "get_once", return_value=(None, 403, m.prior.prior.LIST_URL, False)) as getter:
            report = m.probe()
        self.assertEqual(getter.call_count, 1)
        self.assertTrue(report["decision"].startswith("HOLD_"))

    def test_13_no_date_regex(self):
        self.assertEqual(self.parse(CARD.replace(b"<h3>Example title</h3>", b"<span>2026-11-07</span>"))[0]["decision"],
                         "HOLD_CARD_HEADING_ABSENT_OR_AMBIGUOUS")

if __name__ == "__main__":
    unittest.main()

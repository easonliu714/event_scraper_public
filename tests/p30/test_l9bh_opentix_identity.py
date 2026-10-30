#!/usr/bin/env python3
"""P30-L9-BH strict OPENTIX source-derived event identity/role tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from p30_l9bh_opentix_identity import safe_event, label_title, index_edges, inspect_detail

GOOD = "/event/2073011844495765504"
TITLE = "〖2026聲浪藝術節〗《海角七號》造夢者"

class Cases(unittest.TestCase):
    def test_event_url(self):
        self.assertIsNotNone(safe_event(GOOD))
    def test_external(self):
        self.assertIsNone(safe_event("https://evil.example" + GOOD))
    def test_http(self):
        self.assertIsNone(safe_event("http://www.opentix.life" + GOOD))
    def test_protocol_relative(self):
        self.assertIsNone(safe_event("//www.opentix.life" + GOOD))
    def test_credentials(self):
        self.assertIsNone(safe_event("https://u@www.opentix.life" + GOOD))
    def test_query(self):
        self.assertIsNone(safe_event(GOOD + "?ticket=1"))
    def test_fragment(self):
        self.assertIsNone(safe_event(GOOD + "#abc"))
    def test_wrong_path(self):
        self.assertIsNone(safe_event("/event/ABC"))
    def test_category(self):
        self.assertEqual(label_title("戲劇 " + TITLE), TITLE)
    def test_generic(self):
        self.assertIsNone(label_title("看全部"))
    def test_index_edge(self):
        self.assertEqual(index_edges('<a href="' + GOOD + '">戲劇 ' + TITLE + '</a>'), [(safe_event(GOOD), TITLE)])
    def test_conflicting_titles(self):
        html = '<a href="' + GOOD + '">戲劇 ' + TITLE + '</a><a href="' + GOOD + '">音樂 另一場活動</a>'
        self.assertEqual(index_edges(html), [])
    def test_review(self):
        html = "<h1>" + TITLE + "</h1><h2>購票資訊</h2><p>選擇場次</p><p>選擇場館</p>"
        value = inspect_detail(html, TITLE)
        self.assertEqual(value["decision"], "REVIEW_EXACT_EVENT_TITLE_TICKET_SECTION_NO_FIELDS")
        self.assertEqual(value["acceptedFields"], 0)
        self.assertEqual(value["sessionChooserLabelCount"], 1)
    def test_refund_not_session(self):
        value = inspect_detail("<h1>" + TITLE + "</h1><h2>購票資訊</h2><p>退票期限：</p>", TITLE)
        self.assertEqual(value["sessionChooserLabelCount"], 0)
        self.assertEqual(value["refundLabelCount"], 1)
    def test_mismatch(self):
        self.assertEqual(inspect_detail("<h1>其他節目</h1><h2>購票資訊</h2>", TITLE)["decision"], "HOLD_EVENT_TITLE_MISMATCH_OR_AMBIGUITY")
    def test_missing_section(self):
        self.assertEqual(inspect_detail("<h1>" + TITLE + "</h1>", TITLE)["decision"], "HOLD_TICKET_SECTION_MISSING_OR_DUPLICATED")
    def test_duplicate_title(self):
        self.assertEqual(inspect_detail("<h1>" + TITLE + "</h1><h1>" + TITLE + "</h1><h2>購票資訊</h2>", TITLE)["decision"], "HOLD_EVENT_TITLE_MISMATCH_OR_AMBIGUITY")

if __name__ == "__main__":
    unittest.main()

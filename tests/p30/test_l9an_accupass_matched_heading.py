"""P30-L9-AN exact heading anchor, bounded local role and fail-closed negatives."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_l9an_accupass_matched_heading as m

TITLE = "Example event"
GOOD = ('<main><div><h1>Example event</h1>'
        '<div><span>活動日期</span><span>2026-11-01</span></div>'
        '</div></main>')

class ExactHeadingContract(unittest.TestCase):
    def test_01_single_exact_local_pair(self):
        r = m.inspect_matched_region(GOOD, TITLE)
        self.assertTrue(r["assessed"])
        self.assertEqual(r["matchedHeadingCount"], 1)
        self.assertEqual(r["observedLocalPairs"], 1)
        self.assertEqual(r["roles"]["EVENT"], 1)
        self.assertEqual(r["acceptedFields"], 0)

    def test_02_mismatched_heading(self):
        r = m.inspect_matched_region(GOOD, "Another event")
        self.assertEqual(r["decision"], "HOLD_NO_EXACT_SEMANTIC_HEADING")

    def test_03_duplicate_exact_headings(self):
        r = m.inspect_matched_region(GOOD + '<main><h2>Example event</h2></main>', TITLE)
        self.assertEqual(r["decision"], "HOLD_MATCHED_HEADING_AMBIGUOUS")

    def test_04_hidden_heading(self):
        r = m.inspect_matched_region('<main><div hidden><h1>Example event</h1></div></main>', TITLE)
        self.assertEqual(r["decision"], "HOLD_MATCHED_HEADING_HIDDEN")

    def test_05_script_region(self):
        r = m.inspect_matched_region(GOOD.replace('</div></main>', '<script>x</script></div></main>'), TITLE)
        self.assertTrue(r["decision"].startswith("HOLD_"))

    def test_06_no_explicit_role_pair(self):
        r = m.inspect_matched_region('<main><div><h1>Example event</h1><p>2026-11-01</p></div></main>', TITLE)
        self.assertEqual(r["decision"], "HOLD_NO_EXPLICIT_LOCAL_ROLE_PAIR")

    def test_07_two_headings_same_region(self):
        r = m.inspect_matched_region('<main><h1>Example event</h1><h2>Another event</h2></main>', TITLE)
        self.assertEqual(r["decision"], "HOLD_REGION_HAS_OTHER_HEADINGS")

    def test_08_html_cap(self):
        r = m.inspect_matched_region("x" * (m.MAX_HTML_BYTES + 1), TITLE)
        self.assertEqual(r["decision"], "HOLD_HTML_OR_TITLE_CAP")

    def test_09_no_semantic_root(self):
        r = m.inspect_matched_region('<h1>Example event</h1>', TITLE)
        self.assertEqual(r["decision"], "HOLD_HEADING_ABSENT_OR_CAP")

    def test_10_no_global_regex_date(self):
        r = m.inspect_matched_region('<main><div><h1>Example event</h1>2026-11-01</div></main>', TITLE)
        self.assertEqual(r["decision"], "HOLD_NO_EXPLICIT_LOCAL_ROLE_PAIR")

    def test_11_review_requires_two_identities(self):
        one = {"details": [{"http": 200, "identityDecision": "REVIEW_EXACT_TITLE",
                            "fieldTopology": m.inspect_matched_region(GOOD, TITLE)}]}
        self.assertEqual(m.summarize(one)["decision"], "HOLD_MATCHED_HEADING_OR_IDENTITY")

    def test_12_two_exact_review_not_golden(self):
        one = {"http": 200, "identityDecision": "REVIEW_EXACT_TITLE",
               "fieldTopology": m.inspect_matched_region(GOOD, TITLE)}
        r = m.summarize({"details": [one, one], "listHttp": 200})
        self.assertTrue(r["decision"].startswith("REVIEW_"))
        self.assertEqual(r["goldenAccepted"], 0)

    def test_13_hold_identity_blocks_promotion(self):
        one = {"http": 200, "identityDecision": "HOLD_TITLE_MISMATCH",
               "fieldTopology": m.inspect_matched_region(GOOD, TITLE)}
        self.assertTrue(m.summarize({"details": [one, one]})["decision"].startswith("HOLD_"))

    def test_14_release_locked(self):
        self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
        self.assertEqual(m.MAX_HTML_BYTES, 1_500_000)

if __name__ == "__main__":
    unittest.main()

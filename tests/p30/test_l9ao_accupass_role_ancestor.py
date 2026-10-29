"""P30-L9-AO bounded ancestor selection, explicit roles and refusal cases."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_l9ao_accupass_role_ancestor as m

TITLE = "Example event"
WRAPPER = ('<main><section><div class="title"><h1>Example event</h1></div>'
           '<div class="role"><span>活動日期</span><span>2026-11-07</span></div></section></main>')

class AncestorTests(unittest.TestCase):
    def test_01_prior_heading_only_wrapper_holds(self):
        r = m.ORIGINAL_INSPECT(WRAPPER, TITLE)
        self.assertEqual(r["decision"], "HOLD_NO_EXPLICIT_LOCAL_ROLE_PAIR")

    def test_02_role_bearing_ancestor_reviews(self):
        r = m.inspect_role_ancestor(WRAPPER, TITLE)
        self.assertTrue(r["assessed"])
        self.assertTrue(r["decision"].startswith("REVIEW_"))
        self.assertEqual(r["roles"]["EVENT"], 1)
        self.assertEqual(r["acceptedFields"], 0)

    def test_03_no_explicit_pair_holds(self):
        r = m.inspect_role_ancestor(WRAPPER.replace("<span>活動日期</span><span>2026-11-07</span>",
                                                    "<p>2026-11-07</p>"), TITLE)
        self.assertTrue(r["decision"].startswith("HOLD_"))

    def test_04_conflicting_role_values_holds(self):
        r = m.inspect_role_ancestor(WRAPPER.replace("</section>",
            "<div class=\"role\"><span>活動日期</span><span>2026-11-08</span></div></section>"), TITLE)
        self.assertEqual(r["decision"], "HOLD_ANCESTOR_ROLE_CONFLICT")

    def test_05_other_heading_blocks_ancestor(self):
        r = m.inspect_role_ancestor(WRAPPER.replace("</section>",
            "<h2>Another event</h2></section>"), TITLE)
        self.assertTrue(r["decision"].startswith("HOLD_"))

    def test_06_hidden_heading_holds(self):
        r = m.inspect_role_ancestor(WRAPPER.replace('<div class="title">',
            '<div class="title" hidden>'), TITLE)
        self.assertTrue(r["decision"].startswith("HOLD_"))

    def test_07_script_ancestor_holds(self):
        r = m.inspect_role_ancestor(WRAPPER.replace("</section>",
            "<script>not trusted</script></section>"), TITLE)
        self.assertTrue(r["decision"].startswith("HOLD_"))

    def test_08_ambiguous_outer_role_holds(self):
        html = WRAPPER.replace("</main>", "<div class=\"role\"><span>票價</span><span>200</span></div></main>")
        r = m.inspect_role_ancestor(html, TITLE)
        self.assertEqual(r["decision"], "HOLD_ANCESTOR_SCOPE_CONFLICT")

    def test_09_mismatched_identity_holds(self):
        r = m.inspect_role_ancestor(WRAPPER, "Another event")
        self.assertEqual(r["decision"], "HOLD_NO_EXACT_SEMANTIC_HEADING")

    def test_10_html_cap_holds(self):
        r = m.inspect_role_ancestor("x" * (m.prior.MAX_HTML_BYTES + 1), TITLE)
        self.assertEqual(r["decision"], "HOLD_HTML_OR_TITLE_CAP")

    def test_11_no_global_regex(self):
        r = m.inspect_role_ancestor(WRAPPER.replace(
            "<div class=\"role\"><span>活動日期</span><span>2026-11-07</span></div>", "2026-11-07"), TITLE)
        self.assertTrue(r["decision"].startswith("HOLD_"))

    def test_12_release_stays_locked(self):
        self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
        self.assertEqual(m.ORIGINAL_INSPECT(WRAPPER, TITLE)["acceptedFields"], 0)

if __name__ == "__main__":
    unittest.main()

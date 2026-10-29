"""P30-VENUE-02D title-local roles and provenance refusal."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_venue02d_tmc_field_provenance as m

def html(pairs):
    return ('<main><section><h1>Example event</h1>' + pairs + '</section></main>').encode()
PAIR = '<dl><dt>活動日期</dt><dd>2026-11-07</dd></dl>'

class Contract(unittest.TestCase):
    def test_01_explicit_event_pair_review(self):
        r=m.inspect(html(PAIR), "Example event")
        self.assertEqual(r["decision"], "REVIEW_EXPLICIT_TITLE_LOCAL_ROLE_NOT_ACCEPTED")
        self.assertEqual(r["roles"]["EVENT"], 1)
        self.assertEqual(r["acceptedFields"], 0)
    def test_02_unlabeled_date_hold(self):
        self.assertEqual(m.inspect(html("<p>2026-11-07</p>"), "Example event")["decision"],
                         "HOLD_NO_EXPLICIT_TITLE_LOCAL_ROLE_PAIR")
    def test_03_conflicting_values_hold(self):
        self.assertEqual(m.inspect(html(PAIR + '<dl><dt>活動日期</dt><dd>2026-11-08</dd></dl>'), "Example event")["decision"],
                         "HOLD_FIELD_CONFLICTING_VALUES")
    def test_04_wrong_title_hold(self):
        self.assertEqual(m.inspect(html(PAIR), "Another event")["decision"],
                         "HOLD_FIELD_EXACT_HEADING_NOT_UNIQUE")
    def test_05_duplicate_title_hold(self):
        self.assertEqual(m.inspect(html(PAIR + "<h2>Example event</h2>"), "Example event")["decision"],
                         "HOLD_FIELD_EXACT_HEADING_NOT_UNIQUE")
    def test_06_script_region_hold(self):
        self.assertTrue(m.inspect(html(PAIR + "<script>ignored</script>"), "Example event")["decision"].startswith("HOLD_"))
    def test_07_other_role_not_event(self):
        r=m.inspect(html('<dl><dt>票價</dt><dd>200</dd></dl>'), "Example event")
        self.assertEqual(r["roles"]["PRICE"], 1)
        self.assertEqual(r["roles"]["EVENT"], 0)
    def test_08_html_cap(self):
        self.assertEqual(m.inspect(b"x"*(m.MAX_HTML+1), "Example event")["decision"], "HOLD_FIELD_INPUT")
    def test_09_no_publication(self):
        self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_10_hidden_ancestor_cannot_supply_field(self):
        source = ('<main hidden><section><h1>Example event</h1>' + PAIR + '</section></main>').encode()
        self.assertEqual(m.inspect(source, "Example event")["decision"],
                         "HOLD_FIELD_HIDDEN_HEADING_ANCESTOR")

if __name__ == "__main__":
    unittest.main()

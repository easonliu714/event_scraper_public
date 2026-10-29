"""P30-L9-AK synthetic heading-region regression; no HTTP."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
import p30_l9ak_accupass_heading_near as m
def wrap(x): return "<main>"+x+"</main>"
class HeadingTests(unittest.TestCase):
    def test_01_bounded(self):
        h=wrap("<section><h1>虛構</h1><div><span>票價</span><span>100</span></div></section>")
        self.assertEqual(m.inspect_heading_regions(h)["decision"],"REVIEW_BOUNDED_HEADING_TOPOLOGY_NOT_ACCEPTED")
    def test_02_pairs(self):
        h=wrap("<section><h1>虛構</h1><div><span>票價</span><span>100</span></div></section>")
        self.assertEqual(m.inspect_heading_regions(h)["observedLocalPairs"],1)
    def test_03_hidden(self):
        self.assertEqual(m.inspect_heading_regions(wrap("<div hidden><h1>x</h1></div>"))["decision"],"HOLD_HIDDEN_HEADING_ANCESTOR")
    def test_04_hidden_aria(self):
        self.assertEqual(m.inspect_heading_regions(wrap("<div aria-hidden='true'><h1>x</h1></div>"))["decision"],"HOLD_HIDDEN_HEADING_ANCESTOR")
    def test_05_no_heading(self): self.assertEqual(m.inspect_heading_regions(wrap("<div>abc</div>"))["decision"],"HOLD_NO_SEMANTIC_HEADING")
    def test_06_cap(self): self.assertEqual(m.inspect_heading_regions(wrap("<h1>x</h1>"*13))["decision"],"HOLD_HEADING_CAP")
    def test_07_multi(self):
        h=wrap("<section><h1>x</h1></section><section><h2>y</h2></section>")
        self.assertEqual(m.inspect_heading_regions(h)["decision"],"HOLD_MULTIPLE_HEADING_REGIONS")
    def test_08_script(self):
        h=wrap("<section><h1>x</h1><script>hello</script></section>")
        self.assertEqual(m.inspect_heading_regions(h)["decision"],"HOLD_INTERACTIVE_OR_SCRIPT_REGION")
    def test_09_invalid(self): self.assertEqual(m.inspect_heading_regions(None)["decision"],"HOLD_INVALID_HTML")
    def test_10_cap_bytes(self): self.assertEqual(m.inspect_heading_regions("x"*(1500001))["decision"],"HOLD_INVALID_HTML")
    def test_11_no_publish(self): self.assertFalse(m.offline_contract()["published"])
    def test_12_no_get(self): self.assertEqual(m.offline_contract()["httpRequests"],0)
    def test_13_zero_fields(self): self.assertEqual(m.offline_contract()["acceptedFields"],0)
    def test_14_no_raw(self):
        h=wrap("<section><h1>SECRET</h1><div><span>票價</span><span>SECRET</span></div></section>")
        self.assertNotIn("SECRET",str(m.inspect_heading_regions(h)))
if __name__=="__main__":unittest.main()

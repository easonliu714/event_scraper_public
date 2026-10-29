"""P30-VENUE-02A: offline positive/negative source boundary tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_venue02a_tmc_source as m

LIST=b'<main><a href="/tw/blog/show/ExampleEvent2026">Example title</a></main>'
DETAIL=b'<main><h2>Example title</h2></main>'
class Contract(unittest.TestCase):
    def test_01_official_path(self):
        self.assertTrue(m.safe_detail("https://www.tmc.taipei/tw/blog/show/ExampleEvent2026"))
    def test_02_other_host(self):
        self.assertFalse(m.safe_detail("https://evil.example/tw/blog/show/ExampleEvent2026"))
    def test_03_query(self):
        self.assertFalse(m.safe_detail("https://www.tmc.taipei/tw/blog/show/ExampleEvent2026?x=1"))
    def test_04_fragment(self):
        self.assertFalse(m.safe_detail("https://www.tmc.taipei/tw/blog/show/ExampleEvent2026#x"))
    def test_05_short_slug(self):
        self.assertFalse(m.safe_detail("https://www.tmc.taipei/tw/blog/show/ab"))
    def test_06_list(self):
        r=m.assess_list(LIST,200,m.LIST_URL,False)
        self.assertEqual(r["distinctDetailPaths"],1)
    def test_07_list_redirect(self):
        self.assertTrue(m.assess_list(LIST,200,m.LIST_URL,True)["decision"].startswith("HOLD_"))
    def test_08_list_bad_status(self):
        self.assertTrue(m.assess_list(LIST,403,m.LIST_URL,False)["decision"].startswith("HOLD_"))
    def test_09_list_external(self):
        r=m.assess_list(b'<a href="https://evil.example/tw/blog/show/ExampleEvent2026">x</a>',200,m.LIST_URL,False)
        self.assertEqual(r["distinctDetailPaths"],0)
    def test_10_list_no_title(self):
        r=m.assess_list(b'<a href="/tw/blog/show/ExampleEvent2026"></a>',200,m.LIST_URL,False)
        self.assertEqual(r["distinctDetailPaths"],0)
    def test_11_list_cap(self):
        self.assertEqual(m.assess_list(b"x"*(m.MAX_BYTES+1),200,m.LIST_URL,False)["decision"],"HOLD_LIST_INPUT")
    def test_12_detail_heading(self):
        url="https://www.tmc.taipei/tw/blog/show/ExampleEvent2026"
        self.assertTrue(m.assess_detail(DETAIL,200,url,url,False)["decision"].startswith("REVIEW_"))
    def test_13_detail_no_heading(self):
        url="https://www.tmc.taipei/tw/blog/show/ExampleEvent2026"
        self.assertEqual(m.assess_detail(b"<main>none</main>",200,url,url,False)["decision"],"HOLD_NO_DETAIL_HEADING")
    def test_14_detail_redirect(self):
        url="https://www.tmc.taipei/tw/blog/show/ExampleEvent2026"
        self.assertEqual(m.assess_detail(DETAIL,200,url,url,True)["decision"],"HOLD_DETAIL_URL_OR_REDIRECT")
    def test_15_no_formal_promotion(self):
        self.assertEqual(m.RELEASE,"HARD_HOLD_NO_PUBLICATION")
if __name__=="__main__":
    unittest.main()

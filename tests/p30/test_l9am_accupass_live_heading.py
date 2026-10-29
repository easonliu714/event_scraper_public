"""P30-L9-AM: offline source summarizer negatives; no network."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
import p30_l9am_accupass_live_heading as m
def sample(identity="REVIEW_SAME_EVENT_PATH_TITLE",assessed=True,decision="REVIEW_BOUNDED_HEADING_TOPOLOGY_NOT_ACCEPTED"):
    return {"http":200,"identityDecision":identity,"fieldTopology":{
        "assessed":assessed,"headingDecision":decision,"headingCount":1,
        "boundedRegions":1,"observedLocalPairs":0}}
class Contract(unittest.TestCase):
    def test_01_review(self):
        self.assertEqual(m.summarize({"details":[sample(),sample()]})["decision"],
                         "REVIEW_BOUNDED_HEADING_TOPOLOGY_NOT_FIELDS")
    def test_02_identity_hold(self):
        self.assertEqual(m.summarize({"details":[sample("HOLD_TITLE"),sample()]})["decision"],
                         "HOLD_IDENTITY_OR_COUNT")
    def test_03_count_hold(self):
        self.assertEqual(m.summarize({"details":[sample()]})["decision"],"HOLD_IDENTITY_OR_COUNT")
    def test_04_topology_hold(self):
        self.assertEqual(m.summarize({"details":[sample(assessed=False),sample()]})["decision"],
                         "HOLD_BOUNDED_HEADING_TOPOLOGY")
    def test_05_adapter_no_heading(self):
        self.assertFalse(m.adapter("<main><p>x</p></main>")["assessed"])
    def test_06_adapter_local(self):
        r=m.adapter("<main><section><h1>sample</h1><div><span>票價</span><span>100</span></div></section></main>")
        self.assertTrue(r["assessed"])
        self.assertEqual(r["observedLocalPairs"],1)
    def test_07_no_raw(self):
        r=m.summarize({"details":[sample(),sample()]})
        self.assertNotIn("sample",str(r))
        self.assertNotIn("https://",str(r))
    def test_08_no_accept(self):
        self.assertEqual(m.summarize({"details":[sample(),sample()]})["detailCount"],2)
        self.assertEqual(m.MAX_DETAILS,2)
if __name__=="__main__":
    unittest.main()

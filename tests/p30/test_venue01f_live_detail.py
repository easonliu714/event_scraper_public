"""VENUE-01F offline negative contracts. No source requests in tests."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
import p30_venue01f_live_detail as m
BODY=b'<html><main><h1>Sample</h1><section><p>\xe6\xb4\xbb\xe5\x8b\x95\xe6\x97\xa5\xe6\x9c\x9f: 2027/1/16</p></section></main></html>'
class TestVenueDetail(unittest.TestCase):
    def test_01_valid_structure_not_identity(self):
        r=m.assess_html(BODY,200,m.DETAIL,False)
        self.assertEqual(r["decision"],"REVIEW_HTTP200_DETAIL_STRUCTURE_NOT_IDENTITY")
        self.assertEqual(r["titleParity"],"UNVERIFIED_NO_SAME_SESSION_LIST")
    def test_02_redirect(self):
        self.assertEqual(m.assess_html(BODY,200,m.DETAIL,True)["decision"],"HOLD_URL_OR_REDIRECT")
    def test_03_official_url_only(self):
        self.assertEqual(m.assess_html(BODY,200,"https://evil.example/News_Content.aspx",False)["decision"],"HOLD_URL_OR_REDIRECT")
    def test_04_http(self):
        self.assertEqual(m.assess_html(BODY,403,m.DETAIL,False)["decision"],"HOLD_HTTP_OR_BODY_CAP")
    def test_05_body_cap(self):
        self.assertEqual(m.assess_html(b"x"*(m.MAX_BYTES+1),200,m.DETAIL,False)["decision"],"HOLD_HTTP_OR_BODY_CAP")
    def test_06_no_heading(self):
        self.assertEqual(m.assess_html(b"<main><p>Nothing</p></main>",200,m.DETAIL,False)["decision"],"HOLD_NO_DETAIL_HEADING")
    def test_07_no_promotion(self):
        r=m.assess_html(BODY,200,m.DETAIL,False)
        self.assertEqual(r["acceptedFields"],0)
        self.assertIsNone(r["ticketEventId"])
        self.assertFalse(r["published"])
    def test_08_no_raw_content(self):
        r=m.assess_html(BODY,200,m.DETAIL,False)
        self.assertNotIn("Sample",str(r))
        self.assertNotIn("2027/1/16",str(r))
if __name__=="__main__":
    unittest.main()

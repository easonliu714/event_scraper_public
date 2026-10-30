#!/usr/bin/env python3
"""VENUE-02Q redirect safety classification tests; no network."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02q_xinzhuang_redirect import classify_location,inspect_response
BASE="https://www.xzcac.ntpc.gov.tw/xmdoc/cont?xsmsid=abc"

class Cases(unittest.TestCase):
    def test_same_origin_relative_review_only(self):
        x=inspect_response(302,"/xmdoc/cont?xsmsid=def",BASE)
        self.assertEqual(x["locationClass"],"HTTPS_SAME_ORIGIN_UNFOLLOWED")
        self.assertEqual(x["decision"],"REVIEW_SAME_ORIGIN_REDIRECT_UNFOLLOWED_NO_IDENTITY")
        self.assertEqual(x["locationQueryKeys"],["xsmsid"])
        self.assertNotIn("def",str(x))
    def test_no_location_hold(self):
        self.assertEqual(inspect_response(302,None,BASE)["locationClass"],"MISSING_LOCATION")
    def test_http_hold(self):
        self.assertEqual(classify_location("http://www.xzcac.ntpc.gov.tw/xmdoc/cont",BASE)["locationClass"],"NON_HTTPS_SCHEME")
    def test_external_hold(self):
        self.assertEqual(classify_location("https://evil.example/xmdoc/cont",BASE)["locationClass"],"EXTERNAL_HOST")
    def test_userinfo_hold(self):
        self.assertEqual(classify_location("https://user:pass@www.xzcac.ntpc.gov.tw/xmdoc/cont",BASE)["locationClass"],"USERINFO_PRESENT")
    def test_port_hold(self):
        self.assertEqual(classify_location("https://www.xzcac.ntpc.gov.tw:444/xmdoc/cont",BASE)["locationClass"],"NONDEFAULT_PORT")
    def test_self_redirect_hold(self):
        self.assertEqual(classify_location(BASE,BASE)["locationClass"],"SELF_REDIRECT")
    def test_root_hold(self):
        self.assertEqual(classify_location("/",BASE)["locationClass"],"NON_DETAIL_TARGET")
    def test_malformed_port_hold(self):
        self.assertEqual(classify_location("https://www.xzcac.ntpc.gov.tw:abc/xmdoc/cont",BASE)["locationClass"],"MALFORMED_LOCATION")
    def test_not_redirect_hold(self):
        self.assertEqual(inspect_response(200,None,BASE)["decision"],"HOLD_NOT_REDIRECT")

if __name__=="__main__":unittest.main()

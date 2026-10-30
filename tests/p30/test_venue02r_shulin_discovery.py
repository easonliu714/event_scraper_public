#!/usr/bin/env python3
"""VENUE-02R index link role tests, offline."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_venue02r_shulin_discovery import safe_link,inspect_index
class Cases(unittest.TestCase):
    def test_relative_https_same_origin(self): self.assertIsNotNone(safe_link("/shulin_artcenter_chi/xmdoc?XsmSId=abc"))
    def test_external_refused(self): self.assertIsNone(safe_link("https://evil.example/xmdoc"))
    def test_http_refused(self): self.assertIsNone(safe_link("http://www.culture.ntpc.gov.tw/xmdoc"))
    def test_userinfo_refused(self): self.assertIsNone(safe_link("https://user:pass@www.culture.ntpc.gov.tw/xmdoc"))
    def test_port_refused(self): self.assertIsNone(safe_link("https://www.culture.ntpc.gov.tw:444/xmdoc"))
    def test_js_refused(self): self.assertIsNone(safe_link("javascript:alert(1)"))
    def test_index_roles_only(self):
        x=inspect_index('<a href="/shulin_artcenter_chi/xmdoc?XsmSId=abc">展覽</a>')
        self.assertEqual(x["decision"],"REVIEW_INDEX_LINK_ROLES_NO_LIST_OR_DETAIL_IDENTITY")
        self.assertEqual(x["acceptedFields"],0)
    def test_empty_hold(self): self.assertEqual(inspect_index("<p>展覽</p>")["decision"],"HOLD_NO_SOURCE_LOCAL_LINKS")
if __name__=="__main__": unittest.main()

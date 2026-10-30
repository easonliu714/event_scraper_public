#!/usr/bin/env python3
"""L9-BB safety-class refusal regression; no network."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from p30_l9bb_era_anchor_safety import classify_href,inspect
from p30_l9av_era_source_role import TITLE

def page(href):
    return (f"<h1>{TITLE}</h1><section><div><h4>場次列表</h4></div>"
            f"<div><table><tr><th>日期</th><th>時間</th><th>連結</th></tr>"
            f'<tr><td>2026/11/01</td><td>19:30</td><td><a href="{href}">訂票</a></td></tr>'
            "</table></div><h4>退票方式</h4></section>")

class Cases(unittest.TestCase):
    def test_http_refused(self):
        x=inspect(page("http://ticket.com.tw/purchase"),"2026-10-30T06:55:00Z")
        self.assertEqual(x["anchorSafetyClass"],"NON_HTTPS_SCHEME")
        self.assertEqual(x["decision"],"HOLD_UNSAFE_ANCHOR_CLASSIFIED")
        self.assertEqual((x["acceptedFields"],x["goldenAccepted"],x["published"]),(0,0,False))
        self.assertNotIn("http://ticket.com.tw/purchase",str(x))
    def test_userinfo_refused(self):
        self.assertEqual(classify_href("https://user:secret@ticket.com.tw/path"),"USERINFO_PRESENT")
    def test_port_refused(self):
        self.assertEqual(classify_href("https://ticket.com.tw:8443/path"),"NONDEFAULT_PORT")
    def test_malformed_port_refused(self):
        self.assertEqual(classify_href("https://ticket.com.tw:abc/path"),"MALFORMED_AUTHORITY_OR_PORT")
    def test_external_refused(self):
        self.assertEqual(classify_href("https://elsewhere.example/p"),"EXTERNAL_HOST")
    def test_https_safe_not_promoted(self):
        x=inspect(page("/activity?PRODUCT_ID=P1GFK34F&session=1"),"2026-10-30T06:55:00Z")
        self.assertEqual(x["decision"],"HOLD_PREDECESSOR_NOT_UNSAFE_ANCHOR")
    def test_javascript_refused(self):
        self.assertEqual(classify_href("javascript:alert(1)"),"NON_NAVIGABLE")
    def test_no_date_refused(self):
        x=inspect(page("http://ticket.com.tw/p").replace("2026/11/01","日期未定"),"2026-10-30T06:55:00Z")
        self.assertEqual(x["decision"],"HOLD_PREDECESSOR_NOT_UNSAFE_ANCHOR")
if __name__=="__main__":unittest.main()

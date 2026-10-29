#!/usr/bin/env python3
"""L9-AD bounded synthetic contracts; no network."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_l9ad_accupass_identity as m

TITLE = "測試音樂會"
URL = "https://www.accupass.com/event/260101010101000001"

class Contracts(unittest.TestCase):
    def test_01_kind(self): self.assertEqual(m.KIND,"EVENTRADAR_P30_L9AD_ACCUPASS_IDENTITY_V1")
    def test_02_release(self): self.assertEqual(m.RELEASE,"HARD_HOLD_NO_PUBLICATION")
    def test_03_parent(self): self.assertEqual(m.PARENT_HEAD,"3b6b64ff4803a1a156e5774a23850f756d31e799")
    def test_04_bounds(self): self.assertEqual((m.MAX_CANDIDATES,m.OBSERVATIONS),(30,4))
    def test_05_https(self): self.assertTrue(m.allowed(URL))
    def test_06_http(self): self.assertFalse(m.allowed(URL.replace("https","http")))
    def test_07_foreign(self): self.assertFalse(m.allowed("https://evil.example/event/260101010101000001"))
    def test_08_subdomain(self): self.assertFalse(m.allowed("https://accupass.com.evil.org/event/260101010101000001"))
    def test_09_userinfo(self): self.assertFalse(m.allowed("https://x@www.accupass.com/event/260101010101000001"))
    def test_10_port(self): self.assertFalse(m.allowed("https://www.accupass.com:8443/event/260101010101000001"))
    def test_11_fragment(self): self.assertFalse(m.allowed(URL+"#x"))
    def test_12_event_id(self): self.assertEqual(m.event_id(URL),"260101010101000001")
    def test_13_no_query_id(self): self.assertIsNone(m.event_id(URL+"?x=1"))
    def test_14_no_non_event(self): self.assertIsNone(m.event_id("https://www.accupass.com/search"))
    def test_15_list_anchor(self):
        rows,state,n=m.list_candidates(f'<a href="{URL}"><h3>{TITLE}</h3></a>')
        self.assertEqual((len(rows),state,n),(1,"REVIEW_LIST_CANDIDATES_ONLY",1))
    def test_16_list_no_global_title(self):
        rows,_,_=m.list_candidates(f'<h2>{TITLE}</h2><a href="{URL}">票</a>')
        self.assertEqual(len(rows),0)
    def test_17_list_duplicate(self):
        rows,_,_=m.list_candidates((f'<a href="{URL}">{TITLE}</a>')*2)
        self.assertEqual(len(rows),1)
    def test_18_list_offsite(self):
        rows,_,_=m.list_candidates(f'<a href="https://evil.org/event/260101010101000001">{TITLE}</a>')
        self.assertEqual(len(rows),0)
    def test_19_list_anchor_cap(self):
        rows,state,_=m.list_candidates("<a href='x'>x</a>"*(m.MAX_LINKS+1))
        self.assertEqual((rows,state),([],"HOLD_LIST_ANCHOR_CAP"))
    def test_20_list_html_cap(self):
        self.assertEqual(m.list_candidates("x"*(m.MAX_HTML+1))[1],"HOLD_LIST_HTML_CAP")
    def test_21_heading_exact(self):
        self.assertEqual(m.detail_snapshot(f"<h1>{TITLE}</h1>",TITLE)["exactHeadings"],1)
    def test_22_heading_partial(self):
        self.assertEqual(m.detail_snapshot(f"<h1>{TITLE} 票價</h1>",TITLE)["exactHeadings"],0)
    def test_23_metadata_only(self):
        r=m.detail_snapshot(f'<meta property="og:title" content="{TITLE}">',TITLE)
        self.assertEqual((r["exactHeadings"],r["metadataExact"]),(0,True))
    def test_24_heading_cap(self):
        self.assertEqual(m.detail_snapshot("<h2>x</h2>"*(m.MAX_HEADINGS+1),TITLE)["hold"],"HEADING_CAP")
    def test_25_heading_html_cap(self):
        self.assertEqual(m.detail_snapshot("x"*(m.MAX_HTML+1),TITLE)["hold"],"HTML_CAP")
    def test_26_metadata_hold(self):
        f=m.detail_snapshot(f'<meta property="og:title" content="{TITLE}">',TITLE)
        self.assertEqual(m.classify(dict(http=200,sameId=True,allowed=True,observations=[f]*4)),
                         "HOLD_METADATA_ONLY_NOT_IDENTITY")
    def test_27_heading_review_not_golden(self):
        f=m.detail_snapshot(f"<h1>{TITLE}</h1>",TITLE)
        self.assertEqual(m.classify(dict(http=200,sameId=True,allowed=True,observations=[f]*4)),
                         "REVIEW_STABLE_HEADING_EXACT_NOT_GOLDEN")
    def test_28_id_hold(self):
        self.assertEqual(m.classify(dict(http=200,sameId=False,allowed=True)),"HOLD_DETAIL_HTTP_OR_ID")
    def test_29_http_hold(self):
        self.assertEqual(m.classify(dict(http=403,sameId=True,allowed=True)),"HOLD_DETAIL_HTTP_OR_ID")
    def test_30_no_heading(self):
        f=m.detail_snapshot("<h2>別的活動</h2>",TITLE)
        self.assertEqual(m.classify(dict(http=200,sameId=True,allowed=True,observations=[f]*4)),
                         "HOLD_NO_SOURCE_BOUND_HEADING")
    def test_31_incomplete(self):
        self.assertEqual(m.classify(dict(http=200,sameId=True,allowed=True,observations=[])),
                         "HOLD_INCOMPLETE_OBSERVATIONS")
    def test_32_bad_status(self):
        with self.assertRaisesRegex(ValueError,"HOLD_STATUS_BLOB"): m.validate_status(b"{}")
    def test_33_source_error(self):
        self.assertEqual(m.classify(dict(error="TimeoutError")),"HOLD_DETAIL_TimeoutError")
    def test_34_no_publisher(self): self.assertFalse(hasattr(m,"publish"))
    def test_35_no_title_persisted(self):
        self.assertNotIn(TITLE,json.dumps(m.detail_snapshot(f"<h1>{TITLE}</h1>",TITLE),ensure_ascii=False))
    def test_36_url_path_not_identity_without_heading(self):
        f=m.detail_snapshot("<div>no title</div>",TITLE)
        self.assertEqual(f["exactHeadings"],0)
if __name__ == "__main__":
    unittest.main()

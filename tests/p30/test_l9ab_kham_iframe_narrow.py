#!/usr/bin/env python3
"""P30-L9-AB isolated positive/negative source-boundary contracts."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import p30_l9ab_kham_iframe_narrow as m

TITLE = "測試音樂會"
def frame(overflow=False, narrow=0, iframe=0, exact=0):
    return {"ready": "complete",
            "broad": {"zoneOverflow": overflow},
            "narrow": {"count": 1, "matches": narrow, "overflow": False},
            "iframeTopology": {"sameOriginAllowed": iframe, "exactBounded": exact}}
def sample(frames=None, **kw):
    s = {"sourceException": False, "sourceErrorKind": "NONE",
         "finalAllowed": True, "sameProductId": True, "http": 200,
         "frames": frames if frames is not None else [frame()] * 4}
    s.update(kw)
    return s
def report(**kw):
    d = {"sourceException": False, "sourceErrorKind": "NONE",
         "listFinalAllowed": True, "listHttp": 200,
         "listCounts": {"unsafeSelected": 0, "nonCanonical": 0, "provisionalObjects": 10},
         "samples": [{"decision": "HOLD"}] * 2}
    d.update(kw)
    return d

class Contracts(unittest.TestCase):
    def test_01_kind(self): self.assertEqual(m.KIND, "EVENTRADAR_P30_L9AB_KHAM_IFRAME_NARROW_V1")
    def test_02_release(self): self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_03_parent(self): self.assertEqual(m.PARENT_HEAD, "86ef4fffb67824f9981bba984ecadb62eca93631")
    def test_04_bounds(self): self.assertEqual((m.MAX_IFRAMES, m.MAX_DETAILS, m.SNAPSHOTS), (6,2,4))
    def test_05_narrow_match(self): self.assertEqual(m.narrow_snapshot("<main><h3>測試音樂會</h3></main>", TITLE)["matches"], 1)
    def test_06_narrow_outside(self): self.assertEqual(m.narrow_snapshot("<footer><h3>測試音樂會</h3></footer>", TITLE)["matches"], 0)
    def test_07_narrow_substring(self): self.assertEqual(m.narrow_snapshot("<main><h3>測試音樂會售票</h3></main>", TITLE)["matches"], 0)
    def test_08_narrow_overcap(self):
        r=m.narrow_snapshot("<main>"+"<h3>x</h3>"*(m.aa.MAX_ZONE_NODES+1)+"</main>", TITLE)
        self.assertTrue(r["overflow"])
        self.assertIsNone(r["matches"])
    def test_09_narrow_bytes(self):
        r=m.narrow_snapshot("a"*(m.aa.MAX_BYTES+1), TITLE)
        self.assertIsNone(r["matches"])
    def test_10_no_raw_title(self): self.assertNotIn(TITLE,json.dumps(m.narrow_snapshot("<main><h3>"+TITLE+"</h3></main>",TITLE),ensure_ascii=False))
    def test_11_source_exception(self): self.assertEqual(m.classify(sample(sourceException=True,sourceErrorKind="TIMEOUT")), "HOLD_DETAIL_SOURCE_TIMEOUT")
    def test_12_http(self): self.assertEqual(m.classify(sample(http=403)), "HOLD_DETAIL_IDENTITY_OR_HTTP")
    def test_13_id(self): self.assertEqual(m.classify(sample(sameProductId=False)), "HOLD_DETAIL_IDENTITY_OR_HTTP")
    def test_14_frames(self): self.assertEqual(m.classify(sample(frames=[frame()])), "HOLD_INCOMPLETE_FRAMES")
    def test_15_iframe_review_only(self): self.assertEqual(m.classify(sample(frames=[frame(exact=1)]*4)), "REVIEW_SAME_ORIGIN_IFRAME_EXACT_NOT_IDENTITY")
    def test_16_narrow_review_only(self): self.assertEqual(m.classify(sample(frames=[frame(overflow=True,narrow=1)]*4)), "REVIEW_NARROW_EXACT_BROAD_UNASSESSED")
    def test_17_overflow_zero(self): self.assertEqual(m.classify(sample(frames=[frame(overflow=True)]*4)), "HOLD_BROAD_OVERFLOW_NARROW_ZERO_NOT_IDENTITY")
    def test_18_overflow_null(self):
        f=frame(overflow=True)
        f["narrow"]={"overflow":True,"matches":None}
        self.assertEqual(m.classify(sample(frames=[f]*4)),"HOLD_NARROW_UNASSESSED")
    def test_19_same_origin_no_title(self): self.assertEqual(m.classify(sample(frames=[frame(iframe=1)]*4)), "HOLD_SAME_ORIGIN_IFRAME_NO_EXACT")
    def test_20_list_exception(self): self.assertEqual(m.decide(report(sourceException=True,sourceErrorKind="DNS")),"HOLD_LIST_SOURCE_DNS")
    def test_21_list_block(self): self.assertEqual(m.decide(report(listHttp=403)),"HOLD_LIST_ACCESS")
    def test_22_list_zero(self): self.assertEqual(m.decide(report(listCounts={"unsafeSelected":0,"nonCanonical":0,"provisionalObjects":0})),"HOLD_LIST_CANDIDATES")
    def test_23_report_hold(self): self.assertEqual(m.decide(report()),"HOLD_IFRAME_AND_NARROW_TITLE_NOT_FORMALLY_VERIFIED")
    def test_24_parent_bad_sha(self):
        with self.assertRaisesRegex(ValueError,"HOLD_STATUS_BLOB"): m.verify_parent(b"{}",b"{}",b"{}")
    def test_25_scraper_bad_sha(self):
        with patch.object(m.aa.z,"git_blob",side_effect=[m.aa.STATUS_BLOB,"bad"]):
            with self.assertRaisesRegex(ValueError,"HOLD_SCRAPER_BLOB"): m.verify_parent(b"{}",b"{}",b"{}")
    def test_26_parent_contract(self):
        with patch.object(m.aa.z,"git_blob",side_effect=[m.aa.STATUS_BLOB,m.aa.SOURCE_BLOB]):
            with self.assertRaisesRegex(ValueError,"HOLD_PARENT_CONTRACT"): m.verify_parent(b"{}",b"{}",b"{}")
    def test_27_iframe_unrelated_not_inspected(self):
        page=Mock()
        page.url="https://kham.com.tw/application/UTK02/UTK0201_.aspx"
        child=Mock()
        child.url="https://example.invalid/embed"
        page.frames=[Mock(),child]
        r=m.iframe_topology(page,TITLE)
        self.assertEqual((r["unrelated"],r["readable"],r["exactBounded"]),(1,0,0))
        child.content.assert_not_called()
    def test_28_iframe_opaque_not_inspected(self):
        page=Mock()
        page.url="https://kham.com.tw/application/UTK02/UTK0201_.aspx"
        child=Mock()
        child.url="about:blank"
        page.frames=[Mock(),child]
        r=m.iframe_topology(page,TITLE)
        self.assertEqual((r["opaque"],r["readable"]),(1,0))
        child.content.assert_not_called()
    def test_29_iframe_cap(self):
        page=Mock()
        page.url="https://kham.com.tw/application/UTK02/UTK0201_.aspx"
        children=[Mock(url="about:blank") for _ in range(8)]
        page.frames=[Mock()]+children
        r=m.iframe_topology(page,TITLE)
        self.assertEqual(r["total"],7)
        self.assertTrue(r["capped"])
        self.assertEqual(r["opaque"],6)
    def test_30_no_publisher(self): self.assertFalse(hasattr(m,"publish"))
if __name__ == "__main__":
    unittest.main()

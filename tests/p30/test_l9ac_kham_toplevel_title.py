#!/usr/bin/env python3
"""P30-L9-AC synthetic source-boundary and refusal tests."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import p30_l9ac_kham_toplevel_title as m

TITLE = "測試音樂會"
def snap(table=0, component=0, overflow=None):
    return dict(tableRows=1, labeledPairs=1, tableExact=table,
                components=1, componentExact=component, overflow=overflow)
def frame(**kw):
    return dict(ready="complete", topLevel=snap(**kw))
def sample(frames=None, **kw):
    d = dict(sourceException=False, sourceErrorKind="NONE",
             http=200, finalAllowed=True, sameProductId=True,
             frames=frames if frames is not None else [frame()] * m.SNAPSHOTS)
    d.update(kw)
    return d
def report(**kw):
    d = dict(sourceException=False, sourceErrorKind="NONE", listHttp=200,
             listFinalAllowed=True,
             listCounts=dict(unsafeSelected=0, nonCanonical=0, provisionalObjects=10),
             samples=[dict(decision="HOLD")] * 2)
    d.update(kw)
    return d

class Contracts(unittest.TestCase):
    def test_01_kind(self):
        self.assertEqual(m.KIND, "EVENTRADAR_P30_L9AC_KHAM_TOPLEVEL_TITLE_V1")
    def test_02_release(self):
        self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_03_parent(self):
        self.assertEqual(m.PARENT_HEAD, "f657555b16f41d4d24e4b67205c0c0019d0b12fe")
    def test_04_bounds(self):
        self.assertEqual((m.MAX_TABLES, m.MAX_ROWS, m.MAX_COMPONENTS, m.MAX_DETAILS, m.SNAPSHOTS), (12,160,64,2,4))
    def test_05_table_exact(self):
        html="<div id='content'><table><tr><th>節目名稱：</th><td>測試音樂會</td></tr></table></div>"
        self.assertEqual(m.top_level_snapshot(html,TITLE)["tableExact"],1)
    def test_06_table_outside_scope(self):
        html="<footer><table><tr><th>節目名稱</th><td>測試音樂會</td></tr></table></footer>"
        self.assertEqual(m.top_level_snapshot(html,TITLE)["tableExact"],0)
    def test_07_table_label_refusal(self):
        html="<main><table><tr><th>售票時間</th><td>測試音樂會</td></tr></table></main>"
        self.assertEqual(m.top_level_snapshot(html,TITLE)["tableExact"],0)
    def test_08_table_substring_refusal(self):
        html="<main><table><tr><th>活動名稱</th><td>測試音樂會開始售票</td></tr></table></main>"
        self.assertEqual(m.top_level_snapshot(html,TITLE)["tableExact"],0)
    def test_09_table_multicell(self):
        html="<main><table><tr><td>活動名稱</td><td>測試音樂會</td><td>備註</td></tr></table></main>"
        self.assertEqual(m.top_level_snapshot(html,TITLE)["tableExact"],1)
    def test_10_component_exact(self):
        html="<main><div class='event-title'>測試音樂會</div></main>"
        self.assertEqual(m.top_level_snapshot(html,TITLE)["componentExact"],1)
    def test_11_component_outside_scope(self):
        html="<footer><div class='event-title'>測試音樂會</div></footer>"
        self.assertEqual(m.top_level_snapshot(html,TITLE)["componentExact"],0)
    def test_12_component_partial(self):
        html="<main><div class='event-title'>測試音樂會 票價</div></main>"
        self.assertEqual(m.top_level_snapshot(html,TITLE)["componentExact"],0)
    def test_13_table_cap(self):
        html="<main>"+("<table></table>"*(m.MAX_TABLES+1))+"</main>"
        r=m.top_level_snapshot(html,TITLE)
        self.assertEqual(r["overflow"],"TABLE_COUNT")
        self.assertIsNone(r["tableExact"])
    def test_14_row_cap(self):
        html="<main><table>"+("<tr><td>a</td><td>b</td></tr>"*(m.MAX_ROWS+1))+"</table></main>"
        r=m.top_level_snapshot(html,TITLE)
        self.assertEqual(r["overflow"],"TABLE_ROWS")
        self.assertIsNone(r["tableExact"])
    def test_15_component_cap(self):
        html="<main>"+("<div class='event-title'>x</div>"*(m.MAX_COMPONENTS+1))+"</main>"
        r=m.top_level_snapshot(html,TITLE)
        self.assertEqual(r["overflow"],"COMPONENT_COUNT")
        self.assertIsNone(r["componentExact"])
    def test_16_bytes_cap(self):
        r=m.top_level_snapshot("a"*(m.ab.aa.MAX_BYTES+1),TITLE)
        self.assertEqual(r["overflow"],"HTML_BYTES")
    def test_17_long_text_not_matched(self):
        html="<main><div class='event-title'>"+TITLE+("a"*m.MAX_TEXT_CHARS)+"</div></main>"
        self.assertEqual(m.top_level_snapshot(html,TITLE)["componentExact"],0)
    def test_18_no_title_persisted(self):
        html="<main><div class='event-title'>"+TITLE+"</div></main>"
        self.assertNotIn(TITLE,json.dumps(m.top_level_snapshot(html,TITLE),ensure_ascii=False))
    def test_19_stable_review_only(self):
        self.assertEqual(m.classify(sample(frames=[frame(table=1)]*4)),
                         "REVIEW_STABLE_TOPLEVEL_EXACT_NOT_FORMAL_IDENTITY")
    def test_20_transient_hold(self):
        self.assertEqual(m.classify(sample(frames=[frame(),frame(),frame(table=1),frame()])),
                         "HOLD_TRANSIENT_TOPLEVEL_EXACT")
    def test_21_no_match_hold(self):
        self.assertEqual(m.classify(sample()),"HOLD_NO_BOUND_TOPLEVEL_TITLE")
    def test_22_overflow_unassessed(self):
        self.assertEqual(m.classify(sample(frames=[frame(table=1),frame(table=1),frame(table=1),frame(overflow="TABLE_ROWS")])),
                         "HOLD_TOPLEVEL_UNASSESSED")
    def test_23_source_error(self):
        self.assertEqual(m.classify(sample(sourceException=True,sourceErrorKind="TIMEOUT")),"HOLD_DETAIL_SOURCE_TIMEOUT")
    def test_24_http_refusal(self):
        self.assertEqual(m.classify(sample(http=403)),"HOLD_DETAIL_IDENTITY_OR_HTTP")
    def test_25_id_refusal(self):
        self.assertEqual(m.classify(sample(sameProductId=False)),"HOLD_DETAIL_IDENTITY_OR_HTTP")
    def test_26_frames_refusal(self):
        self.assertEqual(m.classify(sample(frames=[frame()])), "HOLD_INCOMPLETE_SNAPSHOTS")
    def test_27_list_source(self):
        self.assertEqual(m.decide(report(sourceException=True,sourceErrorKind="DNS")),"HOLD_LIST_SOURCE_DNS")
    def test_28_list_http(self):
        self.assertEqual(m.decide(report(listHttp=302)),"HOLD_LIST_ACCESS")
    def test_29_list_count(self):
        self.assertEqual(m.decide(report(listCounts=dict(unsafeSelected=0,nonCanonical=0,provisionalObjects=0))),"HOLD_LIST_CANDIDATES")
    def test_30_sample_count(self):
        self.assertEqual(m.decide(report(samples=[])),"HOLD_SAMPLE_COUNT")
    def test_31_report_hold(self):
        self.assertEqual(m.decide(report()),"HOLD_TOPLEVEL_TITLE_NOT_FORMALLY_VERIFIED")
    def test_32_bad_status(self):
        with self.assertRaisesRegex(ValueError,"HOLD_STATUS_BLOB"):
            m.verify_parent(b"{}",b"{}",b"{}")
    def test_33_bad_scraper(self):
        with patch.object(m.ab.aa.z,"git_blob",side_effect=[m.ab.aa.STATUS_BLOB,"bad"]):
            with self.assertRaisesRegex(ValueError,"HOLD_SCRAPER_BLOB"):
                m.verify_parent(b"{}",b"{}",b"{}")
    def test_34_parent_contract(self):
        with patch.object(m.ab.aa.z,"git_blob",side_effect=[m.ab.aa.STATUS_BLOB,m.ab.aa.SOURCE_BLOB]):
            with self.assertRaisesRegex(ValueError,"HOLD_PARENT_CONTRACT"):
                m.verify_parent(b"{}",b"{}",b"{}")
    def test_35_no_publisher(self):
        self.assertFalse(hasattr(m,"publish"))
    def test_36_metadata_not_identity(self):
        html="<html><head><title>測試音樂會</title></head><body></body></html>"
        r=m.top_level_snapshot(html,TITLE)
        self.assertEqual((r["tableExact"],r["componentExact"]),(0,0))
if __name__ == "__main__":
    unittest.main()

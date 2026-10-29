"""P30-L9-AF bounded ACCUPASS query-role synthetic tests; zero network."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_l9af_accupass_query_roles as m

URL = "https://www.accupass.com/event/260101010101000001"
TITLE = "測試音樂會"
def anchor(query="?utm_source=abc", title=TITLE, url=URL):
    return f'<a href="{url}{query}"><h3>{title}</h3></a>'
def frames(s):
    return [m.inspect(s) for _ in range(m.OBSERVATIONS)]
def decision(s):
    return m.classify(m.inspect(s), frames(s), 200, True, None)

class Contracts(unittest.TestCase):
    def test_01_kind(self): self.assertTrue(m.KIND.endswith("_V1"))
    def test_02_release(self): self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_03_parent(self): self.assertEqual(len(m.PARENT), 40)
    def test_04_observations(self): self.assertEqual(m.OBSERVATIONS, 4)
    def test_05_allowed(self): self.assertTrue(m.allowed(URL))
    def test_06_http_refused(self): self.assertFalse(m.allowed(URL.replace("https:", "http:")))
    def test_07_foreign_refused(self): self.assertFalse(m.allowed("https://evil.org/event/260101010101000001"))
    def test_08_suffix_refused(self): self.assertFalse(m.allowed("https://www.accupass.com.evil.org/event/x"))
    def test_09_userinfo_refused(self): self.assertFalse(m.allowed("https://x@www.accupass.com/event/x"))
    def test_10_port_refused(self): self.assertFalse(m.allowed("https://www.accupass.com:8080/event/x"))
    def test_11_fragment_refused(self): self.assertFalse(m.allowed(URL+"#x"))
    def test_12_tracking(self):
        q=m.query_roles("utm_source=a&utm_campaign=b")
        self.assertEqual(q["tracking"], {"utm_source":1,"utm_campaign":1})
    def test_13_no_values_persist(self):
        self.assertNotIn("privateValue", json.dumps(m.query_roles("utm_source=privateValue")))
    def test_14_semantic(self): self.assertEqual(m.query_roles("event_id=secret")["semantic"],1)
    def test_15_unknown(self): self.assertEqual(m.query_roles("unlisted_secret=secret")["unknown"],1)
    def test_16_unknown_names_not_persist(self):
        self.assertNotIn("unlisted_secret",json.dumps(m.query_roles("unlisted_secret=secret")))
    def test_17_bad_utf8(self): self.assertEqual(m.query_roles("foo=%FF")["malformed"],1)
    def test_18_query_cap(self): self.assertEqual(m.query_roles("x="+"a"*(m.MAX_QUERY_BYTES+1))["kind"],"OVER_CAP")
    def test_19_field_cap(self): self.assertEqual(m.query_roles("&".join("a=x" for _ in range(m.MAX_QUERY_FIELDS+1)))["malformed"],1)
    def test_20_empty(self): self.assertEqual(m.query_roles("")["kind"],"NONE")
    def test_21_event_query(self): self.assertEqual(m.inspect(anchor())["queryEventAnchors"],1)
    def test_22_path_id_with_query(self): self.assertEqual(m.inspect(anchor())["strictPathWithQuery"],1)
    def test_23_title_local(self): self.assertEqual(m.inspect(anchor())["localTitleOnQueryAnchors"],1)
    def test_24_no_global_title(self):
        s=f"<h2>{TITLE}</h2>"+anchor(title="x")
        self.assertEqual(m.inspect(s)["localTitleOnQueryAnchors"],0)
    def test_25_missing_title(self): self.assertEqual(m.inspect(anchor(title="x"))["missingLocalTitleOnQueryAnchors"],1)
    def test_26_duplicate_paths(self): self.assertEqual(m.inspect(anchor()*2)["duplicateEventPaths"],1)
    def test_27_query_review_not_identity(self):
        self.assertEqual(decision(anchor()),"REVIEW_TRACKING_NAMES_ONLY_NOT_CANONICAL_IDENTITY")
    def test_28_unknown_hold(self): self.assertEqual(decision(anchor("?token=secret")),"HOLD_QUERY_SEMANTICS_UNKNOWN")
    def test_29_semantic_hold(self): self.assertEqual(decision(anchor("?event_id=123")),"HOLD_QUERY_SEMANTICS_UNKNOWN")
    def test_30_id_shape_hold(self): self.assertEqual(decision(anchor(url="https://www.accupass.com/event/123")),"HOLD_EVENT_ID_PATH_SHAPE")
    def test_31_title_hold(self): self.assertEqual(decision(anchor(title="x")),"HOLD_ANCHOR_LOCAL_TITLE_MISSING")
    def test_32_malformed_hold(self): self.assertEqual(decision(anchor("?bad=%FF")),"HOLD_QUERY_MALFORMED_OR_CAP")
    def test_33_no_query_not_promoted(self): self.assertEqual(decision(anchor(query="")),"HOLD_EVENT_PATH_NOT_ACCEPTED")
    def test_34_external_hold(self): self.assertEqual(decision(anchor(url="https://evil.org/event/260101010101000001")),"HOLD_NO_EVENT_PATH")
    def test_35_html_cap(self): self.assertEqual(m.inspect("x"*(m.MAX_HTML_BYTES+1))["hold"],"HTML_CAP")
    def test_36_anchor_cap(self): self.assertEqual(m.inspect("<a href='/'>x</a>"*(m.MAX_ANCHORS+1))["hold"],"ANCHOR_CAP")
    def test_37_http_hold(self): self.assertEqual(m.classify(m.inspect(anchor()),frames(anchor()),403,True,None),"HOLD_HTTP_OR_REDIRECT")
    def test_38_error_hold(self): self.assertEqual(m.classify(m.inspect(anchor()),frames(anchor()),200,True,"TimeoutError"),"HOLD_NAVIGATION_ERROR")
    def test_39_incomplete_hold(self): self.assertEqual(m.classify(m.inspect(anchor()),[],200,True,None),"HOLD_OBSERVATION_INCOMPLETE")
    def test_40_no_detail(self): self.assertFalse(hasattr(m,"probe_detail"))
    def test_41_no_publisher(self): self.assertFalse(hasattr(m,"publish"))
    def test_42_no_id_leak(self): self.assertNotIn("260101010101000001",json.dumps(m.inspect(anchor())))
    def test_43_no_title_leak(self): self.assertNotIn(TITLE,json.dumps(m.inspect(anchor()),ensure_ascii=False))
    def test_44_no_url_leak(self): self.assertNotIn("https://",json.dumps(m.inspect(anchor())))
    def test_45_duplicate_tracking_name(self): self.assertEqual(m.query_roles("utm_source=a&utm_source=b")["tracking"]["utm_source"],2)
    def test_46_percent_encoded_name(self): self.assertEqual(m.query_roles("utm%5Fsource=x")["tracking"]["utm_source"],1)
    def test_47_invalid_key(self): self.assertEqual(m.query_roles("bad-key=x")["unknown"],1)
    def test_48_uppercase_tracking(self): self.assertEqual(m.query_roles("UTM_SOURCE=x")["tracking"]["utm_source"],1)

if __name__ == "__main__":
    unittest.main()

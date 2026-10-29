"""P30-L9-AE synthetic topology tests; zero network."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_l9ae_accupass_list_topology as m

URL = "https://www.accupass.com/event/260101010101000001"
TITLE = "測試音樂會"
def anchor(url=URL, title=TITLE):
    return f'<a href="{url}"><h3>{title}</h3></a>'
def frames(html):
    return [m.inspect(html) for _ in range(m.OBSERVATIONS)]

class Contracts(unittest.TestCase):
    def test_01_kind(self): self.assertTrue(m.KIND.endswith("_V1"))
    def test_02_release(self): self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_03_parent(self): self.assertEqual(len(m.PARENT), 40)
    def test_04_observations(self): self.assertEqual(m.OBSERVATIONS, 4)
    def test_05_allowed(self): self.assertTrue(m.allowed(URL))
    def test_06_http_refused(self): self.assertFalse(m.allowed(URL.replace("https:", "http:")))
    def test_07_foreign_refused(self): self.assertFalse(m.allowed("https://evil.org/event/260101010101000001"))
    def test_08_host_suffix_refused(self): self.assertFalse(m.allowed("https://accupass.com.evil.org/event/x"))
    def test_09_userinfo_refused(self): self.assertFalse(m.allowed("https://x@www.accupass.com/event/x"))
    def test_10_port_refused(self): self.assertFalse(m.allowed("https://www.accupass.com:8080/event/x"))
    def test_11_fragment_refused(self): self.assertFalse(m.allowed(URL+"#abc"))
    def test_12_strict_id(self): self.assertEqual(m.inspect(anchor())["strictWithLocalTitle"], 1)
    def test_13_duplicate(self): self.assertEqual(m.inspect(anchor()*2)["duplicateStrictAnchors"], 1)
    def test_14_query_refused_as_strict(self): self.assertEqual(m.inspect(anchor(URL+"?x=1"))["eventPathNonStrict"], 1)
    def test_15_short_id(self): self.assertEqual(m.inspect(anchor("https://www.accupass.com/event/123"))["eventPathNonStrict"], 1)
    def test_16_local_title_missing(self): self.assertEqual(m.inspect(anchor(title="x"))["strictMissingLocalTitle"], 1)
    def test_17_no_global_title(self):
        x=m.inspect(f"<h2>{TITLE}</h2><a href='{URL}'>x</a>")
        self.assertEqual(x["strictWithLocalTitle"], 0)
    def test_18_non_event(self): self.assertEqual(m.inspect("<a href='/search'>a</a>")["nonEventAnchors"], 1)
    def test_19_external_event(self): self.assertEqual(m.inspect(anchor("https://evil.org/event/260101010101000001"))["externalEventLinks"], 1)
    def test_20_anchor_cap(self): self.assertEqual(m.inspect("<a href='/'>x</a>"*(m.MAX_ANCHORS+1))["hold"], "ANCHOR_CAP")
    def test_21_html_cap(self): self.assertEqual(m.inspect("x"*(m.MAX_HTML_BYTES+1))["hold"], "HTML_CAP")
    def test_22_card_hint(self): self.assertEqual(m.inspect("<article><h3>x</h3></article>")["cardTitleHints"], 1)
    def test_23_review_not_golden(self):
        self.assertEqual(m.classify(m.inspect(anchor()),frames(anchor()),200,True,None),
                         "REVIEW_SAME_NAVIGATION_CANDIDATES_NOT_IDENTITY")
    def test_24_missing_title_hold(self):
        self.assertEqual(m.classify(m.inspect(anchor(title="x")),frames(anchor(title="x")),200,True,None),
                         "HOLD_STRICT_ID_LOCAL_TITLE_MISSING")
    def test_25_query_hold(self):
        s=anchor(URL+"?q=1")
        self.assertEqual(m.classify(m.inspect(s),frames(s),200,True,None),"HOLD_EVENT_PATH_FORMAT_OR_QUERY")
    def test_26_card_hold(self):
        s="<article><h3>測試</h3></article>"
        self.assertEqual(m.classify(m.inspect(s),frames(s),200,True,None),"HOLD_CARD_HINTS_WITHOUT_EVENT_URL")
    def test_27_zero_hold(self): self.assertEqual(m.classify(m.inspect(""),frames(""),200,True,None),"HOLD_NO_EVENT_SHAPED_ANCHORS")
    def test_28_http_hold(self): self.assertEqual(m.classify(m.inspect(anchor()),frames(anchor()),403,True,None),"HOLD_HTTP_OR_REDIRECT")
    def test_29_redirect_hold(self): self.assertEqual(m.classify(m.inspect(anchor()),frames(anchor()),200,False,None),"HOLD_HTTP_OR_REDIRECT")
    def test_30_error_hold(self): self.assertEqual(m.classify(m.inspect(anchor()),frames(anchor()),200,True,"TimeoutError"),"HOLD_NAVIGATION_ERROR")
    def test_31_cap_hold(self): self.assertEqual(m.classify(m.inspect("x"*(m.MAX_HTML_BYTES+1)),frames(anchor()),200,True,None),"HOLD_UNASSESSED_CAP")
    def test_32_incomplete_hold(self): self.assertEqual(m.classify(m.inspect(anchor()),[],200,True,None),"HOLD_OBSERVATION_INCOMPLETE")
    def test_33_status_blob_refused(self):
        with self.assertRaisesRegex(ValueError,"HOLD_STATUS_BLOB"): m.validate_status(b"{}")
    def test_34_no_publisher(self): self.assertFalse(hasattr(m,"publish"))
    def test_35_no_title_leak(self): self.assertNotIn(TITLE,json.dumps(m.inspect(anchor()),ensure_ascii=False))
    def test_36_no_id_leak(self): self.assertNotIn("260101010101000001",json.dumps(m.inspect(anchor())))
    def test_37_https_relative(self): self.assertEqual(m.inspect(anchor("/event/260101010101000001"))["strictWithLocalTitle"],1)
    def test_38_external_only_hold(self):
        s=anchor("https://evil.org/event/260101010101000001")
        self.assertEqual(m.classify(m.inspect(s),frames(s),200,True,None),"HOLD_EXTERNAL_EVENT_LINKS_NOT_FOLLOWED")
    def test_39_unassessed_frame(self):
        self.assertEqual(m.classify(m.inspect(anchor()),frames("x"*(m.MAX_HTML_BYTES+1)),200,True,None),"HOLD_UNASSESSED_CAP")
    def test_40_no_detail_navigation(self): self.assertFalse(hasattr(m,"probe_detail"))

if __name__ == "__main__":
    unittest.main()

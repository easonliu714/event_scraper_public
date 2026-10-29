"""P30-L9-AG offline bounded source/list/detail parity and privacy contracts; no network."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import p30_l9ag_accupass_detail_parity as m

URL = "https://www.accupass.com/event/260101010101000001?utm_source=test"
URL2 = "https://www.accupass.com/event/260101010101000002?utm_source=test"
TITLE = "測試音樂會"
CAND = ("260101010101000001", TITLE, URL)
def anchor(url=URL, title=TITLE):
    return f'<a href="{url}"><h3>{title}</h3></a>'
def pair():
    return anchor() + anchor(URL2, "第二場測試音樂會")
def headings(title=TITLE):
    return f'<html><body><h1>{title}</h1></body></html>'
def frames(title=TITLE):
    return [m.detail_heading_evidence(headings(title), TITLE) for _ in range(m.OBSERVATIONS)]
def check(url=URL, http=200, redirected=False, states=None, obs=None, error=None):
    return m.detail_decision(CAND, url, http, redirected,
                             states if states is not None else ["complete"]*m.OBSERVATIONS,
                             obs if obs is not None else frames(), error)

class Contracts(unittest.TestCase):
    def test_01_release(self): self.assertEqual(m.RELEASE, "HARD_HOLD_NO_PUBLICATION")
    def test_02_parent(self): self.assertEqual(m.PARENT, "ae54d7687893e4f0960fc7d3926c7a376798d386")
    def test_03_source(self): self.assertEqual(len(m.SOURCE_MAIN), 40)
    def test_04_status(self): self.assertEqual(len(m.STATUS_BLOB), 40)
    def test_05_data(self): self.assertEqual(len(m.DATA_BLOB), 40)
    def test_06_details_cap(self): self.assertEqual(m.MAX_DETAILS, 2)
    def test_07_observations(self): self.assertEqual(m.OBSERVATIONS, 4)
    def test_08_valid_query(self): self.assertTrue(m.safe_event(URL))
    def test_09_http_refused(self): self.assertFalse(m.safe_event(URL.replace("https:", "http:")))
    def test_10_foreign_refused(self): self.assertFalse(m.safe_event(URL.replace("www.accupass.com", "evil.org")))
    def test_11_userinfo_refused(self): self.assertFalse(m.safe_event(URL.replace("www.accupass.com", "a@www.accupass.com")))
    def test_12_port_refused(self): self.assertFalse(m.safe_event(URL.replace("accupass.com/", "accupass.com:8080/")))
    def test_13_fragment_refused(self): self.assertFalse(m.safe_event(URL+"#foo"))
    def test_14_no_query_refused(self): self.assertFalse(m.safe_event(URL.split("?")[0]))
    def test_15_unknown_query_refused(self): self.assertFalse(m.safe_event(URL+"&token=secret"))
    def test_16_semantic_query_refused(self): self.assertFalse(m.safe_event(URL+"&event_id=other"))
    def test_17_bad_encoding_refused(self): self.assertFalse(m.safe_event(URL+"&bad=%FF"))
    def test_18_bad_id_refused(self): self.assertFalse(m.safe_event(URL.replace("260101010101000001","a")))
    def test_19_list_pair(self):
        metrics, candidates=m.list_candidates(pair())
        self.assertEqual(metrics["candidateCount"],2)
        self.assertEqual(len(candidates),2)
    def test_20_list_duplicates(self):
        metrics,_=m.list_candidates(pair()+anchor(title="x"))
        self.assertEqual(metrics["uniquePaths"],2)
        self.assertEqual(metrics["candidateCount"],2)
    def test_21_conflicting_title_hold(self):
        metrics,_=m.list_candidates(pair()+anchor(title="另一個活動標題"))
        self.assertEqual(metrics["hold"],"CONFLICTING_LOCAL_TITLES")
    def test_22_untrusted_link_hold(self):
        metrics,_=m.list_candidates(pair()+anchor(url=URL+"&ticket=123"))
        self.assertEqual(metrics["hold"],"UNSAFE_OR_UNCLASSIFIED_EVENT_LINK")
    def test_23_insufficient_candidates_hold(self):
        metrics,_=m.list_candidates(anchor())
        self.assertEqual(metrics["hold"],"INSUFFICIENT_UNIQUE_TITLED_PATHS")
    def test_24_missing_title(self):
        metrics,_=m.list_candidates(anchor(title="x"))
        self.assertEqual(metrics["titledPaths"],0)
    def test_25_html_cap(self):
        metrics,_=m.list_candidates("x"*(m.MAX_HTML_BYTES+1))
        self.assertEqual(metrics["hold"],"HTML_CAP")
    def test_26_anchor_cap(self):
        metrics,_=m.list_candidates("<a href='/'>x</a>"*(m.MAX_ANCHORS+1))
        self.assertEqual(metrics["hold"],"ANCHOR_CAP")
    def test_27_title_nfc(self):
        self.assertEqual(m.normalized("e\u0301  test"), "é test")
    def test_28_heading_exact(self):
        self.assertEqual(m.detail_heading_evidence(headings(),"測試音樂會")["exactMatches"],1)
    def test_29_heading_mismatch(self):
        self.assertEqual(m.detail_heading_evidence(headings("另一個標題"),TITLE)["exactMatches"],0)
    def test_30_heading_zero(self):
        self.assertEqual(m.detail_heading_evidence("<html><div>no title</div></html>",TITLE)["headingCount"],0)
    def test_31_heading_cap(self):
        self.assertEqual(m.detail_heading_evidence("<h1>x</h1>"*(m.MAX_HEADINGS+1),TITLE)["hold"],"HEADING_CAP")
    def test_32_detail_review_only(self):
        self.assertEqual(check(),"REVIEW_EXACT_SAME_PATH_H1_H2_TITLE_NOT_FORMAL_IDENTITY")
    def test_33_detail_http_hold(self): self.assertEqual(check(http=403),"HOLD_DETAIL_HTTP")
    def test_34_detail_redirect_hold(self): self.assertEqual(check(redirected=True),"HOLD_REDIRECT_OR_ID_QUERY_CHANGED")
    def test_35_detail_query_changed_hold(self): self.assertEqual(check(url=URL+"&utm_medium=changed"),"HOLD_REDIRECT_OR_ID_QUERY_CHANGED")
    def test_36_detail_id_changed_hold(self): self.assertEqual(check(url=URL2),"HOLD_REDIRECT_OR_ID_QUERY_CHANGED")
    def test_37_detail_foreign_hold(self): self.assertEqual(check(url="https://evil.org/event/x"),"HOLD_REDIRECT_OR_ID_QUERY_CHANGED")
    def test_38_detail_interactive_hold(self):
        self.assertEqual(check(states=["interactive"]*4),"HOLD_DETAIL_INTERACTIVE")
    def test_39_detail_no_headings_hold(self):
        obs=[m.detail_heading_evidence("<div>x</div>",TITLE)]*4
        self.assertEqual(check(obs=obs),"HOLD_NO_H1_H2")
    def test_40_detail_mismatch_hold(self):
        self.assertEqual(check(obs=frames("不同的測試音樂會")),"HOLD_H1_H2_TITLE_MISMATCH")
    def test_41_detail_incomplete_hold(self):
        self.assertEqual(check(obs=[]),"HOLD_INCOMPLETE_OBSERVATIONS")
    def test_42_detail_error_hold(self):
        self.assertEqual(check(error="TimeoutError"),"HOLD_DETAIL_NAVIGATION_ERROR")
    def test_43_detail_overflow_hold(self):
        obs=[m.detail_heading_evidence("<h1>x</h1>"*(m.MAX_HEADINGS+1),TITLE)]*4
        self.assertEqual(check(obs=obs),"HOLD_DETAIL_UNASSESSED_CAP")
    def test_44_list_no_title_leak(self):
        self.assertNotIn(TITLE,json.dumps(m.list_candidates(pair())[0],ensure_ascii=False))
    def test_45_list_no_id_leak(self):
        self.assertNotIn("260101010101000001",json.dumps(m.list_candidates(pair())[0]))
    def test_46_list_no_url_leak(self):
        self.assertNotIn("https://",json.dumps(m.list_candidates(pair())[0]))
    def test_47_detail_no_title_leak(self):
        self.assertNotIn(TITLE,json.dumps(m.detail_heading_evidence(headings(),TITLE),ensure_ascii=False))
    def test_48_no_publish_function(self): self.assertFalse(hasattr(m,"publish"))
    def test_49_no_write_data_function(self): self.assertFalse(hasattr(m,"write_production"))
    def test_50_query_value_not_metrics(self):
        self.assertNotIn("test",json.dumps(m.list_candidates(pair())[0]))
    def test_51_unsafe_no_promote(self):
        self.assertFalse(m.safe_event(URL+"&utm_source=x&access_token=private"))
    def test_52_tracking_uppercase(self):
        self.assertTrue(m.safe_event(URL.replace("utm_source","UTM_SOURCE")))

if __name__ == "__main__":
    unittest.main()

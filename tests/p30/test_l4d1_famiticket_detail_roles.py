import importlib.util
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

p=Path(__file__).resolve().parents[2]/"scripts"/"p30_l4d1_famiticket_detail_roles.py"
spec=importlib.util.spec_from_file_location("famiticket_l4d1",p)
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

TITLE=s.TARGET_TITLE
ROW={"title":TITLE,"official_url":"https://www.famiticket.com.tw/Home/Activity/Info/"+"A"*40}
GOOD=("<h2>"+TITLE+"</h2><div>展出日期：2026/11/06～2026/11/09</div>"
      "<div>售票期間：2026/10/01～2026/11/05</div>"
      "<div>票券使用期限：2026/12/31</div>"
      "<div>報名期間：2026/10/10～2026/10/20</div>").encode()
BAD=("<h2>不相關活動</h2><p>展出日期：2026/11/06～2026/11/09</p>").encode()
NET={"state":"HTTP_OK","http_status":200,"sha256":"abc"}

class Tests(TestCase):
    def test_01_event_label_explicit(self):
        roles=s.labeled_date_roles(GOOD)
        self.assertEqual([x["roleLabel"] for x in roles],
            ["展出日期","售票期間","票券使用期限","報名期間"])
    def test_02_event_not_sales(self):
        data=s.labeled_date_roles(GOOD)
        self.assertEqual(data[0]["role"],"EVENT_OCCURRENCE_EVIDENCE")
        self.assertEqual(data[1]["role"],"SALE_WINDOW_NOT_EVENT")
        self.assertEqual(data[2]["role"],"VOUCHER_VALIDITY_NOT_EVENT")
        self.assertEqual(data[3]["role"],"REGISTRATION_WINDOW_NOT_EVENT")
    def test_03_never_promote_dates_even_when_title_matches(self):
        q=s.assess_detail(ROW,GOOD,NET)
        self.assertEqual(q["identity"],"EXACT_LIST_DETAIL_TITLE_MATCH")
        self.assertIsNone(q["dateStart"])
        self.assertFalse(q["eventTimeVerified"])
        self.assertEqual(q["saleStatus"],"UNKNOWN")
    def test_04_wrong_title_rejects_role_promotion(self):
        q=s.assess_detail(ROW,BAD,NET)
        self.assertEqual(q["identity"],"DETAIL_TITLE_IDENTITY_HOLD")
        self.assertEqual(q["roles"],[])
    def test_05_http200_without_body_is_hold(self):
        q=s.assess_detail(ROW,None,{"http_status":200,"state":"EMPTY_HTML"})
        self.assertEqual(q["identity"],"HTTP_OR_CONTENT_HOLD")
        self.assertEqual(q["roles"],[])
    def test_06_page_title_2026_does_not_become_date(self):
        self.assertEqual(s.labeled_date_roles(b"<title>2026 SHOW 10/01</title>"),[])
    def test_07_invalid_leap_day_is_ignored(self):
        self.assertEqual(s.iso_dates("2026/02/29 2024/02/29"),["2024-02-29"])
    def test_08_roc_year_date_not_inferred(self):
        self.assertEqual(s.iso_dates("115/11/06 11/06"),[])
    def test_09_unlabeled_date_not_classified(self):
        self.assertEqual(s.labeled_date_roles(b"<p>2026/11/06</p>"),[])
    def test_10_fake_label_inside_scripts_dropped(self):
        html=b"<script>var x='':</script><div>var: 2026/11/01</div>"
        self.assertEqual(s.labeled_date_roles(html),[])
    def test_11_mixed_role_order_must_be_stable(self):
        x=s.labeled_date_roles("<div>售票期間：2026/11/01 至 2026/11/05</div><div>展出日期：2026/11/06 至 2026/11/09</div>")
        self.assertEqual([a["role"] for a in x],["SALE_WINDOW_NOT_EVENT","EVENT_OCCURRENCE_EVIDENCE"])
    def test_12_sales_tag_cannot_expand_ticket_status(self):
        q=s.assess_detail(ROW,("<h2>"+TITLE+"</h2><div>售票期間：2026/10/01</div><button>立即購票</button>").encode(),NET)
        self.assertEqual(q["saleStatus"],"UNKNOWN")
    def test_13_mismatch_twice_is_stability_hold(self):
        self.assertEqual(s.repeat_stability([{"identity":"DETAIL_TITLE_IDENTITY_HOLD"}]*2),"TWO_RESPONSES_WITHOUT_TITLE_HOLD")
    def test_14_one_match_is_intermittent_hold(self):
        a=[{"identity":"EXACT_LIST_DETAIL_TITLE_MATCH"},{"identity":"HTTP_OR_CONTENT_HOLD"}]
        self.assertEqual(s.repeat_stability(a),"INTERMITTENT_TITLE_MATCH_HOLD")
    def test_15_both_match_no_golden_claim(self):
        a=[{"identity":"EXACT_LIST_DETAIL_TITLE_MATCH"}]*2
        self.assertEqual(s.repeat_stability(a),"SAMPLED_TWICE_IDENTITY_MATCH_NOT_EVENT_GOLDEN")
    def test_16_wrong_observation_count_rejected(self):
        with self.assertRaises(ValueError):s.repeat_stability([{"identity":"EXACT_LIST_DETAIL_TITLE_MATCH"}])
    def test_17_real_runner_count_and_unchanged_target(self):
        fake_html=b"<html>official list</html>"
        sample=[ROW.copy()]
        with patch.object(s.fami,"fetch",side_effect=[(fake_html,NET),(GOOD,NET),(BAD,NET)]) as f, \
             patch.object(s.fami,"parse_list",return_value=(sample,{"candidate_count":1})):
            rows,report=s.build(None,sleep=lambda _:None)
        self.assertEqual(len(rows),1)
        self.assertEqual(report["state"],"INTERMITTENT_TITLE_MATCH_HOLD")
        self.assertEqual(report["sampleCount"],2)
        self.assertEqual(report["maxDetailGET"],2)
        self.assertFalse(report["goldenAccepted"])
        self.assertIsNone(report["eventDateStart"])
        self.assertFalse(report["writerExecuted"])
        self.assertEqual(f.call_count,3)
    def test_18_missing_list_identity_blocks_http_detail(self):
        with patch.object(s.fami,"fetch",return_value=(b"fake",NET)) as f, \
             patch.object(s.fami,"parse_list",return_value=([],{"candidate_count":0})):
            rows,report=s.build(None,sleep=lambda _:None)
        self.assertEqual(rows,[])
        self.assertEqual(report["state"],"TARGET_TITLE_UNIQUE_IDENTITY_HOLD")
        self.assertEqual(f.call_count,1)
    def test_19_unsafe_detail_url_rejected_by_original_module(self):
        self.assertFalse(s.fami.allowed("https://bad.example/Home/Activity/Info/"+"A"*40,detail=True))
        self.assertFalse(s.fami.allowed("http://www.famiticket.com.tw/Home/Activity/Info/"+"A"*40,detail=True))

if __name__=="__main__":main()

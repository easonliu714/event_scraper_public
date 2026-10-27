"""P30-L9-C fully offline positive/negative contracts: zero network before CI live stage."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "scripts" / "p30_l9c_four_source_fresh.py"
spec = importlib.util.spec_from_file_location("eventradar_l9c", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

CK_LIST = '''<html><a href="/mocweb/reg/CKSMH/Detail.init.ctr?actId=123456">示範藝術展覽活動</a></html>'''
TW_LIST = '''<table><tr><td>10/01~10/27</td>
<td><a href="/exhibition_more.aspx?id=12345&p=home">臺北示範科技展覽</a></td>
<td>主辦單位</td><td>活動資訊</td><td>世貿一館</td></tr></table>'''
IB_LIST = '''<a href="/ActivityInfo/Details/1234"><h3>示範售票演出活動</h3></a>'''
FAM_KEY = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
FAM_LIST = '<a href="/Home/Activity/Info/'+FAM_KEY+'"><h3>台灣示範國際旅展</h3></a>'
CK_DETAIL = '<h1>示範藝術展覽活動</h1><div>展覽介紹</div>'
TW_DETAIL = '<h1>臺北示範科技展覽</h1><p>展出日期：2026/10/01～2026/10/27</p>'
IB_DETAIL = '<h1>示範售票演出活動</h1>'
FAM_DETAIL = '<h1>台灣示範國際旅展</h1>'
DETAIL_URLS = {
 "中正紀念堂": "https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId=123456",
 "台北世貿": "https://twtc.com.tw/exhibition_more.aspx?id=12345&p=home",
 "ibon": "https://ticket.ibon.com.tw/ActivityInfo/Details/1234",
 "FamiTicket": "https://www.famiticket.com.tw/Home/Activity/Info/"+FAM_KEY
}

class Response:
    def __init__(self, html=None, code=200, location=None):
        self.status_code = code
        self._bytes = (html or '').encode()
        self.headers = {'content-type': 'text/html; charset=utf-8'}
        if location:
            self.headers['location'] = location
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def iter_content(self, chunk_size=32768):
        for i in range(0,len(self._bytes),chunk_size):
            yield self._bytes[i:i+chunk_size]

class Session:
    def __init__(self, overrides=None):
        self.urls = []
        self.data = {
            m.SOURCES["中正紀念堂"]["list"]: Response(CK_LIST),
            m.SOURCES["台北世貿"]["list"]: Response(TW_LIST),
            "https://ticket.ibon.com.tw/Index/entertainment": Response(IB_LIST),
            "https://ticket.ibon.com.tw/Home/MoreResult?inATAPID=105&inATAPWebType=entertainment": Response('<html></html>'),
            m.SOURCES["FamiTicket"]["list"]: Response(FAM_LIST),
            DETAIL_URLS["中正紀念堂"]: Response(CK_DETAIL),
            DETAIL_URLS["台北世貿"]: Response(TW_DETAIL),
            DETAIL_URLS["ibon"]: Response(IB_DETAIL),
            DETAIL_URLS["FamiTicket"]: Response(FAM_DETAIL),
        }
        if overrides:
            self.data.update(overrides)
    def get(self, url, **kwargs):
        assert not kwargs.get('allow_redirects', False) and kwargs.get('stream') is True
        self.urls.append(url)
        return self.data.get(url, Response(code=404))
    def close(self):
        pass

class Tests(unittest.TestCase):
    def test_01_named_four_sources(self):
        self.assertEqual(m.PORTALS, ("中正紀念堂", "台北世貿", "ibon", "FamiTicket"))

    def test_02_twtc_table_list_not_generic_anchor(self):
        rows, extra = m.twtc_list(TW_LIST)
        self.assertEqual(len(rows), 1)
        self.assertEqual(extra["tableRows"], 1)
        self.assertEqual(rows[0]["identity"], "12345")

    def test_03_twtc_postponement_kept_raw(self):
        p=TW_LIST.replace("10/01~10/27","延期未定")
        rows,_=m.twtc_list(p)
        self.assertEqual(rows[0]["rawPeriod"], "延期未定")
        self.assertFalse(rows[0]["verified"])

    def test_04_twtc_ambiguous_date_not_promoted(self):
        rows,_=m.twtc_list(TW_LIST)
        self.assertEqual(rows[0]["rawPeriodRole"],"EXHIBITION_LIST_PERIOD_REVIEW_ONLY")

    def test_05_twtc_off_host_id_rejected(self):
        self.assertFalse(m.strict_detail_url("https://evil.test/exhibition_more.aspx?id=12345&p=home",
                        "twtc.com.tw","/exhibition_more.aspx","id"))

    def test_06_twtc_duplicate_identity_query_rejected(self):
        self.assertFalse(m.strict_detail_url("https://twtc.com.tw/exhibition_more.aspx?id=111&id=222",
                         "twtc.com.tw","/exhibition_more.aspx","id"))

    def test_07_twtc_path_escape_rejected(self):
        for url in ["http://twtc.com.tw/exhibition_more.aspx?id=1234",
                    "https://twtc.com.tw/evil/exhibition_more.aspx?id=1234",
                    "https://a@twtc.com.tw/exhibition_more.aspx?id=1234",
                    "https://twtc.com.tw/exhibition_more.aspx?id=12a",
                    "https://twtc.com.tw/exhibition_more.aspx?id=1234#top"]:
            self.assertFalse(m.strict_detail_url(url,"twtc.com.tw","/exhibition_more.aspx","id"),url)

    def test_08_twtc_no_cross_row_inferred_period(self):
        html='<tr><td>10/01~10/27</td><td>標題</td><td>主辦</td></tr>'
        rows,_=m.twtc_list('<table>'+html+'</table>')
        self.assertEqual(rows,[])

    def test_09_cksmh_act_id_bounded_positive(self):
        ck=m.module("ckunit","p30_l4b_cksmh_details.py")
        rows,extra=m.cksmh_list(CK_LIST,ck)
        self.assertEqual(rows[0]["identity"],"123456")
        self.assertEqual(extra["candidates"],1)

    def test_10_cksmh_foreign_links_rejected(self):
        ck=m.module("ckneg","p30_l4b_cksmh_details.py")
        rows,_=m.cksmh_list(CK_LIST.replace('href="/','href="https://fake.test/'),ck)
        self.assertEqual(rows,[])

    def test_11_cksmh_no_global_date_leak(self):
        ck=m.module("ckneg2","p30_l4b_cksmh_details.py")
        rows,_=m.cksmh_list(CK_LIST+"<p>活動時間 2032/01/01</p>",ck)
        self.assertIsNone(rows[0]["rawPeriod"])

    def test_12_fami_original_adapter_is_loadable(self):
        fam=m.module("famunit","p30_l3b_a_famiticket.py")
        rows,_=fam.parse_list(FAM_LIST)
        self.assertGreaterEqual(len(rows),1)
        self.assertTrue(rows[0]["official_url"].startswith("https://www.famiticket.com.tw/"))

    def test_13_ibon_specialized_id_only(self):
        ib=m.module("ibunit","p30_l3bb_ibon.py")
        rows,_=ib.parse_list(IB_LIST,"https://ticket.ibon.com.tw/Index/entertainment")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["officialUrl"],DETAIL_URLS["ibon"])

    def test_14_details_twtc_match_stays_review_only(self):
        rows,_=m.twtc_list(TW_LIST)
        res=m.detail_record("台北世貿",rows[0],TW_DETAIL,{"state":"HTTP_OK"})
        self.assertTrue(res["titleParity"])
        self.assertEqual(res["formalFieldPromotions"],0)
        self.assertEqual(res["fieldEvidence"][0]["verification"],"REVIEW_REQUIRED")

    def test_15_details_twtc_mismatch_holds(self):
        row=m.twtc_list(TW_LIST)[0][0]
        out=m.detail_record("台北世貿",row,"<h1>另一場展覽</h1>",{"state":"HTTP_OK"})
        self.assertFalse(out["titleParity"])
        self.assertEqual(out["fieldEvidence"],[])

    def test_16_fami_detail_heading_no_fuzzy(self):
        fam=m.module("fam2","p30_l3b_a_famiticket.py")
        row=m.item_from_specialized("FamiTicket",{"official_url":DETAIL_URLS["FamiTicket"],
            "title":"台灣示範國際旅展"})
        ok=m.detail_record("FamiTicket",row,FAM_DETAIL,{"state":"HTTP_OK"},fam)
        fail=m.detail_record("FamiTicket",row,"<h1>不同活動</h1>",{"state":"HTTP_OK"},fam)
        self.assertTrue(ok["titleParity"])
        self.assertFalse(fail["titleParity"])

    def test_17_ibon_detail_heading_exact(self):
        ib=m.module("ib2","p30_l3bb_ibon.py")
        row=m.item_from_specialized("ibon",{"officialUrl":DETAIL_URLS["ibon"],"title":"示範售票演出活動"})
        self.assertTrue(m.detail_record("ibon",row,IB_DETAIL,{"state":"HTTP_OK"},ib)["titleParity"])

    def test_18_blank_http_never_promotes(self):
        out=m.detail_record("台北世貿",m.twtc_list(TW_LIST)[0][0],None,{"state":"HTTP_403"})
        self.assertEqual(out["formalFieldPromotions"],0)
        self.assertFalse(out["titleParity"])

    def test_19_no_output_to_production(self):
        for path in ("docs/l9c","scripts/new",".github/workflows","tests/test","."):
            with self.assertRaisesRegex(ValueError,"HOLD_ISOLATED"):
                m.safe_output(path)

    def test_20_mock_all_four_uses_no_actual_fresh_http(self):
        session=Session()
        report=m.acquire(session=session,sleeper=lambda _:None)
        self.assertEqual(report["candidateOrigin"],"L9C_SYNTHETIC_TEST_NOT_FRESH")
        self.assertEqual(report["actualFreshHTTPRequests"],0)
        self.assertGreaterEqual(report["syntheticTestGETs"],5)
        self.assertEqual(report["platformsAttempted"],4)
        self.assertFalse(report["published"])
        self.assertEqual(report["goldenAccepted"],0)
        self.assertEqual(report["formalDatePriceTicketPromotions"],0)

    def test_21_mock_404_is_not_event_cancelled(self):
        session=Session({m.SOURCES["台北世貿"]["list"]:Response(code=404)})
        report=m.acquire(session=session,sleeper=lambda _:None)
        row=next(x for x in report["sources"] if x["platform"]=="台北世貿")
        self.assertEqual(row["listCandidates"],0)
        self.assertEqual(row["state"],"HOLD_LIST_ZERO_OR_HTTP")

    def test_22_duplicate_ibon_two_listings_stay_one(self):
        session=Session({"https://ticket.ibon.com.tw/Home/MoreResult?inATAPID=105&inATAPWebType=entertainment":Response(IB_LIST)})
        report=m.acquire(session=session,sleeper=lambda _:None)
        row=next(x for x in report["sources"] if x["platform"]=="ibon")
        self.assertEqual(row["listCandidates"],1)

    def test_23_min_delay_safety(self):
        with self.assertRaisesRegex(ValueError,"HOLD_BOUNDED_RATE"):
            m.acquire(session=Session(),delay=0.1,sleeper=lambda _:None)

    def test_24_sha_manifest_roundtrip(self):
        report=m.acquire(session=Session(),sleeper=lambda _:None)
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            m.emit(report,tmp)
            manifest=json.loads((Path(tmp)/"manifest.json").read_text())
            candidate=(Path(tmp)/"fresh_four_source_diagnostics.json").read_bytes()
            self.assertEqual(manifest["sha256"]["fresh_four_source_diagnostics.json"],m.hexdigest(candidate))
            self.assertEqual(manifest["releaseState"],"HARD_HOLD_NO_PUBLICATION")

    def test_25_isolated_no_writer_or_scheduler(self):
        report=m.acquire(session=Session(),sleeper=lambda _:None)
        self.assertFalse(report["writerExecuted"])
        self.assertFalse(report["schedulerExecuted"])
        self.assertFalse(report["notifierExecuted"])
        self.assertFalse(report["fullPlatformCoverageVerified"])
        self.assertTrue(report["existingAndroid44Preserved"])

if __name__=="__main__":
    unittest.main()

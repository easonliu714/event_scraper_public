"""L9-D synthetic, zero-network DOM, structured scripts, and negative URL contracts."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "scripts/p30_l9d_ibon_public_dom.py"
spec = importlib.util.spec_from_file_location("eventradar_l9d", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ib = m.adapter()
BASE = ib.LISTS[0]
DETAIL = "https://ticket.ibon.com.tw/ActivityInfo/Details/1234"
TITLE = "臺北示範音樂會活動"
DIRECT = '<html><a href="/ActivityInfo/Details/1234"><h3>'+TITLE+'</h3></a></html>'
LD = '<script type="application/ld+json">'+json.dumps({
    "@context":"https://schema.org","@type":"MusicEvent",
    "name":TITLE,"url":DETAIL},ensure_ascii=False)+'</script>'
HYDRATION = '<script type="application/json">'+json.dumps({
    "page":{"events":[{"eventName":TITLE,"detailUrl":DETAIL}]}},
    ensure_ascii=False)+'</script>'
class Response:
    def __init__(self,body="",code=200,content_type="text/html"):
        self.status_code=code
        self.headers={"content-type":content_type}
        self.body=body.encode()
    def __enter__(self):
        return self
    def __exit__(self,*a):
        return False
    def iter_content(self,chunk_size=32768):
        for i in range(0,len(self.body),chunk_size):
            yield self.body[i:i+chunk_size]

class Session:
    def __init__(self,mapping=None):
        self.mapping={
            ib.LISTS[0]:Response("<html><div id='app'></div><script src='/js/main.js'></script></html>"),
            ib.LISTS[1]:Response("<html><div>No listed event</div></html>"),
            DETAIL:Response("<h1>"+TITLE+"</h1>")}
        if mapping:self.mapping.update(mapping)
        self.urls=[]
    def get(self,url,**opts):
        assert opts.get("stream") is True and opts.get("allow_redirects") is False
        self.urls.append(url)
        return self.mapping.get(url,Response(code=404))

class TestIBONDOM(unittest.TestCase):
    def analyze(self,html):
        return m.analyze(html,BASE,ib)
    def test_01_authority_two_official_list_urls(self):
        self.assertEqual(len(ib.LISTS),2)
        self.assertTrue(all(ib.role(u,listing=True) for u in ib.LISTS))
    def test_02_html_only_shell_yields_hold(self):
        rows,d=self.analyze("<div id='app'></div><script src='/js/app.js'></script>")
        self.assertFalse(rows)
        self.assertEqual(d["scriptRoleCounts"]["scriptSrcOfficialHost"],1)
    def test_03_direct_event_anchor(self):
        a,b=self.analyze(DIRECT)
        self.assertEqual(len(a),1)
        self.assertEqual(a[0]["candidateId"],"1234")
        self.assertEqual(a[0]["sourceEvidenceRole"],"DIRECT_ANCHOR_SAME_CARD_REVIEW_ONLY")
    def test_04_json_ld_same_object_event(self):
        a,d=self.analyze(LD)
        self.assertEqual(len(a),1)
        self.assertEqual(a[0]["officialUrl"],DETAIL)
        self.assertEqual(a[0]["sourceEvidenceRole"],"JSON_LD_EVENT_SAME_OBJECT_REVIEW_ONLY")
    def test_05_json_ld_bare_unrelated_product_rejected(self):
        a,_=self.analyze(LD.replace("MusicEvent","Product"))
        self.assertEqual(a,[])
    def test_06_json_ld_title_and_url_from_two_objects_never_joined(self):
        split={"@graph":[{"@type":"MusicEvent","name":TITLE},
                         {"@type":"MusicEvent","url":DETAIL}]}
        html='<script type="application/ld+json">'+json.dumps(split,ensure_ascii=False)+'</script>'
        self.assertEqual(self.analyze(html)[0],[])
    def test_07_html_non_json_script_is_never_evaluated(self):
        a,d=self.analyze("<script>window.x="+json.dumps({"eventName":TITLE,"eventUrl":DETAIL},
          ensure_ascii=False)+";</script>")
        self.assertFalse(a)
        self.assertEqual(d["scriptRoleCounts"]["inlineNonJsonScript"],1)
    def test_08_hydration_direct_pair_review(self):
        a,d=self.analyze(HYDRATION)
        self.assertEqual(a[0]["sourceEvidenceRole"],"JSON_HYDRATION_SAME_OBJECT_REVIEW_ONLY")
        self.assertFalse(a[0]["detailIdentityVerified"])
    def test_09_hydration_off_origin_rejected(self):
        a,_=self.analyze(HYDRATION.replace("ticket.ibon.com.tw","evil.test"))
        self.assertEqual(a,[])
    def test_10_hydration_login_url_rejected(self):
        a,_=self.analyze(HYDRATION.replace(DETAIL,"https://ticket.ibon.com.tw/login"))
        self.assertEqual(a,[])
    def test_11_hydration_non_numeric_id_rejected(self):
        a,_=self.analyze(HYDRATION.replace("Details/1234","Details/ABCDEF"))
        self.assertEqual(a,[])
    def test_12_hydration_title_only_rejected(self):
        a,_=self.analyze(HYDRATION.replace('"detailUrl": "'+DETAIL+'"','"detailUrl": null'))
        self.assertEqual(a,[])
    def test_13_duplicate_urls_across_modes_deduplicated(self):
        a,_=self.analyze(DIRECT+LD+HYDRATION)
        self.assertEqual(len(a),1)
    def test_14_script_external_not_downloaded(self):
        a,d=self.analyze('<script src="https://evil.test/app.js"></script>')
        self.assertEqual(a,[])
        self.assertEqual(d["scriptRoleCounts"]["scriptSrcOtherHost"],1)
        self.assertFalse(d["thirdPartyScriptDownloaded"])
    def test_15_malformed_json_kept_as_diagnostic(self):
        a,d=self.analyze('<script type="application/json">{invalid}</script>')
        self.assertFalse(a)
        self.assertEqual(d["malformedJsonCount"],1)
    def test_16_script_bomb_is_bounded(self):
        a,d=self.analyze('<script type="application/json">'+"A"*(m.MAX_SCRIPT_BYTES+1)+"</script>")
        self.assertFalse(a)
        self.assertEqual(d["scriptRoleCounts"]["jsonScriptSizeOrQuantityHold"],1)
    def test_17_js_shell_hints_are_not_candidates(self):
        a,d=self.analyze('<div id="__next"></div><script>fetch("/api/events")</script>')
        self.assertFalse(a)
        self.assertTrue(d["renderingHints"]["nextNuxtAngularHint"])
        self.assertTrue(d["renderingHints"]["fetchOrAjaxInlineHint"])
    def test_18_waf_signal_does_not_forge_event(self):
        a,d=self.analyze("<h1>cloudflare captcha</h1>")
        self.assertEqual(a,[])
        self.assertTrue(d["renderingHints"]["wafOrCaptchaText"])
    def test_19_genuine_mock_empty_is_not_fresh_or_cancel(self):
        s=Session()
        result=m.run(session=s,sleep=lambda _:None)
        self.assertEqual(result["actualFreshHTTPRequests"],0)
        self.assertEqual(result["observedSyntheticRequests"],2)
        self.assertEqual(result["candidateCount"],0)
        self.assertEqual(result["sampleDetail"]["state"],"NOT_ATTEMPTED_NO_SOURCE_ID")
        self.assertEqual(result["releaseState"],m.HOLD)
    def test_20_mock_direct_detail_pass_is_not_formal_data(self):
        s=Session({ib.LISTS[0]:Response(DIRECT)})
        d=m.run(session=s,sleep=lambda _:None)
        self.assertEqual(len(s.urls),3)
        self.assertEqual(d["candidateCount"],1)
        self.assertTrue(d["sampleDetail"]["detailTitleParity"])
        self.assertEqual(d["formalFieldPromotions"],0)
        self.assertEqual(d["goldenAccepted"],0)
    def test_21_mock_json_ld_detail_mismatch_holds(self):
        s=Session({ib.LISTS[1]:Response(LD),DETAIL:Response("<h1>完全不同節目</h1>")})
        d=m.run(session=s,sleep=lambda _:None)
        self.assertEqual(d["candidateCount"],1)
        self.assertFalse(d["sampleDetail"]["detailTitleParity"])
        self.assertEqual(d["sampleDetail"]["state"],"TITLE_MISMATCH_OR_HTML_SHELL_HOLD")
    def test_22_403_page_is_not_deleted_event(self):
        d=m.run(session=Session({ib.LISTS[0]:Response(code=403)}),sleep=lambda _:None)
        self.assertEqual(d["candidateCount"],0)
        self.assertFalse(d["published"])
        self.assertFalse(d["writerExecuted"])
    def test_23_minimum_interval_mandatory(self):
        with self.assertRaisesRegex(ValueError,"HOLD_IBON_MINIMUM_RATE_INTERVAL"):
            m.run(session=Session(),delay=0.1,sleep=lambda _:None)
    def test_24_isolated_output_paths_only(self):
        for p in ("docs/l9d",".github/workflows",".git","scripts","tests","."):
            with self.assertRaisesRegex(ValueError,"HOLD_IBON_ISOLATED_OUTPUT_ONLY"):
                m.output_dir(p)
    def test_25_manifest_exact_sha_no_fresh_masquerade(self):
        result=m.run(session=Session(),sleep=lambda _:None)
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            manifest=m.seal(result,tmp)
            blob=(Path(tmp)/"fresh_ibon_dom_diagnostics.json").read_bytes()
            self.assertEqual(manifest["sha256"]["fresh_ibon_dom_diagnostics.json"],m.sha(blob))
            self.assertEqual(manifest["actualFreshHTTPRequests"],0)
    def test_26_nested_json_objects_bounded(self):
        doc={"data":{"level":{"events":[{"eventUrl":DETAIL,"eventName":TITLE}]}}}
        a,_=self.analyze('<script type="application/json">'+json.dumps(doc,ensure_ascii=False)+'</script>')
        self.assertEqual(len(a),1)
    def test_27_no_current_date_or_ticket_inferred_from_title(self):
        a,_=self.analyze(LD.replace(TITLE,"2026/11/28 售票已額滿音樂會"))
        self.assertEqual(len(a),1)
        self.assertNotIn("dateStart",a[0])
        self.assertNotIn("ticketStatus",a[0])
    def test_28_fake_duplicate_detail_ID_query_rejected(self):
        row=m.same_object_candidate({"@type":"Event","name":TITLE,
             "url":DETAIL+"?a=1"},BASE,ib,True)
        self.assertIsNone(row)

if __name__ == "__main__":
    unittest.main()

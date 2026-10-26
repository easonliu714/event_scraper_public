"""P30-L7-B offline positive and negative proof. All HTTP is fully mocked."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[2] / "scripts" / "p30_l7b_fresh_acquisition.py"
spec = importlib.util.spec_from_file_location("l7b", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

HOSTS = ("example.com",)
LIST_URL = "https://example.com/list"
DETAIL_URL = "https://example.com/events/123"
TITLE = "臺灣示範城市音樂祭"
LIST = '<a href="/events/123"><h3>' + TITLE + '</h3></a>'
DETAIL = '<html><head><meta property="og:title" content="' + TITLE + '"></head>' \
         '<body><h1>' + TITLE + '</h1><p>活動日期：2026/10/28</p>' \
         '<p>報名期間：2026/10/01-2026/10/08</p>' \
         '<p>售票期間：2026/10/12-2026/10/20</p>' \
         '<p>票券有效期間：2026/10/28-2026/10/28</p>' \
         '<p>入場時間：2026/10/28 17:00</p>' \
         '<p>活動地點：臺北市</p><p>票價：新台幣500元</p></body></html>'


class Response:
    def __init__(self, code=200, body=b"<html></html>", mime="text/html", location=None):
        self.status_code = code
        self.body = body
        self.headers = {"content-type": mime}
        if location is not None:
            self.headers["Location"] = location

    def __enter__(self):
        return self

    def __exit__(self, *ignored):
        return False

    def iter_content(self, chunk_size=32768):
        for i in range(0, len(self.body), chunk_size):
            yield self.body[i:i + chunk_size]


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.headers = {}
        self.request_urls = []

    def get(self, url, **kwargs):
        assert kwargs["allow_redirects"] is False and kwargs["stream"] is True
        self.request_urls.append(url)
        return next(self.responses)


def response(html):
    return Response(body=html.encode("utf-8"))


def fetch(responses, url=LIST_URL):
    s = Session(responses)
    counter = {"requests": 0}
    page, info = m.get_page(s, url, HOSTS, 6, counter)
    return s, counter, page, info


def run_mock(responses, pattern=r"/events/"):
    s = Session(responses)
    candidates, diagnosis = m.audit(
        [("Test", LIST_URL, HOSTS, pattern)], 1, 6, 0.7, 60,
        session=s, sleeper=lambda _t: None)
    return candidates, diagnosis, s


class L7BTests(unittest.TestCase):
    def test_01_all_19_sources_are_named_without_live_requests(self):
        self.assertEqual(len(m.PLATFORMS), 19)
        self.assertEqual(len(set(x[0] for x in m.PLATFORMS)), 19)
        endpoints = {p[0]: p[1] for p in m.PLATFORMS}
        self.assertEqual(endpoints["台北世貿"], "https://twtc.com.tw/exhibition?p=home")
        self.assertEqual(endpoints["中正紀念堂"],
                         "https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr")
        self.assertEqual(endpoints["FamiTicket"], "https://www.famiticket.com.tw/Home")
        self.assertEqual(endpoints["ibon"], "https://ticket.ibon.com.tw/Index/entertainment")
        self.assertTrue(all(m.allow_url(p[1], p[2]) for p in m.PLATFORMS))

    def test_02_http_allowlist_positive(self):
        self.assertTrue(m.allow_url(DETAIL_URL, HOSTS))
        self.assertTrue(m.allow_url("https://a.example.com/x", HOSTS))

    def test_03_http_non_tls_and_wrong_hosts_rejected(self):
        for u in ["http://example.com/x", "https://evil.com/x",
                  "https://example.com.evil.net/x", "file:///tmp/a",
                  "https://127.0.0.1/x", "https://example.com:8443/x"]:
            self.assertFalse(m.allow_url(u, HOSTS), u)

    def test_04_credentials_and_malformed_port_rejected(self):
        for u in ["https://a:b@example.com/x", "https://example.com:invalid/x"]:
            self.assertFalse(m.allow_url(u, HOSTS), u)

    def test_05_redirect_foreign_does_not_fetch(self):
        s, c, html, meta = fetch([Response(302, location="https://malicious.example.net/")])
        self.assertIsNone(html)
        self.assertEqual(meta["state"], "HOLD_URL_NOT_ALLOWLISTED")
        self.assertEqual(c["requests"], 1)
        self.assertEqual(len(s.request_urls), 1)

    def test_06_redirect_tls_downgrade_rejected(self):
        s, c, html, meta = fetch([Response(301, location="http://example.com/x")])
        self.assertIsNone(html)
        self.assertEqual(c["requests"], 1)

    def test_07_only_two_redirects_accepted(self):
        s, c, html, meta = fetch([
            Response(301, location="/r1"), Response(302, location="/r2"),
            Response(307, location="/r3")])
        self.assertIsNone(html)
        self.assertEqual(meta["state"], "HOLD_REDIRECT_LIMIT")
        self.assertEqual(c["requests"], 3)

    def test_08_403_is_not_cancelled_activity(self):
        _, _, body, meta = fetch([Response(403)])
        self.assertIsNone(body)
        self.assertEqual(meta["state"], "HTTP_403_BLOCKED")

    def test_09_404_is_not_event_expiration(self):
        _, _, body, meta = fetch([Response(404)])
        self.assertIsNone(body)
        self.assertEqual(meta["state"], "HTTP_404_NOT_FOUND")

    def test_10_429_is_reported_without_retry(self):
        s, c, body, meta = fetch([Response(429)])
        self.assertIsNone(body)
        self.assertEqual(meta["state"], "HTTP_429_RATE_LIMIT")
        self.assertEqual(len(s.request_urls), 1)

    def test_11_html_success_has_raw_body_sha(self):
        _, c, body, meta = fetch([response(LIST)])
        self.assertIn(TITLE, body)
        self.assertEqual(meta["state"], "HTTP_OK")
        self.assertEqual(len(meta["bodySHA256"]), 64)
        self.assertEqual(c["requests"], 1)

    def test_12_non_html_is_hold(self):
        _, _, body, meta = fetch([Response(200, b"{}", "application/json")])
        self.assertIsNone(body)
        self.assertEqual(meta["state"], "HOLD_NOT_HTML")

    def test_13_empty_response_is_hold(self):
        _, _, body, meta = fetch([Response(200, b"")])
        self.assertIsNone(body)
        self.assertEqual(meta["state"], "HOLD_EMPTY_BODY")

    def test_14_large_html_is_hold(self):
        _, _, body, meta = fetch([Response(200, b"x" * (m.MAX_BYTES + 1))])
        self.assertIsNone(body)
        self.assertEqual(meta["state"], "HOLD_SIZE_LIMIT")

    def test_15_list_unique_anchor_and_offdomain_filtered(self):
        rows, diag = m.parse_list(LIST + LIST +
                 '<a href="https://evil.net/events/123">Foreign event</a>',
                 "Test", LIST_URL, HOSTS, r"/events/")
        self.assertEqual(len(rows), 1)
        self.assertEqual(diag["anchorCount"], 3)
        self.assertEqual(rows[0]["detailStatus"], "NOT_SAMPLED")

    def test_16_list_uses_canonical_fragment_free_identity(self):
        rows, _ = m.parse_list(
            '<a href="/events/123#section">' + TITLE + '</a>',
            "Test", LIST_URL, HOSTS, r"/events/")
        self.assertEqual(rows[0]["sourceUrl"], DETAIL_URL)

    def test_17_200_no_list_is_not_zero_activity_assertion(self):
        rows, diag, _ = run_mock([response("<html><script>__NEXT_DATA__</script></html>")])
        self.assertEqual(rows["candidateEventRecords"], [])
        self.assertEqual(diag["platforms"][0]["listState"], "HOLD_NO_LIST_OR_JS_RENDERED")
        self.assertTrue(diag["platforms"][0]["jsRenderingHint"])
        self.assertEqual(diag["counts"]["httpOK"], 1)

    def test_18_waf_hint_on_200_not_accepted_list(self):
        _, extra = m.parse_list("<html>Cloudflare captcha</html>", "Test",
                                LIST_URL, HOSTS, r"/events/")
        self.assertTrue(extra["wafHint"])

    def test_19_detail_title_parity_exact(self):
        self.assertTrue(m.title_parity(TITLE, TITLE))

    def test_20_detail_title_parity_obvious_mismatch(self):
        self.assertFalse(m.title_parity(TITLE, "不同歌手的大型活動"))

    def test_21_detail_no_title_is_unverified(self):
        self.assertFalse(m.title_parity(TITLE, None))

    def test_22_extract_distinct_date_roles(self):
        ev = m.extract_fields(DETAIL, DETAIL_URL)
        self.assertTrue({"EVENT_PERIOD", "REGISTRATION_PERIOD", "SALE_PERIOD",
                         "VOUCHER_VALIDITY", "ADMISSION_TIME"}.issubset(
                         {x["role"] for x in ev}))
        self.assertTrue(all(x["verification"].endswith("REVIEW_REQUIRED") for x in ev))

    def test_23_evidence_from_labeled_fields_only(self):
        self.assertEqual(m.extract_fields(
            "<p>2026/11/01 巨型演出</p><p>售票資訊見官方網站</p>", DETAIL_URL), [])

    def test_24_full_mock_chain_no_claim_of_real_http(self):
        output, report, s = run_mock([response(LIST), response(DETAIL)])
        self.assertEqual(len(s.request_urls), 2)
        self.assertEqual(report["counts"]["listCandidates"], 1)
        self.assertEqual(report["counts"]["detailHttpOK"], 1)
        self.assertEqual(report["counts"]["detailIdentityVerified"], 1)
        self.assertGreater(report["counts"]["labelEvidenceObserved"], 0)
        self.assertEqual(report["actualFreshHTTPRequests"], 0)
        self.assertEqual(report["observedTestRequests"], 2)
        self.assertIn("TEST_INJECTION", output["candidateOrigin"])

    def test_25_chain_never_promotes_price_date_ticket(self):
        out, report, _ = run_mock([response(LIST), response(DETAIL)])
        row = out["candidateEventRecords"][0]
        for k in ("dateStart", "dateEnd", "venue", "price", "saleWindow",
                  "registrationPeriod", "voucherValidity"):
            self.assertIsNone(row[k], k)
        self.assertEqual(row["ticketStatus"], "UNKNOWN")
        self.assertFalse(row["goldenVerified"])
        self.assertEqual(report["goldenAccepted"], 0)

    def test_26_mismatched_detail_title_suppresses_field_evidence(self):
        wrong = DETAIL.replace(TITLE, "完全不同活動")
        out, report, _ = run_mock([response(LIST), response(wrong)])
        row = out["candidateEventRecords"][0]
        self.assertFalse(row["detailIdentityVerified"])
        self.assertEqual(row["fieldEvidence"], [])
        self.assertEqual(report["qualityGate"]["detail"], "HOLD")

    def test_27_detail_403_preserves_list_not_delete(self):
        out, report, _ = run_mock([response(LIST), Response(403)])
        self.assertEqual(out["candidateCount"], 1)
        self.assertEqual(out["candidateEventRecords"][0]["detailStatus"], "HTTP_403_BLOCKED")
        self.assertEqual(report["counts"]["detailHttpOK"], 0)

    def test_28_aggregator_separate_from_first_party(self):
        rows, _ = m.parse_list(
            '<a href="https://strolltimes.com/events/taipei/261017444444/">'+TITLE+'</a>',
            "StrollTimes", "https://strolltimes.com/", ("strolltimes.com",), r"/events/")
        self.assertEqual(rows[0]["sourceRole"], "THIRD_PARTY_AGGREGATOR_ARTICLE")
        self.assertFalse(rows[0]["goldenVerified"])

    def test_29_no_auto_merge_or_hide(self):
        out, diag, _ = run_mock([response(LIST), response(DETAIL)])
        self.assertFalse(out["mergeAllowed"])
        self.assertEqual(diag["automaticMergeCount"], 0)
        self.assertEqual(diag["automaticHideCount"], 0)
        self.assertFalse(diag["writerExecuted"])

    def test_30_docs_output_guard(self):
        with self.assertRaisesRegex(ValueError, "HOLD_ISOLATED"):
            m.safe_out("docs/data.json")

    def test_31_code_and_git_folder_guards(self):
        for path in (".github/workflows", ".git", "scripts", "tests", "."):
            with self.assertRaisesRegex(ValueError, "HOLD_ISOLATED"):
                m.safe_out(path)

    def test_32_artifact_manifest_hash_and_run_id(self):
        out, diag, _ = run_mock([response(LIST), response(DETAIL)])
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as root:
            manifest = m.emit(out, diag, root)
            self.assertEqual(set(manifest["filesSHA256"]),
                             {"fresh_candidate.json", "platform_diagnostics.json"})
            for filename, sha in manifest["filesSHA256"].items():
                self.assertEqual(sha, m.digest((Path(root) / filename).read_bytes()))
            self.assertEqual(manifest["runId"], out["runId"])

    def test_33_no_requests_without_real_live_mode(self):
        out, diag, s = run_mock([Response(404)])
        self.assertEqual(diag["actualFreshHTTPRequests"], 0)
        self.assertEqual(diag["counts"]["listCandidates"], 0)
        self.assertEqual(len(s.request_urls), 1)
        self.assertEqual(diag["qualityGate"]["http"], "HOLD")

    def test_34_unique_source_id_platform_scoped(self):
        a, _ = m.parse_list(LIST, "Test", LIST_URL, HOSTS, r"/events/")
        b, _ = m.parse_list(LIST, "Other", LIST_URL, HOSTS, r"/events/")
        self.assertNotEqual(a[0]["candidateId"], b[0]["candidateId"])


if __name__ == "__main__":
    unittest.main()

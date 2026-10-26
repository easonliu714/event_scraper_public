"""P30-L3-B FamiTicket synthetic no-network URL, parser and budget tests."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[2] / "scripts" / "p30_l3b_famiticket.py"
spec = importlib.util.spec_from_file_location("p30_l3b_fami", path)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

TOKEN = "RQA3AHUAbwBwAEgANwBzAFIAQQA1AGEAbABEADgAcABq"
INFO = "https://www.famiticket.com.tw/Home/Activity/Info/" + TOKEN
FIXTURE = (f'<a href="/Home/Activity/Info/{TOKEN}?utm_source=ignore">'
           '展覽 2026/11/06~2026/11/09 2026 國際旅展 購票</a>'
           f'<a href="/Home/Activity/Info/{TOKEN}">同活動重複入口</a>'
           '<a href="/Home/Activity/Info/QlBBQTFRSVlNTE9OR1RPS0VO">購票</a>'
           '<a href="https://evil.example/Home/Activity/Info/QlBBQTFRSVlNTE9OR1RPS0VO">假活動</a>')


class Response:
    def __init__(self, code=200, body=FIXTURE.encode("utf-8"), ct="text/html", loc=None):
        self.status_code = code
        self.body = body
        self.headers = {"content-type": ct}
        if loc:
            self.headers["location"] = loc

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def iter_content(self, chunk_size=32768):
        yield self.body


class Session:
    def __init__(self, values):
        self.values = iter(values)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        assert kwargs["allow_redirects"] is False
        assert kwargs["stream"] is True
        return next(self.values)


class Cases(unittest.TestCase):
    def test_allow_only_official_public_list_or_detail(self):
        self.assertTrue(p.allowlisted(p.BASE_URL))
        self.assertTrue(p.allowlisted(INFO))
        for item in ("https://www.famiticket.com.tw.evil.com/Home",
                     "https://www.famiticket.com.tw@evil.com/Home",
                     "http://www.famiticket.com.tw/Home",
                     "https://www.famiticket.com.tw:8888/Home",
                     "https://www.famiticket.com.tw/Home/../private",
                     "https://www.famiticket.com.tw/Account/Login",
                     "https://127.0.0.1/Home", "file:///tmp/secret"):
            with self.subTest(item=item):
                self.assertFalse(p.allowlisted(item))

    def test_canonical_detail_strips_fragment_tracking(self):
        self.assertEqual(p.canonical_info(INFO+"?utm_source=abc#foo", p.BASE_URL), INFO)
        self.assertIsNone(p.canonical_info("javascript:alert(1)", p.BASE_URL))
        self.assertIsNone(p.canonical_info("https://evil.example/Home", p.BASE_URL))
        self.assertIsNone(p.canonical_info("/Home", p.BASE_URL))

    def test_list_one_deduplicated_candidate_no_false_date(self):
        result, diag = p.parse_list(FIXTURE, p.BASE_URL)
        self.assertEqual(len(result), 1)
        self.assertEqual(diag["candidate_count"], 1)
        self.assertEqual(result[0]["official_url"], INFO)
        self.assertIn("國際旅展", result[0]["title"])
        self.assertIsNone(result[0]["date"])
        self.assertEqual(result[0]["source_time_role"], "UNVERIFIED_LIST_TEXT")
        self.assertEqual(result[0]["ticket_availability"], "UNKNOWN")

    def test_empty_or_navigation_not_a_event(self):
        rows, diag = p.parse_list("<a href='/Home'>首頁</a><a href='/news'>More</a>", p.BASE_URL)
        self.assertEqual(rows, [])
        self.assertEqual(diag["candidate_count"], 0)

    def test_403_404_429_blocked_no_retry(self):
        for code in (403, 404, 429):
            sess = Session([Response(code=code)])
            html, meta = p.get_html(sess, p.BASE_URL)
            self.assertIsNone(html)
            self.assertEqual(meta["http_status"], code)
            self.assertEqual(len(sess.calls), 1)

    def test_foreign_redirect_fails_closed(self):
        sess = Session([Response(code=302,loc="https://evil.example/Home")])
        html, meta = p.get_html(sess, p.BASE_URL)
        self.assertIsNone(html)
        self.assertEqual(meta["state"], "URL_REJECTED")
        self.assertEqual(len(sess.calls), 1)

    def test_allowlisted_redirect_observed(self):
        sess = Session([Response(code=302,loc="/Home/Index"),Response()])
        html, meta = p.get_html(sess, p.BASE_URL)
        self.assertIsNotNone(html)
        self.assertEqual(len(meta["trail"]), 2)

    def test_content_type_and_html_size_guard(self):
        for response, outcome in ((Response(ct="application/json"),"NON_HTML"),
                                  (Response(body=b""),"EMPTY_HTML"),
                                  (Response(body=b"x"*(p.MAX_BYTES+1)),"OVERSIZED_HTML")):
            html, meta = p.get_html(Session([response]), p.BASE_URL)
            self.assertIsNone(html)
            self.assertEqual(meta["state"], outcome)

    def test_bounded_list_and_detail_no_publishing(self):
        sess = Session([Response(),Response(body=b"<html>official</html>")])
        with patch.object(p.time, "sleep", return_value=None) as clock:
            candidates, report = p.run(sess)
        self.assertEqual(len(sess.calls), 2)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report["detail_sample"]["state"], "DETAIL_HTTP_OK")
        self.assertEqual(clock.call_count, 1)
        self.assertFalse(report["writer_executed"])
        self.assertFalse(report["notification_executed"])
        self.assertFalse(report["golden_accepted"])
        self.assertFalse(report["app_data_published"])

    def test_empty_result_no_detail_call(self):
        sess = Session([Response(body=b"<html>empty</html>")])
        rows, report = p.run(sess)
        self.assertEqual(rows, [])
        self.assertEqual(len(sess.calls), 1)
        self.assertEqual(report["detail_sample"]["state"], "NOT_ATTEMPTED")

    def test_rate_limit_negative(self):
        with self.assertRaisesRegex(ValueError,"RATE_LIMIT"):
            p.run(Session([]),interval=0)


if __name__ == "__main__":
    unittest.main()

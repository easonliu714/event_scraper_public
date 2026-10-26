"""No-network P30-L2-B CKSMH URL, parse, redirect and provenance tests."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[2] / "scripts" / "p30_l2b_cksmh.py"
spec = importlib.util.spec_from_file_location("p30_l2b_cksmh", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

BASE = "https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr"
ITEM = "/mocweb/reg/CKSMH/Detail.init.ctr;jsessionid=SECRET?actId=51331&utm_source=x"
LIST_HTML = (b'<a href="' + ITEM.encode() + b'">2026 Public Art Exhibition</a>'
             b'<a href="/mocweb/reg/CKSMH/Detail.init.ctr?actId=51331">Duplicate</a>'
             b'<a href="https://other.tld/mocweb/reg/CKSMH/Detail.init.ctr?actId=7">Evil</a>' +
             '<a href="/mocweb/reg/CKSMH/Detail.init.ctr?actId=81234">詳內容</a>'.encode('utf-8'))


class Response:
    def __init__(self, status=200, body=LIST_HTML, ct="text/html; charset=utf-8", location=None):
        self.status_code = status
        self.body = body
        self.headers = {"content-type": ct}
        if location:
            self.headers["location"] = location

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, chunk_size=32768):
        yield self.body


class Session:
    def __init__(self, responses):
        self._responses = iter(responses)
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        assert kwargs["allow_redirects"] is False
        assert kwargs["stream"] is True
        assert kwargs["timeout"][0] == 6
        return next(self._responses)


class L2BTests(unittest.TestCase):
    def test_allowed_official_cksmh_only(self):
        self.assertTrue(m.allowlisted(BASE))
        self.assertTrue(m.allowlisted("https://event.culture.tw/CKSMH"))
        for url in ("http://event.culture.tw/CKSMH",
                    "https://evil.tld/CKSMH",
                    "https://event.culture.tw.evil.tld/CKSMH",
                    "https://event.culture.tw@evil.tld/CKSMH",
                    "https://event.culture.tw:9443/CKSMH",
                    "https://event.culture.tw/admin/",
                    "https://event.culture.tw/CKSMH/../admin",
                    "file:///tmp/secret", "https://127.0.0.1/CKSMH"):
            with self.subTest(url=url):
                self.assertFalse(m.allowlisted(url))

    def test_session_tracking_removed_dedupe_and_noise(self):
        items, c = m.parse_list(LIST_HTML, BASE)
        self.assertEqual(len(items), 1)
        self.assertEqual(c["list_candidates"], 1)
        self.assertEqual(items[0]["official_url"],
                         "https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId=51331")
        self.assertIsNone(items[0]["date"])
        self.assertEqual(items[0]["ticket_availability"], "UNKNOWN")

    def test_portal_act_id_supported(self):
        url = "https://event.culture.tw/CKSMH/portal/Registration/C0103MAction?actId=90159&useLanguage=tw"
        self.assertEqual(m.canonical_detail(url, BASE),
                         "https://event.culture.tw/CKSMH/portal/Registration/C0103MAction?actId=90159")

    def test_dont_guess_details_without_bound_id(self):
        for bad in ("https://event.culture.tw/CKSMH",
                    "/mocweb/reg/CKSMH/Detail.init.ctr",
                    "/mocweb/reg/CKSMH/Detail.init.ctr?actId=abc",
                    "/mocweb/reg/CKSMH/Detail.init.ctr?actId=123&actId=1234",
                    "/mocweb/reg/OTHER/Detail.init.ctr?actId=12345",
                    "https://evil.com/mocweb/reg/CKSMH/Detail.init.ctr?actId=12345"):
            with self.subTest(url=bad):
                self.assertIsNone(m.canonical_detail(bad, BASE))

    def test_one_redirect_approved(self):
        sess = Session([Response(302, location="/mocweb/reg/CKSMH/Query.list.ctr"),
                        Response(200)])
        html, meta = m.get_html(sess, "https://event.culture.tw/CKSMH")
        self.assertEqual(meta["state"], "HTTP_OK")
        self.assertEqual(len(sess.urls), 2)
        self.assertEqual(html, LIST_HTML)
        self.assertEqual(len(meta["sha256"]), 64)

    def test_redirect_outside_official_blocked(self):
        sess = Session([Response(302, location="https://evil.tld/redirect")])
        html, meta = m.get_html(sess, BASE)
        self.assertIsNone(html)
        self.assertEqual(meta["state"], "URL_REJECTED")
        self.assertEqual(len(sess.urls), 1)

    def test_http_403_404_are_not_success(self):
        for status in (403, 404, 429):
            with self.subTest(status=status):
                sess = Session([Response(status)])
                html, meta = m.get_html(sess, BASE)
                self.assertIsNone(html)
                self.assertEqual(meta["http_status"], status)
                self.assertEqual(meta["state"], "HTTP_ERROR")

    def test_html_guard(self):
        for response, expected in ((Response(200, ct="application/json"), "NOT_HTML"),
                                   (Response(200, body=b""), "EMPTY_BODY"),
                                   (Response(200, body=b"X" * (m.MAX_HTML + 1)), "TOO_LARGE")):
            html, meta = m.get_html(Session([response]), BASE)
            self.assertIsNone(html)
            self.assertEqual(meta["state"], expected)

    def test_pipeline_two_list_one_detail_no_writer(self):
        sess = Session([Response(200), Response(200, body=b"<html></html>"),
                        Response(200, body=b"<html>one detail</html>")])
        with patch.object(m.time, "sleep", return_value=None) as delay:
            events, report = m.run(sess, delay=1.0)
        self.assertEqual(len(sess.urls), 3)
        self.assertEqual(len(events), 1)
        self.assertEqual(report["unique_list_candidates"], 1)
        self.assertEqual(report["detail_sample"]["state"], "DETAIL_HTTP_OK")
        self.assertEqual(report["http_ok_entries"], 2)
        self.assertEqual(report["list_nonempty_entries"], 1)
        self.assertFalse(report["writer_executed"])
        self.assertFalse(report["notification_executed"])
        self.assertFalse(report["app_data_published"])
        self.assertEqual(delay.call_count, 2)

    def test_all_blocked_reports_hold_without_detail(self):
        sess = Session([Response(403), Response(404)])
        with patch.object(m.time, "sleep", return_value=None):
            records, report = m.run(sess)
        self.assertEqual(len(sess.urls), 2)
        self.assertEqual(records, [])
        self.assertEqual(report["unique_list_candidates"], 0)
        self.assertEqual(report["detail_sample"]["state"], "NOT_ATTEMPTED")

    def test_rate_budget_guard(self):
        with self.assertRaisesRegex(ValueError, "RATE_LIMIT"):
            m.run(Session([]), delay=0)


if __name__ == "__main__":
    unittest.main()

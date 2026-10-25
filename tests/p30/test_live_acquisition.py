"""P30 offline safety and extraction tests: never contact public activity sites."""
import argparse
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "p30_live_acquisition.py"
spec = importlib.util.spec_from_file_location("p30_live_acquisition", SCRIPT)
p30 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p30)


class Response:
    def __init__(self, status, content=b"", content_type="text/html; charset=utf-8", location=None):
        self.status_code = status
        self._payload = content
        self.headers = {"content-type": content_type}
        if location is not None:
            self.headers["Location"] = location

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, chunk_size=32768):
        yield self._payload


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.headers = {}
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        assert kwargs["allow_redirects"] is False
        assert kwargs["stream"] is True
        return next(self.responses)

    def close(self):
        pass


class P30Tests(unittest.TestCase):
    def test_url_allowlist(self):
        hosts = ("example.com",)
        self.assertTrue(p30.allowed("https://events.example.com/x?id=5", hosts))
        for url in ("http://example.com/", "https://evil.com/",
                    "https://example.com@evil.com/", "https://example.com:8443/",
                    "file:///tmp/private", "https://127.0.0.1/"):
            self.assertFalse(p30.allowed(url, hosts), url)

    def test_redirect_to_foreign_domain_fails_closed(self):
        session = Session([Response(302, location="https://evil.test/steal")])
        html, report = p30.get_html(session, "https://example.com/list", ("example.com",), 6)
        self.assertIsNone(html)
        self.assertEqual(report["status"], "URL_NOT_ALLOWLISTED")
        self.assertEqual(len(session.urls), 1)

    def test_http_block_is_not_success(self):
        session = Session([Response(403)])
        html, report = p30.get_html(session, "https://example.com/list", ("example.com",), 6)
        self.assertIsNone(html)
        self.assertEqual(report["status"], "HTTP_ERROR")
        self.assertEqual(report["http_status"], 403)

    def test_parse_list_dedup_and_noise(self):
        html = """<a href="/event/123"><h3>城市音樂會</h3></a>
            <a href="/event/123">城市音樂會</a>
            <a href="https://evil.com/event/999">其他活動</a>
            <a href="/event/55">購票</a>"""
        events, anchors = p30.parse_list(html, "示範", "https://example.com/list",
                                         ("example.com",), r"/event/")
        self.assertEqual(anchors, 4)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["source_level"], "LIST_ONLY")
        self.assertIsNone(events[0]["date"])

    def test_detail_unverified_fields_remain_unknown(self):
        row = {"title": "公開活動", "date": None, "location": None, "price": None,
               "description": None, "ticket_availability": "UNKNOWN"}
        ev = p30.merge_detail(row, {"date": "2026-11-03",
                                     "source_identity_status": "UNBOUND_OR_MULTI_EVENT"})
        self.assertEqual(ev["date"], "2026-11-03")
        self.assertEqual(ev["ticket_availability"], "UNKNOWN")
        self.assertIsNone(ev["price"])
        self.assertEqual(ev["source_identity_status"], "UNBOUND_OR_MULTI_EVENT")

    def test_pipeline_stage_count_and_candidate(self):
        listing = b'<a href="/event/123">Test Concert 2026</a>'
        detail = (b'<script type="application/ld+json">'
                  b'{"@type":"Event","name":"Test Concert 2026",'
                  b'"startDate":"2026-11-03","url":"https://example.com/event/123"}'
                  b'</script>')
        session = Session([Response(200, listing), Response(200, detail)])
        args = argparse.Namespace(parser_file=None, platform_limit=1,
                                  detail_per_platform=1, timeout=6,
                                  min_interval=0.6, max_seconds=30)
        with patch.object(p30, "PLATFORMS",
                          (("Test", "https://example.com/list",
                            ("example.com",), r"/event/"),)):
            rows, report = p30.run(args, session=session,
                                   parser=lambda html, expected_url=None:
                                     {"date": "2026-11-03",
                                      "source_identity_status": "EXACT_JSONLD_EVENT_URL"},
                                   sleeper=lambda seconds: None)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["date"], "2026-11-03")
        self.assertEqual(report["counts"]["detail_http_ok"], 1)
        self.assertFalse(report["app_data_published"])
        self.assertFalse(report["writer_executed"])
        self.assertFalse(report["notification_executed"])
        self.assertEqual(report["platforms"][0]["stage4"], "FIELD_CANDIDATES")

    def test_no_unapproved_writer_imports(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("import scraper", "import show_news", "LINE_TOKEN", "TG_BOT_TOKEN",
                          "requests.post", "docs/data.json" + '").write'):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

"""P30-L3-A TWTC isolated, never-network, source/field negative matrix."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

filename = Path(__file__).resolve().parents[2] / "scripts" / "p30_l3a_twtc.py"
spec = importlib.util.spec_from_file_location("p30_l3a_twtc", filename)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

ROWS = """<html><table>
<tr><th>展出日期</th><th>展覽名稱</th><th>主辦</th><th>電話</th><th>館別</th></tr>
<tr><td>10/30 ~ 11/02</td>
<td><a href="https://www.art-taipei.com/">ART TAIPEI 2026台北國際藝術博覽會</a>
<a href="/exhibition_more.aspx?id=28519&p=home">more</a></td>
<td>畫廊協會</td><td>02-0000</td><td>世貿一館</td></tr>
<tr><td>10/30 ~ 11/02</td><td>ART TAIPEI 2026台北國際藝術博覽會
<a href="/exhibition_more.aspx?id=28519&p=home">more</a></td>
<td>畫廊協會</td><td>02-0000</td></tr>
<tr><td>延期未定</td><td>某展覽延期  <a href="/exhibition_more.aspx?id=33321">more</a></td>
<td>活動主辦</td><td></td><td>世貿一館</td></tr>
<tr><td>10/30 ~ 11/02</td><td>more</td><td>新聞</td><td></td><td></td></tr>
<tr><td>10/31 ~ 11/01</td><td>無詳情活動</td><td>來源協會</td><td></td><td>世貿一館</td></tr>
</table></html>""".encode("utf-8")
DETAIL = """<h2>ART TAIPEI 2026台北國際藝術博覽會</h2>
<p>展出日期：2026/10/30 ~ 2026/11/02</p>
<p>入場方式以主辦單位公告為準</p>""".encode("utf-8")


class Resp:
    def __init__(self, code=200, body=ROWS, ct="text/html;charset=utf-8", redirect=None):
        self.status_code = code
        self.body = body
        self.headers = {"content-type": ct}
        if redirect:
            self.headers["location"] = redirect

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, chunk_size=32768):
        yield self.body


class Session:
    def __init__(self, responses):
        self.results = iter(responses)
        self.urls = []

    def get(self, url, **kw):
        self.urls.append(url)
        assert kw["stream"] and kw["allow_redirects"] is False
        return next(self.results)


class Tests(unittest.TestCase):
    def test_url_allowlist(self):
        self.assertTrue(p.allowed(p.LISTING))
        self.assertTrue(p.allowed("https://twtc.com.tw/exhibition_more.aspx?id=28519"))
        for bad in ("http://twtc.com.tw/exhibition?p=home",
                    "https://twtc.com.tw.evil.com/exhibition",
                    "https://twtc.com.tw@evil.com/exhibition",
                    "https://twtc.com.tw:8080/exhibition",
                    "https://twtc.com.tw/exhibition/../admin",
                    "https://twtc.com.tw/news",
                    "https://127.0.0.1/exhibition"):
            with self.subTest(bad=bad):
                self.assertFalse(p.allowed(bad))

    def test_detail_identity_allowlist(self):
        from bs4 import BeautifulSoup
        cell = BeautifulSoup(
            '<td><a href="https://external.tld/exhibition_more.aspx?id=123">more</a>'
            '<a href="/exhibition_more.aspx?id=28519&p=home">more</a></td>', "html.parser").td
        self.assertEqual(p.detail_link(cell, p.LISTING),
                         "https://twtc.com.tw/exhibition_more.aspx?id=28519&p=home")

    def test_table_dedupe_title_date_and_postponement(self):
        out, diag = p.parse_list(ROWS)
        self.assertEqual(diag["list_candidates"], 3)
        a = out[0]
        self.assertIn("ART TAIPEI 2026", a["title"])
        self.assertEqual(a["event_period_raw"], "10/30 ~ 11/02")
        self.assertEqual(a["location"], "世貿一館")
        self.assertEqual(a["ticket_availability"], "UNKNOWN")
        self.assertIsNone(a["event_date_start"])
        self.assertEqual(out[1]["status"], "POSTPONED_UNCERTAIN")
        self.assertEqual(out[2]["official_url_role"], "TWTC_LISTING_FALLBACK")
        self.assertTrue(all(not r["golden_verified"] for r in out))

    def test_non_exhibition_navigation_rejected(self):
        out, diag = p.parse_list(b"<nav><a href='/news'>News</a></nav>")
        self.assertEqual(out, [])
        self.assertEqual(diag["table_rows_seen"], 0)

    def test_date_bound_and_full_year_only(self):
        good = p.parse_detail_date(DETAIL, "ART TAIPEI 2026台北國際藝術博覽會")
        self.assertEqual(good["state"], "DETAIL_DATE_CANDIDATE")
        self.assertEqual(good["start"], "2026-10-30")
        self.assertEqual(good["end"], "2026-11-02")
        self.assertEqual(p.parse_detail_date(DETAIL, "Other event")["state"],
                         "UNBOUND_DETAIL_TITLE")
        self.assertEqual(p.parse_detail_date(
            b"<h2>Event</h2><p>10/30 ~ 11/02</p>", "Event")["state"],
            "DATE_ABSENT_OR_AMBIGUOUS")

    def test_invalid_or_reversed_date_rejected(self):
        s = "<h3>Event</h3><p>展出日期：2026/12/29 ~ 2026/01/01</p>".encode()
        self.assertEqual(p.parse_detail_date(s, "Event")["state"], "INVERTED_DATE")
        s = "<h3>Event</h3><p>展出日期：2026/02/30 ~ 2026/03/02</p>".encode()
        self.assertEqual(p.parse_detail_date(s, "Event")["state"], "INVALID_DATE")

    def test_http_fail_and_foreign_redirect(self):
        for code in (403, 404, 429):
            html, meta = p.get_html(Session([Resp(code)]), p.LISTING)
            self.assertIsNone(html)
            self.assertEqual(meta["http_status"], code)
        sess = Session([Resp(302, redirect="https://evil.com/")])
        html, meta = p.get_html(sess, p.LISTING)
        self.assertIsNone(html)
        self.assertEqual(meta["state"], "URL_REJECTED")
        self.assertEqual(len(sess.urls), 1)

    def test_http_content_type_and_bounds(self):
        for resp, label in ((Resp(ct="application/json"), "NON_HTML"),
                            (Resp(body=b""), "EMPTY"),
                            (Resp(body=b"x" * (p.MAX_BYTES + 1)), "OVERSIZE")):
            html, meta = p.get_html(Session([resp]), p.LISTING)
            self.assertIsNone(html)
            self.assertEqual(meta["state"], label)

    def test_one_list_one_detail_and_candidate_date(self):
        sess = Session([Resp(body=ROWS), Resp(body=DETAIL)])
        with patch.object(p.time, "sleep", return_value=None) as wait:
            rows, evidence = p.run(sess)
        self.assertEqual(len(sess.urls), 2)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["event_date_start"], "2026-10-30")
        self.assertEqual(evidence["sample_detail"]["state"], "DETAIL_DATE_CANDIDATE")
        self.assertEqual(evidence["max_list_get"], 1)
        self.assertEqual(evidence["max_detail_get"], 1)
        self.assertFalse(evidence["app_data_published"])
        self.assertFalse(evidence["writer_executed"])
        self.assertEqual(wait.call_count, 1)

    def test_missing_listing_yields_hold_without_detail(self):
        sess = Session([Resp(404)])
        items, report = p.run(sess)
        self.assertEqual(items, [])
        self.assertEqual(len(sess.urls), 1)
        self.assertEqual(report["sample_detail"]["state"], "NOT_ATTEMPTED")

    def test_rate_budget(self):
        with self.assertRaisesRegex(ValueError, "RATE_LIMIT"):
            p.run(Session([]), delay=0.2)


if __name__ == "__main__":
    unittest.main()

"""Offline integration of the A full-stream and B prior-receipt gates."""
import hashlib
import io
import unittest
from datetime import datetime, timezone
from scripts import p30_source_stream_gate as m


class TestSourceStreamGate(unittest.TestCase):
    def setUp(self):
        self.clock = datetime.now(timezone.utc).isoformat()
        self.html = ('<main><section><h1>' + m.TITLE + '</h1>'
                     '<a href="' + m.TICKET_URL + '">購票去</a>'
                     '<p>臺北表演藝術中心 藍盒子</p></section></main>')
        self.large = ('<script>' + 'x' * 550000 + '</script>' + self.html).encode()

    def replay(self, raw, **overrides):
        params = dict(status=200, content_type="text/html; charset=utf-8",
                      final_url=m.TPAC_URL, observed_at_utc=self.clock)
        params.update(overrides)
        return m.inspect_tpac_complete_stream(io.BytesIO(raw), **params)

    def test_large_complete_body_has_real_full_hash_not_prefix(self):
        result = self.replay(self.large)
        self.assertEqual(result["decision"], "REVIEW_DIRECT_EDGE_ONLY", result)
        self.assertEqual(result["body_bytes"], len(self.large))
        self.assertEqual(result["body_sha256"], hashlib.sha256(self.large).hexdigest())
        self.assertFalse(result["body_truncated"])
        self.assertEqual(result["native_get_this_call"], 0)
        self.assertEqual(result["formal_accepted_fields"], 0)

    def test_bound_rejects_without_full_hash(self):
        result = self.replay(self.large, max_bytes=524289)
        self.assertEqual(result["decision"], "HOLD")
        self.assertEqual(result["first_failure"],
                         "TPAC_STREAM_COMPLETE_BODY_EXCEEDS_POLICY_HOLD")
        self.assertTrue(result["body_truncated"])
        self.assertNotIn("body_sha256", result)
        self.assertIn("prefix_sha256", result)

    def test_wrong_title_link_room_and_unscoped_header_hold(self):
        cases = [
            self.html.replace(m.TITLE, "其他活動"),
            self.html.replace(m.TICKET_URL, "https://www.opentix.life/event/0"),
            self.html.replace("藍盒子", "其他場館"),
            self.html.replace("<p>臺北表演藝術中心 藍盒子</p>",
                              "</section><section><p>臺北表演藝術中心 藍盒子</p>"),
            '<header><h1>' + m.TITLE + '</h1><a href="' + m.TICKET_URL +
            '">票</a></header><main><p>藍盒子</p></main>',
        ]
        for html in cases:
            with self.subTest(html=html[:30]):
                self.assertEqual(self.replay(html.encode())["decision"], "HOLD")

    def test_same_article_sibling_sections_are_event_local_review_only(self):
        # Actual source-root-cause hypothesis: title, ticket and room may be
        # separate child sections of one event article, not separate events.
        html = ('<main><article><section><h1>' + m.TITLE + '</h1></section>'
                '<section><a href="' + m.TICKET_URL + '">官方售票</a></section>'
                '<section><p>臺北表演藝術中心 藍盒子</p></section>'
                '</article></main>')
        result = self.replay(html.encode())
        self.assertEqual(result["decision"], "REVIEW_DIRECT_EDGE_ONLY", result)
        self.assertEqual(result["event_local_checks"]["shared_event_ancestor_kind"],
                         "article")
        self.assertEqual(result["native_get_this_call"], 0)
        self.assertEqual(result["formal_accepted_fields"], 0)

    def test_distinct_articles_never_share_identity_through_parent_section(self):
        html = ('<main><section><article><h1>' + m.TITLE + '</h1></article>'
                '<article><a href="' + m.TICKET_URL + '">票</a>'
                '<p>藍盒子</p></article></section></main>')
        result = self.replay(html.encode())
        self.assertEqual(result["decision"], "HOLD")
        self.assertFalse(result["event_local_checks"]["article_ancestor_parity"])
        self.assertFalse(result["event_local_checks"]["same_section_identity"])

    def test_transport_and_encoding_fail_closed(self):
        for options in ({"status": 302},
                        {"final_url": "https://example.org/"},
                        {"content_type": "application/json"},
                        {"content_type": "text/html; charset=big5"}):
            with self.subTest(options=options):
                self.assertEqual(self.replay(self.html.encode(), **options)["decision"],
                                 "HOLD")
        self.assertEqual(self.replay(bytes([255, 254]))["decision"], "HOLD")

    def test_songshan_historical_receipts_do_not_upgrade_identity(self):
        evidence = {
            "target_uuid": m.SONGSHAN_UUID, "same_uuid_review_lkg": 0,
            "persisted": False, "native_get_200_count": 2,
            "reason": "SONGSHAN_DETAIL_EXACT_HEADING_HOLD:h1=0,h2=0,h3=0",
            "source_receipts": [
                {"url": m.SONGSHAN_LIST, "http_status": 200, "bytes": 34242,
                 "body_sha256": "de3df20bcd78e264c7f0eff8bafedbeb39aa580d7892e738bb2eb792c68e33cb",
                 "transport": "BUILTIN_NATIVE_GET"},
                {"url": m.SONGSHAN_DETAIL, "http_status": 200, "bytes": 26506,
                 "body_sha256": "1226b2f61dd328c08a2ff456e4f36dcc20dd23ce9d18219e377bafa4d404e02d",
                 "transport": "BUILTIN_NATIVE_GET"},
            ],
        }
        out = m.audit_songshan_prior_native_receipt(evidence)
        self.assertEqual(out["decision"],
                         "PRIOR_NATIVE_HTTP_CONFIRMED_IDENTITY_STILL_HOLD")
        self.assertEqual(out["replayed_prior_http200"], 2)
        self.assertEqual(out["native_get_this_call"], 0)
        self.assertEqual(out["native_same_uuid_lkg_new"], 0)
        evidence["source_receipts"][1]["body_sha256"] = "invalid"
        self.assertEqual(m.audit_songshan_prior_native_receipt(evidence)["decision"],
                         "HOLD")


    def test_native_single_get_complete_body_and_no_checkout(self):
        from unittest.mock import patch
        class Response(io.BytesIO):
            status = 200
            headers = {"Content-Type": "text/html; charset=utf-8"}
            def geturl(self):
                return m.TPAC_URL
        class Opener:
            calls = 0
            def open(self, req, timeout):
                self.calls += 1
                self.url = req.full_url
                self.timeout = timeout
                return Response(self_payload)
        self_payload = self.large
        opener = Opener()
        with patch("urllib.request.build_opener", return_value=opener):
            result = m.acquire_tpac_native_once()
        self.assertEqual(opener.calls, 1)
        self.assertEqual(opener.url, m.TPAC_URL)
        self.assertEqual(opener.timeout, 8)
        self.assertEqual(result["native_http200_this_call"], 1)
        self.assertEqual(result["body_sha256"], hashlib.sha256(self.large).hexdigest())
        self.assertEqual(result["decision"], "REVIEW_DIRECT_EDGE_ONLY")
        self.assertEqual(result["native_same_id_lkg"], 0)
        self.assertEqual(result["formal_accepted_fields"], 0)
        self.assertEqual(result["published_events"], 0)

    def test_native_one_shot_http_redirect_is_not_followed(self):
        import urllib.error
        from unittest.mock import patch
        class Opener:
            calls = 0
            def open(self, req, timeout):
                self.calls += 1
                raise urllib.error.HTTPError(req.full_url, 302, "redirect", {}, None)
        opener = Opener()
        with patch("urllib.request.build_opener", return_value=opener):
            result = m.acquire_tpac_native_once()
        self.assertEqual(opener.calls, 1)
        self.assertEqual(result["first_failure"], "TPAC_REDIRECT_BLOCKED_HOLD")
        self.assertEqual(result["native_http200_this_call"], 0)
        self.assertNotIn("body_sha256", result)



    def test_a_b_manifest_replay_exact_id_and_checksum(self):
        import tempfile
        import json
        from pathlib import Path
        from scripts.p30_l7_field_golden_readiness import (
            OPENTIX_ROTATION_LIST, OPENTIX_ROTATION_DETAIL, OPENTIX_ROTATION_TITLE,
            load_isolated_review_lkg)
        cases = (
            ("A", (OPENTIX_ROTATION_LIST, OPENTIX_ROTATION_DETAIL),
             OPENTIX_ROTATION_TITLE, "05:2072516129034670080"),
            ("B", (m.SONGSHAN_LIST, m.SONGSHAN_DETAIL),
             "STAR ON THE MOVE 2026 臺北採購媒合與展售會",
             "14:" + m.SONGSHAN_UUID),
        )
        for line, urls, title, identity in cases:
            with self.subTest(line=line), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                list_html = '<main><div><a href="' + urls[1] + '">' + title + '</a></div></main>'
                detail_html = '<main><h1>' + title + '</h1>' + (
                    '<p data-role="venue">臺北表演藝術中心 藍盒子</p>' if line == "A" else ""
                ) + '</main>'
                stamp = datetime.now(timezone.utc).replace(microsecond=0)
                sources = []
                for i, (url, html) in enumerate(zip(urls, (list_html, detail_html))):
                    path = root / (str(i) + ".html")
                    raw = html.encode()
                    path.write_bytes(raw)
                    sources.append(dict(url=url, path=str(path),
                                        sha256=hashlib.sha256(raw).hexdigest(),
                                        observed_at_utc=stamp.isoformat()))
                manifest = root / "manifest.json"
                manifest.write_text(json.dumps(dict(
                    kind="P30_PREACQUIRED_OFFICIAL_HTML_V1",
                    transport="CALLER_SUPPLIED_NOT_NATIVE_ATTESTED",
                    sources=sources)), encoding="utf-8")
                output = root / "review_lkg_snapshot.json"
                result = m.replay_preacquired_ab_to_review_lkg(
                    line, manifest, output, Path.cwd(), now_utc=stamp)
                self.assertEqual(result["decision"], "REVIEW_ONLY_NONPUBLISHING", result)
                self.assertEqual(result["native_get_this_call"], 0)
                snap = load_isolated_review_lkg(output, Path.cwd())
                self.assertEqual(snap["rows"][0]["_candidate"]["record_id"], identity)
                self.assertEqual(snap["rows"][0]["scraped_at"], stamp.isoformat())
                before = output.read_bytes()
                sources[1]["sha256"] = "0" * 64
                manifest.write_text(json.dumps(dict(
                    kind="P30_PREACQUIRED_OFFICIAL_HTML_V1",
                    transport="CALLER_SUPPLIED_NOT_NATIVE_ATTESTED",
                    sources=sources)), encoding="utf-8")
                self.assertEqual(m.replay_preacquired_ab_to_review_lkg(
                    line, manifest, output, Path.cwd(), now_utc=stamp)["decision"], "HOLD")
                self.assertEqual(output.read_bytes(), before)



    def test_zepp_exact_rid_same_anchor_and_detail_heading(self):
        from unittest.mock import patch
        listing = ('<main><a href="/hall/newtaipei/schedule/single/?rid=166457">'
                   'Jony J 2026「本命」TOUR IN TAIPEI</a></main>').encode()
        detail = ('<main><h2>Jony J 2026「本命」TOUR IN TAIPEI</h2>'
                  '<p>2026/11/6 START 20:00</p></main>').encode()
        class Response(io.BytesIO):
            status = 200
            headers = {"Content-Type": "text/html; charset=UTF-8"}
            def __init__(self, raw, url):
                super().__init__(raw)
                self.url = url
            def geturl(self):
                return self.url
        class Opener:
            def __init__(self):
                self.urls = []
            def open(self, req, timeout):
                self.urls.append(req.full_url)
                assert timeout == 8
                if req.full_url.endswith("/robots.txt"):
                    import urllib.error
                    raise urllib.error.HTTPError(req.full_url, 404,
                                                 "not found", {}, None)
                return Response((listing, detail)[len(self.urls)-2],
                                req.full_url)
        opener = Opener()
        with patch("urllib.request.build_opener", return_value=opener):
            result = m.probe_zepp_newtaipei_native_once()
        self.assertEqual(opener.urls, ["https://www.zepp.co.jp/robots.txt",
                                       m.ZEPP_LIST, m.ZEPP_DETAIL])
        self.assertEqual(result["policy_decision"], "ALLOW_ROBOTS_404")
        self.assertEqual(result["native_http200"], 2)
        self.assertEqual(result["native_same_id_review"], 1)
        self.assertEqual(result["same_id_review_lkg"], 0)
        self.assertEqual(result["decision"], "REVIEW_NATIVE_SAME_ID_ONLY")
        self.assertEqual(result["formal_accepted_fields"], 0)
        self.assertEqual(result["published_events"], 0)
        self.assertFalse(result["raw_html_saved"])
        self.assertEqual(result["source_receipts"][1]["body_sha256"],
                         hashlib.sha256(detail).hexdigest())

    def test_zepp_cross_card_or_unscoped_title_does_not_make_identity(self):
        listing = ('<main><a href="/hall/newtaipei/schedule/single/?rid=166457">'
                   'READ MORE</a><h2>Jony J 2026「本命」TOUR IN TAIPEI'
                   '</h2></main>').encode()
        detail = ('<main><h2>Jony J 2026「本命」TOUR IN TAIPEI'
                  '</h2></main>').encode()
        with self.assertRaisesRegex(ValueError, "ZEPP_LIST_EXACT_RID_TITLE_EDGE_HOLD"):
            m.inspect_zepp_same_id_pages(listing, detail)
        good_list = ('<a href="/hall/newtaipei/schedule/single/?rid=166457">'
                     'Jony J 2026「本命」TOUR IN TAIPEI</a>').encode()
        with self.assertRaisesRegex(ValueError, "ZEPP_DETAIL_EVENT_LOCAL_HEADING_HOLD"):
            m.inspect_zepp_same_id_pages(good_list, b"<p>unrelated event</p>")

    def test_zepp_redirect_stops_before_detail(self):
        import urllib.error
        from unittest.mock import patch
        class Opener:
            def __init__(self):
                self.calls = 0
            def open(self, req, timeout):
                self.calls += 1
                raise urllib.error.HTTPError(req.full_url, 302,
                                             "redirect", {}, None)
        opener = Opener()
        with patch("urllib.request.build_opener", return_value=opener):
            result = m.probe_zepp_newtaipei_native_once()
        self.assertEqual(opener.calls, 1)
        self.assertEqual(result["native_get_attempted"], 0)
        self.assertEqual(result["policy_get_attempted"], 1)
        self.assertEqual(result["native_http200"], 0)
        self.assertIn("ZEPP_SITE_POLICY_HOLD", result["first_failure"])
        self.assertEqual(result["source_receipts"], [])


if __name__ == "__main__":
    unittest.main()

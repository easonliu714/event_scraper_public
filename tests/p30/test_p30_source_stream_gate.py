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



    def test_zepp_official_schedule_is_list_authority_not_home(self):
        # Indexed official schedule carries the exact rid event card.
        # Venue home is discovery only; this is NOT a native GET receipt.
        self.assertEqual(m.ZEPP_LIST,
                         "https://www.zepp.co.jp/hall/newtaipei/schedule/")
        self.assertNotEqual(m.ZEPP_LIST,
                            "https://www.zepp.co.jp/hall/newtaipei/")
        self.assertEqual(m.ZEPP_DETAIL,
                         "https://www.zepp.co.jp/hall/newtaipei/schedule/single/?rid=166457")

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


    def test_zepp_parser_reuses_same_adapter_for_new_exact_rid(self):
        # A second official venue schedule ID must not require another adapter.
        # These are synthetic bytes; no native provenance is implied.
        title = "Another source-owned venue event"
        detail_url = ("https://www.zepp.co.jp/hall/newtaipei/"
                      "schedule/single/?rid=166458")
        listing = ('<main><a href="' + detail_url + '">2026 11.7 ' +
                   title + ' READ MORE</a></main>').encode()
        detail = ('<main><h2>' + title + '</h2></main>').encode()
        checks = m.inspect_zepp_same_id_pages(
            listing, detail, detail_url=detail_url, expected_title=title)
        self.assertEqual(checks["exact_rid"], "166458")
        self.assertEqual(checks["source_key"], m.ZEPP_SOURCE_KEY)
        self.assertEqual(checks["formal_accepted_fields"], 0)
        self.assertEqual(checks["date_role"], "UNVERIFIED_NOT_SESSION")
        with self.assertRaisesRegex(ValueError, "ZEPP_LIST_EXACT_RID_TITLE_EDGE_HOLD"):
            m.inspect_zepp_same_id_pages(
                listing, detail, detail_url=m.ZEPP_DETAIL, expected_title=title)

    def test_zepp_exact_url_rejects_query_duplicates_and_foreign_host(self):
        listing = ('<main><a href="' + m.ZEPP_DETAIL + '">' +
                   m.ZEPP_TITLE + '</a></main>').encode()
        detail = ('<main><h2>' + m.ZEPP_TITLE + '</h2></main>').encode()
        invalid = (
            m.ZEPP_DETAIL + '&rid=166458',
            m.ZEPP_DETAIL + '&tracking=1',
            m.ZEPP_DETAIL.replace("www.zepp.co.jp", "example.org"),
            m.ZEPP_DETAIL.replace("rid=166457", "rid=0"),
            m.ZEPP_DETAIL + '#fragment',
        )
        for url in invalid:
            with self.subTest(url=url), self.assertRaisesRegex(
                    ValueError, "ZEPP_TARGET_"):
                m.inspect_zepp_same_id_pages(
                    listing, detail, detail_url=url)

    def test_zepp_global_footer_heading_never_attests_detail_identity(self):
        listing = ('<main><a href="' + m.ZEPP_DETAIL + '">' +
                   m.ZEPP_TITLE + '</a></main>').encode()
        # Matching heading outside MAIN is not source-local event identity.
        detail = ('<main><p>Unrelated activity</p></main>'
                  '<footer><h2>' + m.ZEPP_TITLE + '</h2></footer>').encode()
        with self.assertRaisesRegex(ValueError, "ZEPP_DETAIL_EVENT_LOCAL_HEADING_HOLD"):
            m.inspect_zepp_same_id_pages(listing, detail)




    def test_opentix_new_native_detail_only_no_list_or_formal(self):
        import urllib.error
        from unittest.mock import patch
        html = ('<header><h1>' + m.OPENTIX_FRESH_TITLE + '</h1></header>'
                '<main><h1>' + m.OPENTIX_FRESH_TITLE + '</h1></main>').encode()
        class Response(io.BytesIO):
            status = 200
            headers = {"Content-Type": "text/html; charset=utf-8"}
            def __init__(self, url, raw):
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
                    raise urllib.error.HTTPError(req.full_url, 404, "not found", {}, None)
                return Response(req.full_url, html)
        opener = Opener()
        with patch("urllib.request.build_opener", return_value=opener):
            out = m.probe_opentix_fresh_detail_native_once()
        self.assertEqual(opener.urls, ["https://www.opentix.life/robots.txt",
                                       m.OPENTIX_FRESH_DETAIL])
        self.assertEqual(out["native_http200"], 1)
        self.assertEqual(out["decision"], "REVIEW_NATIVE_DETAIL_ONLY")
        self.assertEqual(out["body_sha256"], hashlib.sha256(html).hexdigest())
        self.assertEqual(out["detail_checks"]["exact_main_heading_count"], 1)
        self.assertFalse(out["detail_checks"]["list_same_id_edge_attested"])
        self.assertEqual(out["native_same_id_review_lkg"], 0)
        self.assertEqual(out["formal_accepted_fields"], 0)
        self.assertEqual(out["golden_accepted_events"], 0)
        self.assertEqual(out["published_events"], 0)
        self.assertFalse(out["raw_html_saved"])

    def test_opentix_global_heading_and_robots_disallow_hold(self):
        from unittest.mock import patch
        global_only = ('<header><h1>' + m.OPENTIX_FRESH_TITLE +
                       '</h1></header><main><p>other event</p></main>').encode()
        self.assertFalse(m.inspect_opentix_fresh_detail_body(
            global_only)["event_local_title_review"])
        with self.assertRaisesRegex(ValueError, "OPENTIX_FRESH_BODY_BOUND_HOLD"):
            m.inspect_opentix_fresh_detail_body(b"")
        class Response(io.BytesIO):
            status = 200
            headers = {"Content-Type": "text/plain"}
            def geturl(self):
                return "https://www.opentix.life/robots.txt"
        class Opener:
            calls = 0
            def open(self, req, timeout):
                self.calls += 1
                return Response(b"User-agent: *\nDisallow: /event/\n")
        opener = Opener()
        with patch("urllib.request.build_opener", return_value=opener):
            out = m.probe_opentix_fresh_detail_native_once()
        self.assertEqual(opener.calls, 1)
        self.assertEqual(out["native_get_attempted"], 0)
        self.assertEqual(out["decision"], "HOLD")
        self.assertIn("OPENTIX_ROBOTS_DISALLOW_HOLD", out["first_failure"])

    def test_zepp_prior_native_receipt_not_raw_html_replay(self):
        # Historical 2/2 receipt has SHA/time but no replayable body.
        self.assertEqual(m.ZEPP_SOURCE_KEY, "venue:zepp-newtaipei")
        self.assertEqual(m.ZEPP_DETAIL.split("rid=")[1], "166457")


    def _zepp_synthetic_archive(self, *, source_event_id="166457",
                                include_receipt=True):
        # Synthetic archive is NOT the pinned historical CI artifact.
        import zipfile
        receipt = {
            "kind": "P30_B_ZEPP_NEWTIPEI_NATIVE_SAME_ID_ONESHOT_V1",
            "line": "B", "source_key": m.ZEPP_SOURCE_KEY,
            "source_event_id": source_event_id,
            "policy_decision": "ALLOW_ROBOTS_200",
            "native_get_attempted": 2, "native_http200": 2,
            "native_list_get_attempted": 1,
            "native_detail_get_attempted": 1,
            "native_same_id_review": 1, "same_id_review_lkg": 0,
            "decision": "REVIEW_NATIVE_SAME_ID_ONLY",
            "raw_html_saved": False, "formal_accepted_fields": 0,
            "golden_accepted_events": 0, "published_events": 0,
            "release_state": "HARD_HOLD_NO_PUBLICATION",
            "identity_checks": {
                "exact_rid": "166457", "title": m.ZEPP_TITLE,
                "source_key": m.ZEPP_SOURCE_KEY,
                "list_exact_edge_count": 1,
                "detail_exact_heading_count": 1,
                "date_role": "UNVERIFIED_NOT_SESSION",
                "start_role": "UNVERIFIED_NOT_SESSION"},
            "source_receipts": [
                {"url": m.ZEPP_LIST, "body_bytes_read": 343607,
                 "body_sha256": "1632f6235bc4a9365c2569697e50f2612e4165dfabee16bc4134f6fddbd497bf",
                 "http_status": 200, "observed_at_utc": "2026-11-05T18:00:18.824848Z",
                 "transport": "BUILTIN_NATIVE_GET_NO_REDIRECT_NO_RETRY"},
                {"url": m.ZEPP_DETAIL, "body_bytes_read": 310512,
                 "body_sha256": "66750b7e3f39e7ec84c4de2b630517b9c39d4171bc305d7c0f7ca72e732aa67d",
                 "http_status": 200, "observed_at_utc": "2026-11-05T18:00:20.983747Z",
                 "transport": "BUILTIN_NATIVE_GET_NO_REDIRECT_NO_RETRY"}]}
        payload = {
            "readiness.txt": b"offline only",
            "field_subset_review_proposal.json": b"{}",
            "tmc_field_authority_contract.json": b"{}",
            "canonical_field_authority_contract.json": b"{}"}
        if include_receipt:
            payload["zepp_newtaipei_native_once.json"] = json.dumps(
                receipt, ensure_ascii=False).encode()
        entries = [
            hashlib.sha256(b).hexdigest() + "  evidence/" + name
            for name, b in payload.items()]
        entries += [
            "0" * 64 + "  " + name for name in (
                ".github/workflows/eventradar_p30_l7_field_readiness.yml",
                "scripts/p30_l7_field_golden_readiness.py",
                "scripts/p30_source_stream_gate.py",
                "tests/p30/test_p30_l7_field_golden_readiness.py",
                "tests/p30/test_p30_source_stream_gate.py",
                "tests/p30/fixtures/p30_l7_prince_field_readiness.json")]
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as z:
            for name, body in payload.items():
                z.writestr(name, body)
            z.writestr("SHA256SUMS.txt", "\n".join(entries) + "\n")
        return stream.getvalue()

    def test_zepp_receipt_archive_sealed_identity_not_body_lkg(self):
        archive = self._zepp_synthetic_archive()
        snapshot = m.audit_zepp_sealed_receipt_archive(
            archive, hashlib.sha256(archive).hexdigest())
        self.assertEqual(snapshot["receipt_only_identity_lkg"], 1)
        self.assertEqual(snapshot["same_id_review_lkg"], 0)
        self.assertEqual(snapshot["native_get_this_call"], 0)
        self.assertEqual(snapshot["historical_native_http200"], 2)
        self.assertEqual(snapshot["formal_accepted_fields"], 0)
        self.assertFalse(snapshot["raw_html_saved"])
        self.assertEqual(snapshot["release_state"], "HARD_HOLD_NO_PUBLICATION")
        with self.assertRaisesRegex(ValueError, "ZEPP_ARTIFACT_EXACT_SHA_HOLD"):
            m.audit_zepp_sealed_receipt_archive(archive, "0" * 64)

    def test_zepp_receipt_archive_rejects_wrong_identity_and_missing_member(self):
        for archive in (self._zepp_synthetic_archive(source_event_id="166458"),
                        self._zepp_synthetic_archive(include_receipt=False)):
            with self.subTest(archive_size=len(archive)):
                with self.assertRaisesRegex(ValueError, "ZEPP_"):
                    m.audit_zepp_sealed_receipt_archive(
                        archive, hashlib.sha256(archive).hexdigest())

    def test_zepp_receipt_durable_handoff_requires_pinned_real_artifact(self):
        import tempfile
        from pathlib import Path
        archive = self._zepp_synthetic_archive()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            root.mkdir()
            isolated = Path(td) / "isolated"
            isolated.mkdir()
            target = isolated / "zepp_receipt_identity_lkg.json"
            with self.assertRaisesRegex(ValueError, "ZEPP_ARTIFACT_EXACT_SHA_HOLD"):
                m.persist_zepp_receipt_identity_lkg(archive, target, root)
            self.assertFalse(target.exists())
            with self.assertRaisesRegex(ValueError, "ZEPP_RECEIPT_REPOSITORY_PATH_HOLD"):
                m.persist_zepp_receipt_identity_lkg(
                    archive, root / "zepp_receipt_identity_lkg.json", root)


if __name__ == "__main__":
    unittest.main()

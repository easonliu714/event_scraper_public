"""A/B source rotation: no network in unit tests, no publication."""
import unittest
from unittest.mock import Mock
from scripts import p30_dual_native_rotation as m
from scripts import p30_ntpc_artcenter_source as b


class TestRotation(unittest.TestCase):
    def test_a_same_id_review(self):
        listing = '<main><a href="' + m.FAMI_DETAIL + '">' + m.FAMI_TITLE + '</a></main>'
        detail = '<main><article><h1>' + m.FAMI_TITLE + '</h1></article></main>'
        r = m.inspect_pair("A", listing, detail)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(r["formal_accepted_fields"], 0)
        self.assertEqual(r["field_review"], 1)

    def test_a_alt_identity(self):
        listing = '<main><a href="' + m.FAMI_DETAIL + '"><img alt="' + m.FAMI_TITLE + '"></a></main>'
        detail = '<main><h2>' + m.FAMI_TITLE + '</h2></main>'
        self.assertEqual(m.inspect_pair("A", listing, detail)["same_id_review"], 1)

    def test_a_wrong_identity_and_no_checkout(self):
        listing = '<main><a href="' + m.FAMI_DETAIL + '">' + m.FAMI_TITLE + '</a></main>'
        detail = '<main><h1>' + m.FAMI_TITLE + '</h1></main>'
        for bad in (m.FAMI_DETAIL + "/checkout", m.FAMI_DETAIL + "?session=1",
                    "https://evil.example" + m.FAMI_DETAIL.split(".tw")[-1]):
            self.assertIsNone(m.fami_exact_link(bad))
        self.assertEqual(m.inspect_pair("A", listing.replace(m.FAMI_DETAIL, "https://evil.example/"), detail)["same_id_review"], 0)
        self.assertEqual(m.inspect_pair("A", listing, "<header><h1>" + m.FAMI_TITLE + "</h1></header>")["same_id_review"], 0)

    def test_b_same_sid_venue(self):
        url = "/artcenter_chi/xmdoc/cont?sid=" + b.SID + "&sq=&xsmsid=" + b.XSMSID
        listing = '<main><a href="' + url + '">' + b.TITLE + '</a></main>'
        detail = '<main><article><h3>' + b.TITLE + '</h3><p>展覽地點：' + b.VENUE + '</p></article></main>'
        r = m.inspect_pair("B", listing, detail)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(r["field_review"], 2)
        self.assertEqual(r["formal_accepted_fields"], 0)

    def test_b_no_cross_source_or_bulletin_date(self):
        url = "/artcenter_chi/xmdoc/cont?sid=" + b.SID + "&sq=&xsmsid=" + b.XSMSID
        listing = '<main><a href="' + url + '">' + b.TITLE + '</a></main>'
        detail = '<main><article><h3>' + b.TITLE + '</h3><p>展覽地點：' + b.VENUE + '</p></article></main>'
        self.assertEqual(m.inspect_pair("B", listing, detail.replace(b.VENUE, "其他展覽室"))["same_id_review"], 0)
        self.assertEqual(m.inspect_pair("B", listing.replace(b.SID, "bad"), detail)["same_id_review"], 0)
        self.assertEqual(m.inspect_pair("B", listing, "<header><h3>" + b.TITLE + "</h3></header>")["same_id_review"], 0)

    def test_robots_html_home_fallback_is_not_allow(self):
        # Prior native FamiTicket robots.txt and HOME had the same 193376-byte SHA.
        class FakeResponse:
            status = 200
            headers = {"Content-Type": "text/html; charset=utf-8"}
            def geturl(self): return "https://www.famiticket.com.tw/robots.txt"
            def read(self, n): return b"<html><head></head><body>HOME</body></html>"
            def __enter__(self): return self
            def __exit__(self, *args): return False
        opener = Mock()
        opener.open.return_value = FakeResponse()
        with self.assertRaisesRegex(ValueError, "ROTATION_ROBOTS_MIME_HOLD"):
            m.read_public(opener, "https://www.famiticket.com.tw/robots.txt", "text/plain")

    def test_html_media_is_not_robots_and_vice_versa(self):
        class FakeResponse:
            status = 200
            headers = {"Content-Type": "text/plain"}
            def geturl(self): return m.FAMI_LIST
            def read(self, n): return b"User-agent: *\\nDisallow: /checkout\\n"
            def __enter__(self): return self
            def __exit__(self, *args): return False
        opener = Mock()
        opener.open.return_value = FakeResponse()
        with self.assertRaisesRegex(ValueError, "ROTATION_HTML_MIME_HOLD"):
            m.read_public(opener, m.FAMI_LIST, "text/html")

    def test_no_unsupported_line(self):
        with self.assertRaises(ValueError):
            m.inspect_pair("C", "", "")
        with self.assertRaises(ValueError):
            m.run_native_once("C")



class TestDistinctNext(unittest.TestCase):
    def pair(self,line):
        c=m.NEXT[line]
        return ('<main><article><a href="'+c["detail"]+'">'+c["title"]+'</a></article></main>',
                '<main><article><h1>'+c["title"]+'</h1><p>'+c["venue"]+'</p></article></main>')

    def test_exact_a_b_identity_and_review_only(self):
        for line in "AB":
            l,d=self.pair(line)
            result=m.inspect_next_pair(line,l,d)
            self.assertEqual(result["identity"],1)
            self.assertEqual(result["fields"],2)
            self.assertEqual(result["decision"],"REVIEW_NON_SESSION_ONLY")

    def test_wrong_host_query_fragment_checkout(self):
        for line in "AB":
            u=m.NEXT[line]["detail"]
            self.assertEqual(m.exact_next_href(line,u),u)
            for bad in (u+"#x",u+"?checkout=1" if line=="A" else u+"&checkout=1",
                        u.replace("https://","http://"),u.replace("https://","https://evil.example@")):
                self.assertIsNone(m.exact_next_href(line,bad))

    def test_title_venue_and_heading_scope_hold(self):
        for line in "AB":
            l,d=self.pair(line)
            c=m.NEXT[line]
            self.assertEqual(m.inspect_next_pair(line,l.replace(c["title"],"WRONG"),d)["identity"],0)
            self.assertEqual(m.inspect_next_pair(line,l,d.replace("<main><article>","<header>").replace("</article></main>","</header>"))["identity"],0)
            self.assertEqual(m.inspect_next_pair(line,l,d.replace("<p>"+c["venue"]+"</p>",""))["fields"],1)

    def test_cross_event_sibling_article_venue_cannot_promote(self):
        # One exact title cannot borrow the venue from an unrelated event.
        for line in "AB":
            cfg = m.NEXT[line]
            listing, _ = self.pair(line)
            foreign = ('<main><article><h1>' + cfg["title"] +
                       '</h1></article><article><h1>UNRELATED EVENT</h1><p>' +
                       cfg["venue"] + '</p></article></main>')
            result = m.inspect_next_pair(line, listing, foreign)
            self.assertEqual(result["decision"], "HOLD")
            self.assertEqual(result["reason"], "NEXT_EVENT_LOCAL_VENUE_HOLD")
            self.assertEqual(result["fields"], 1)
            owned = ('<main><article><section><h1>' + cfg["title"] +
                     '</h1></section><section><p>' + cfg["venue"] +
                     '</p></section></article></main>')
            self.assertEqual(m.inspect_next_pair(line, listing, owned)["fields"], 2)

    def test_zepp_official_event_date_start_vs_sale_role_diagnostics(self):
        # Indexed official rid=167511 shows 11/27 START 19:30, but 7/25 is
        # a sale-start date, never a performance date or KKTIX Session.
        listing, _ = self.pair("B")
        cfg = m.NEXT["B"]
        def detail(show="2026.11.27 (五) 19:30",
                   start="[START] 19:30",
                   sale="2026.7.25 (六) 下午13:00"):
            return ('<main><article><h1>' + cfg["title"] +
                    '</h1><p>' + cfg["venue"] +
                    '</p><p>時間 ' + start + '</p><p>日期｜' + show +
                    '</p><p>開賣時間｜' + sale + '</p></article></main>')
        positive = m.inspect_next_pair("B", listing, detail())
        self.assertEqual(positive["decision"], "REVIEW_NON_SESSION_ONLY")
        self.assertEqual(positive["fields"], 2)  # immutable native receipt roles
        diag = positive["event_local_role_diagnostics"]
        self.assertEqual(diag["decision"], "REVIEW_ONLY")
        self.assertEqual(diag["event_date_review"], "2026-11-27")
        self.assertEqual(diag["start_local_review"], "19:30")
        self.assertEqual(diag["sale_date_diagnostic"], "2026-07-25")
        self.assertFalse(diag["sale_date_is_event_date"])
        self.assertFalse(diag["formal_accepted"])
        for html in (
            detail(start="OPEN 18:30"),
            detail(start="[START] 20:30"),
            detail(show="2026.11.28 (六) 19:30"),
            detail(sale="2026.11.27 (五) 下午13:00"),
            detail(sale=""),
            detail().replace("</article>", "<p>日期｜2026.11.27 (五) 19:30</p></article>"),
        ):
            result = m.inspect_next_pair("B", listing, html)
            self.assertEqual(result["fields"], 2)
            self.assertEqual(result["event_local_role_diagnostics"]["decision"], "HOLD")
            self.assertFalse(result["event_local_role_diagnostics"]["formal_accepted"])

    def test_zepp_date_cannot_borrow_from_sibling_article(self):
        listing, _ = self.pair("B")
        cfg = m.NEXT["B"]
        unrelated = ('<main><article><h1>' + cfg["title"] +
                     '</h1><p>' + cfg["venue"] +
                     '</p></article><article><h1>OTHER EVENT</h1>'
                     '<p>日期｜2026.11.27 (五) 19:30</p>'
                     '<p>時間 [START] 19:30</p>'
                     '<p>開賣時間｜2026.7.25 (六) 下午13:00</p>'
                     '</article></main>')
        result = m.inspect_next_pair("B", listing, unrelated)
        self.assertEqual(result["decision"], "REVIEW_NON_SESSION_ONLY")
        self.assertEqual(result["event_local_role_diagnostics"]["decision"], "HOLD")
        self.assertIsNone(result["event_local_role_diagnostics"]["event_date_review"])


    def test_invalid_line(self):
        with self.assertRaises(ValueError): m.run_next_native_once("C")
        with self.assertRaises(ValueError): m.inspect_next_pair("C","","")



class TestSealedNativeReceiptOnlyLKG(unittest.TestCase):
    """No HTTP, no raw body, no formal-field promotion."""
    HEAD = "a" * 40

    def make_archive(self, *, b_override=None, a_override=None,
                     wrong_manifest=False):
        import io
        import hashlib
        import json
        import zipfile
        cfg = m.NEXT["B"]
        stamp0 = "2026-11-05T23:53:45.220002+00:00"
        stamp1 = "2026-11-05T23:53:46.546587+00:00"
        stamp2 = "2026-11-05T23:53:48.066652+00:00"
        def receipt(url, stamp, mime, size, digit):
            return {"url": url, "http_status": 200, "body_bytes": size,
                    "body_sha256": digit * 64, "content_type": mime,
                    "observed_at_utc": stamp,
                    "transport": "NATIVE_NO_REDIRECT_NO_RETRY"}
        a = {"line": "A", "event_id": m.NEXT["A"]["id"],
             "native_lkg": 0, "formal_fields": 0, "golden": 0,
             "published": 0, "first_failure": "HTTPError:HTTP Error 403"}
        b = {"kind": "P30_AB_DISTINCT_NATIVE_ONESHOT_V1", "line": "B",
             "source_id": cfg["source"], "event_id": cfg["id"],
             "attempted": 3, "http200": 2, "native_list": 1,
             "native_detail": 1, "native_identity": 1,
             "review_fields": 2, "native_lkg": 0,
             "formal_fields": 0, "golden": 0, "published": 0,
             "raw_html_saved": False, "policy": "ROBOTS_ALLOW",
             "decision": "REVIEW_NON_SESSION_ONLY",
             "first_failure": "INDEPENDENT_ACCEPTANCE_AND_LKG_HOLD",
             "release_state": "HARD_HOLD_NO_PUBLICATION",
             "robots_receipt": receipt(cfg["origin"] + "/robots.txt",
                                       stamp0, "text/plain", 160, "a"),
             "source_receipts": [
                 receipt(cfg["listing"], stamp1, "text/html", 343607, "b"),
                 receipt(cfg["detail"], stamp2, "text/html", 309088, "c")],
             "field_receipts": [
                 {"source_url": cfg["detail"], "event_id": cfg["id"],
                  "body_sha256": "c" * 64, "observed_at_utc": stamp2,
                  "role": role, "decision": "REVIEW",
                  "formal_accepted": False}
                 for role in ("SOURCE_EVENT_TITLE_REVIEW",
                              "SOURCE_VENUE_REVIEW")]}
        if a_override:
            a_override(a)
        if b_override:
            b_override(b)
        files = {"readiness.txt": ("head=" + self.HEAD +
                 "\nformal_fields=0\ngolden=0\npublished=0\n").encode(),
                 "next_native_A.json": json.dumps(a).encode(),
                 "next_native_B.json": json.dumps(b).encode()}
        lines = []
        for name, data in files.items():
            digest = hashlib.sha256(data).hexdigest()
            if wrong_manifest and name == "next_native_B.json":
                digest = "0" * 64
            lines.append(digest + "  evidence/" + name)
        files["SHA256SUMS.txt"] = ("\n".join(lines) + "\n").encode()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in files.items():
                z.writestr(name, data)
        raw = buf.getvalue()
        return raw, hashlib.sha256(raw).hexdigest()

    def audit(self, raw, digest):
        return m.audit_next_native_receipt_archive(
            raw, expected_zip_sha256=digest, expected_head=self.HEAD)

    def test_original_shape_receipt_only_not_body_or_formal(self):
        raw, digest = self.make_archive()
        snapshot = self.audit(raw, digest)
        self.assertEqual(snapshot["source_event_id"], "167511")
        self.assertEqual(snapshot["receipt_only_identity_lkg"], 1)
        self.assertEqual(snapshot["native_body_replay_lkg"], 0)
        self.assertEqual(snapshot["formal_accepted_fields"], 0)
        self.assertEqual(snapshot["golden"], 0)
        self.assertEqual(snapshot["published"], 0)

    def test_digest_manifest_and_native_identity_fail_closed(self):
        raw, digest = self.make_archive()
        with self.assertRaisesRegex(ValueError, "ARTIFACT_SHA"):
            self.audit(raw, "0" * 64)
        raw, digest = self.make_archive(wrong_manifest=True)
        with self.assertRaisesRegex(ValueError, "MANIFEST_SHA"):
            self.audit(raw, digest)
        for mutate in (
            lambda b: b.update(event_id="OTHER"),
            lambda b: b.update(native_identity=0),
            lambda b: b.update(formal_fields=1),
            lambda b: b["source_receipts"][1].update(
                body_sha256="e" * 64),
            lambda b: b["field_receipts"][0].update(
                formal_accepted=True),
            lambda b: b["field_receipts"][0].update(
                source_url="https://evil.example/"),
            lambda b: b["robots_receipt"].update(
                content_type="text/html"),
            lambda b: b["source_receipts"][1].update(
                observed_at_utc="2026-11-05T23:30:00+00:00"),
        ):
            raw, digest = self.make_archive(b_override=mutate)
            with self.assertRaises(ValueError):
                self.audit(raw, digest)

    def test_atomic_cas_idempotence_and_isolation(self):
        import json
        import tempfile
        from pathlib import Path
        raw, digest = self.make_archive()
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "receipt_lkg.json"
            kwargs = {"expected_zip_sha256": digest,
                      "expected_head": self.HEAD}
            first = m.persist_next_native_receipt_lkg(
                raw, target, repo, **kwargs)
            self.assertTrue(first["persisted"])
            self.assertEqual(first["native_body_replay_lkg"], 0)
            second = m.persist_next_native_receipt_lkg(
                raw, target, repo, **kwargs)
            self.assertTrue(second["idempotent"])
            payload = json.loads(target.read_text())
            self.assertEqual(payload["snapshot"]["formal_accepted_fields"], 0)
            payload["snapshot"]["formal_accepted_fields"] = 1
            target.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "PRIOR_ENVELOPE"):
                m.persist_next_native_receipt_lkg(
                    raw, target, repo, **kwargs)
            self.assertFalse((Path(temp) / "receipt_lkg.json.lock").exists())
        with self.assertRaisesRegex(ValueError, "ISOLATION"):
            m.persist_next_native_receipt_lkg(
                raw, repo / "docs" / "data.json", repo,
                expected_zip_sha256=digest, expected_head=self.HEAD)



class TestTixfun09DistinctNative(unittest.TestCase):
    """Source-owned event identity; never confuse PRODUCT with Session."""
    def setUp(self):
        self.listing = ('<main><article><a href="' + m.TIXFUN_DETAIL +
                        '">戲劇 ' + m.TIXFUN_TITLE +
                        ' 2026/11/07 - 2026/11/07</a></article></main>')
        self.detail = ('<main><article><h1>' + m.TIXFUN_TITLE +
                       '</h1><p>2026/11/07</p><p>NT$0</p></article></main>')

    def test_distinct_same_product_review_only(self):
        r = m.inspect_tixfun_pair(self.listing, self.detail)
        self.assertEqual(r["list_exact_edge"], 1)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(r["formal_accepted_fields"], 0)
        self.assertNotIn("SESSION", str(r))
        self.assertEqual(m.tixfun_exact_href(m.TIXFUN_DETAIL), m.TIXFUN_DETAIL)

    def test_detail_missing_heading_cannot_borrow_list_title(self):
        r = m.inspect_tixfun_pair(self.listing,
                                  "<main><article><p>2026/11/07 NT$0</p></article></main>")
        self.assertEqual(r["reason"], "TIXFUN_DETAIL_EXACT_TITLE_HOLD")
        self.assertEqual(r["same_id_review"], 0)
        self.assertEqual(r["list_exact_edge"], 1)
        self.assertEqual(m.inspect_tixfun_pair(
            self.listing, "<header><h1>" + m.TIXFUN_TITLE +
            "</h1></header>")["same_id_review"], 0)

    def test_wrong_product_duplicate_query_checkout_and_host_hold(self):
        for href in (m.TIXFUN_DETAIL + "&SESSION=1",
                     m.TIXFUN_DETAIL + "#x",
                     "http://tixfun.com/UTK0201_?PRODUCT_ID=Q029NZNY",
                     "https://evil.example/UTK0201_?PRODUCT_ID=Q029NZNY",
                     "https://tixfun.com/checkout?PRODUCT_ID=Q029NZNY",
                     m.TIXFUN_DETAIL.replace("Q029NZNY", "WRONG")):
            self.assertIsNone(m.tixfun_exact_href(href))
        self.assertEqual(m.inspect_tixfun_pair(
            self.listing + self.listing, self.detail)["same_id_review"], 0)

    def test_native_policy_denies_before_list(self):
        from unittest.mock import patch
        with patch.object(m.urllib.request, "build_opener") as opener, \
             patch.object(m, "read_public", return_value=(
                 "User-agent: *\nDisallow: /\n",
                 dict(url="https://tixfun.com/robots.txt",
                      body_sha256="a" * 64))) as reader:
            r = m.run_tixfun_native_once()
        self.assertEqual(reader.call_count, 1)
        self.assertEqual(r["attempted"], 1)
        self.assertEqual(r["http200"], 0)
        self.assertIn("TIXFUN_ROBOTS_DISALLOW_HOLD", r["first_failure"])

    def test_native_missing_detail_title_keeps_http_receipts_but_no_lkg(self):
        from unittest.mock import patch
        stamps = "2026-11-06T03:55:00+00:00"
        def receipt(url, digest):
            return dict(url=url, http_status=200, body_sha256=digest * 64,
                        body_bytes=123, content_type="text/html",
                        observed_at_utc=stamps,
                        transport="NATIVE_NO_REDIRECT_NO_RETRY")
        answers = [
            ("User-agent: *\nAllow: /\n",
             receipt("https://tixfun.com/robots.txt", "a")),
            (self.listing, receipt(m.TIXFUN_LIST, "b")),
            ("<main><article><p>2026/11/07 NT$0</p></article></main>",
             receipt(m.TIXFUN_DETAIL, "c")),
        ]
        with patch.object(m.urllib.request, "build_opener"), \
             patch.object(m, "read_public", side_effect=answers) as reader:
            r = m.run_tixfun_native_once()
        self.assertEqual(reader.call_count, 3)
        self.assertEqual((r["http200"], r["native_list"], r["native_detail"]), (2, 1, 1))
        self.assertEqual(r["list_exact_edge"], 1)
        self.assertEqual(r["native_same_id_review"], 0)
        self.assertEqual(r["native_lkg"], 0)
        self.assertEqual(r["formal_accepted_fields"], 0)
        self.assertEqual(r["golden"], 0)
        self.assertEqual(r["published"], 0)
        self.assertFalse(r["raw_html_saved"])

if __name__ == "__main__":
    unittest.main()

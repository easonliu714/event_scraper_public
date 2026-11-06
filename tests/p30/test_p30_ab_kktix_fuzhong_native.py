"""KKTIX #01 and Fuzhong15 New Taipei strict source-bound native Gate tests."""
import unittest
from unittest.mock import patch
from scripts import p30_ab_kktix_fuzhong_native as m


class ABSourceTests(unittest.TestCase):
    def setUp(self):
        self.a_list = ('<main><a href="/events/myds2026">'
                       + m.SOURCES["A"]["title"] + '</a>'
                       '<a href="/events/myds2026">Get Ticket</a></main>')
        self.a_detail = ('<main><article><h1>' + m.SOURCES["A"]["title"] +
                         '</h1><p>日期｜2026.11.28 (六) OPEN 17:00／START 18:00</p>'
                         '<p>地點｜The Wall Live House</p>'
                         '<p>一般預售票 NT$1,800 / VIP NT$2,300</p>'
                         '</article></main>')
        self.b_list = ('<main><a href="/xcmovie/cont?sid=0Q289834314351531469'
                       '&amp;xsmsid=0M361641875264878260">時間暫停的季節</a></main>')
        self.b_detail = ('<main><section><h3>時間暫停的季節</h3>'
                         '<p>放映日期：2026/11/06 19:00 2026/12/02 19:00</p>'
                         '<p>更新日期：2026-10-16</p></section></main>')

    def test_a_exact_event_title_show_and_venue_review(self):
        r = m.inspect_pair("A", self.a_list, self.a_detail)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(set(r["field_roles"]), {
            "SHOW_START_2026_11_28_1800_REVIEW", "VENUE_THE_WALL_REVIEW"})
        self.assertEqual(r["formal_accepted_fields"], 0)
        self.assertNotIn("PRICE", repr(r))

    def test_b_list_same_row_date_time_review_without_detail_scope(self):
        src = m.SOURCES["B"]
        listing = ('<table><tr><td>11/06(五)</td><td>19:00</td><td><a href="' +
                   src["detail"].replace("&", "&amp;") + '">' + src["title"] +
                   '</a></td></tr></table>')
        detail = '<main><h1>' + src["title"] + '</h1></main>'
        r = m.inspect_pair("B", listing, detail)
        self.assertEqual(r["decision"], "REVIEW_LIST_ROW_ONLY")
        self.assertEqual(r["list_row_roles"], ["LIST_11_06_19_00_REVIEW_NO_YEAR"])
        self.assertEqual((r["field_roles"], r["formal_accepted_fields"]), ([], 0))
        borrowed = '<table><tr><td>11/06(五)</td><td>19:00</td></tr></table>' + (
            listing.replace('<td>11/06(五)</td><td>19:00</td>', '<td>--</td><td>--</td>'))
        r2 = m.inspect_pair("B", borrowed, detail)
        self.assertEqual(r2["list_row_roles"], [])
        self.assertEqual(r2["decision"], "REVIEW_IDENTITY_ONLY")

    def test_b_exact_sid_two_screenings_not_update_date(self):
        r = m.inspect_pair("B", self.b_list, self.b_detail)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(r["field_roles"], ["TWO_SCREENING_STARTS_REVIEW"])
        self.assertEqual(r["formal_accepted_fields"], 0)

    def test_wrong_host_checkout_query_fragment_and_sid_fail_closed(self):
        for line, path in (("A", "/events/myds2026"),
                           ("B", "/xcmovie/cont?sid=0Q289834314351531469&xsmsid=0M361641875264878260")):
            for href in ("https://evil.example" + path, "//evil.example" + path,
                         m.SOURCES[line]["detail"] + "#foo",
                         m.SOURCES[line]["detail"] + ("&session=1" if line == "B" else "?session=1"),
                         m.SOURCES[line]["detail"] + "/checkout"):
                self.assertIsNone(m.exact_detail(line, href), (line, href))
        self.assertIsNone(m.exact_detail("B",
            "/xcmovie/cont?sid=WRONG&xsmsid=0M361641875264878260"))

    def test_duplicate_edge_missing_heading_and_sibling_borrow_hold(self):
        self.assertEqual(m.inspect_pair("A", self.a_list + self.a_list,
                                         self.a_detail)["same_id_review"], 0)
        self.assertEqual(m.inspect_pair("A", self.a_list,
                "<main><p>名譽傳說 1st ONEMAN TOUR 2026</p></main>")["same_id_review"], 0)
        foreign = ('<main><article><h3>時間暫停的季節</h3></article>'
                   '<article><h3>其他影片</h3>'
                   '<p>放映日期：2026/11/06 19:00 2026/12/02 19:00</p>'
                   '</article></main>')
        r = m.inspect_pair("B", self.b_list, foreign)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(r["field_roles"], [])
        self.assertEqual(r["decision"], "REVIEW_IDENTITY_ONLY")

    def test_b_unexpected_third_date_and_wrong_role_hold(self):
        bad = self.b_detail.replace("更新日期：2026-10-16",
            "放映日期：2026/11/07 18:00")
        self.assertEqual(m.inspect_pair("B", self.b_list, bad)["field_roles"], [])

    def test_native_b_list_row_receipt_bound_to_list_not_detail(self):
        src = m.SOURCES["B"]
        listing = ('<table><tr><td>11/06(五)</td><td>19:00</td><td><a href="' +
                   src["detail"].replace("&", "&amp;") + '">' + src["title"] +
                   '</a></td></tr></table>')
        detail = '<main><h1>' + src["title"] + '</h1></main>'
        def receipt(url, sha):
            return dict(url=url, http_status=200, body_bytes=100,
                        body_sha256=sha*64, observed_at_utc="2026-11-06T06:00:00+00:00",
                        content_type="text/html", transport="NATIVE_NO_REDIRECT_NO_RETRY")
        answers = [("User-agent: *\\nAllow: /\\n", receipt(src["origin"] + "/robots.txt", "a")),
                   (listing, receipt(src["list"], "b")),
                   (detail, receipt(src["detail"], "c"))]
        with patch.object(m.urllib.request, "build_opener"), patch.object(
                m, "read_public", side_effect=answers) as reader:
            r = m.run_native_once("B")
        self.assertEqual(reader.call_count, 3)
        self.assertEqual(r["decision"], "REVIEW_LIST_ROW_ONLY")
        self.assertEqual(r["list_row_roles"], ["LIST_11_06_19_00_REVIEW_NO_YEAR"])
        self.assertEqual(len(r["field_receipts"]), 2)
        self.assertEqual(r["field_receipts"][0]["body_sha256"], "c"*64)
        self.assertEqual(r["field_receipts"][1]["body_sha256"], "b"*64)
        self.assertEqual(r["field_receipts"][1]["source_url"], src["list"])
        self.assertEqual((r["native_lkg"], r["formal_accepted_fields"], r["published"]),
                         (0, 0, 0))

    def test_udn_exact_product_card_is_not_bundle_or_checkout(self):
        src = m.SOURCES["A_UDN"]
        home = ('<main><a href="/Application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1AEBJG5">'
                + src["title"] + ' 2026/11/20 ~ 2026/11/29 臺北表演藝術中心 大劇院 NT$ 1,000 ~ 4,600</a>'
                '<a href="/Application/UTK02/UTK0201_.aspx?PRODUCT_ID=P1BUNDLE">'
                '四人套票-' + src["title"] + '</a></main>')
        detail = ('<main><section><h2>' + src["title"] + '</h2>'
                  '<p>2026/11/20 ~ 2026/11/29</p>'
                  '<p>臺北表演藝術中心 大劇院</p>'
                  '<p>票價 NT$ 1,000 ~ 4,600</p></section></main>')
        r = m.inspect_pair("A_UDN", home, detail)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(set(r["field_roles"]), {
            "ADVERTISED_SHOW_RANGE_REVIEW_NO_SESSION",
            "VENUE_TPAC_GRAND_THEATER_REVIEW"})
        self.assertEqual(r["formal_accepted_fields"], 0)
        self.assertNotIn("PRICE", repr(r))
        for bad in ("?PRODUCT_ID=P1AEBJG5&SESSION=1",
                    "?PRODUCT_ID=P1BUNDLE",
                    "?PRODUCT_ID=P1AEBJG5#checkout"):
            self.assertIsNone(m.exact_detail("A_UDN",
                "/Application/UTK02/UTK0201_.aspx" + bad))
        self.assertEqual(m.inspect_pair("A_UDN", home,
            '<main><p>' + src["title"] + '</p></main>')["same_id_review"], 0)

    def test_yingge_exact_sid_identity_and_no_sibling_date_borrow(self):
        src = m.SOURCES["B_CERAMICS"]
        listing = ('<main><a href="' + src["detail"].replace("&", "&amp;") +
                   '">' + src["title"] + '</a></main>')
        detail = ('<main><article><h3>' + src["title"] + '</h3>'
                  '<p>展覽時間:2026年11月20日至2026年12月20日</p>'
                  '<p>展覽地點:b1陶藝長廊</p></article></main>')
        r = m.inspect_pair("B_CERAMICS", listing, detail)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(set(r["field_roles"]), {
            "EXHIBITION_RANGE_REVIEW_NO_SESSION",
            "VENUE_B1_CERAMICS_GALLERY_REVIEW"})
        sibling = ('<main><article><h3>' + src["title"] + '</h3></article>'
                   '<article><h3>其他展覽</h3>'
                   '<p>展覽時間:2026年11月20日至2026年12月20日</p>'
                   '<p>展覽地點:b1陶藝長廊</p></article></main>')
        r2 = m.inspect_pair("B_CERAMICS", listing, sibling)
        self.assertEqual((r2["same_id_review"], r2["field_roles"]), (1, []))
        self.assertIsNone(m.exact_detail("B_CERAMICS",
            src["detail"] + "&checkout=1"))
        self.assertIsNone(m.exact_detail("B_CERAMICS",
            src["detail"].replace("0Q218346582180038351", "WRONG")))

    def test_new_rotation_native_receipts_are_source_owned_not_formal(self):
        for line in ("A_UDN", "B_CERAMICS"):
            src = m.SOURCES[line]
            title = src["title"]
            label = title + " 2026/11/20 ~ 2026/11/29" if line == "A_UDN" else title
            listing = ('<main><a href="' + src["detail"].replace("&", "&amp;") +
                       '">' + label + '</a></main>')
            detail = '<main><section><h2>' + title + '</h2></section></main>'
            def receipt(url, letter):
                return dict(url=url, http_status=200, body_bytes=256,
                            body_sha256=letter*64,
                            observed_at_utc="2026-11-06T07:55:00+00:00",
                            content_type="text/html", transport="NATIVE_NO_REDIRECT_NO_RETRY")
            answers = [("User-agent: *\\nAllow: /\\n",
                        receipt(src["origin"] + "/robots.txt", "a")),
                       (listing, receipt(src["list"], "b")),
                       (detail, receipt(src["detail"], "c"))]
            with patch.object(m.urllib.request, "build_opener"), patch.object(
                    m, "read_public", side_effect=answers) as reader:
                out = m.run_native_once(line)
            self.assertEqual(reader.call_count, 3)
            self.assertEqual((out["native_list"], out["native_detail"],
                              out["native_same_id_review"]), (1, 1, 1))
            self.assertEqual(out["field_receipts"][0]["body_sha256"], "c"*64)
            self.assertEqual(out["field_receipts"][0]["source_url"], src["detail"])
            self.assertEqual((out["native_lkg"], out["formal_accepted_fields"],
                              out["golden"], out["published"]), (0, 0, 0, 0))
            self.assertFalse(out["raw_html_saved"])


    def test_accupass_02_new_exact_search_card_to_same_event_review(self):
        src = m.SOURCES["A_ACCUPASS"]
        tracking = ("?utm_campaign=accu_e_&utm_medium=search_result_"
                    "&utm_source=web")
        listing = ('<main><a href="' + src["detail"] + tracking + '">'
                   + src["title"] + '</a></main>')
        detail = ('<main><article><h1>' + src["title"] + '</h1>'
                  '<p>2026.11.22 (Sun) 13:45 - 17:00 (GMT+8)</p>'
                  '<p>植境plantārium-複合式空間</p>'
                  '<p>After registration, show your ticket</p>'
                  '</article></main>')
        r = m.inspect_pair("A_ACCUPASS", listing, detail)
        self.assertEqual((r["same_id_review"], r["decision"]),
                         (1, "REVIEW_NON_SESSION_ONLY"))
        self.assertEqual(set(r["field_roles"]), {
            "ADVERTISED_EVENT_RANGE_REVIEW_NO_SESSION",
            "VENUE_PLANTARIUM_REVIEW"})
        self.assertEqual(r["formal_accepted_fields"], 0)
        self.assertNotIn("PRICE", repr(r))
        self.assertEqual(m.exact_detail("A_ACCUPASS",
                         src["detail"] + tracking), src["detail"])
        for bad in ("?session=1", "?utm_source=web&checkout=1",
                    "?utm_source=web&utm_source=web",
                    "?utm_campaign=other", "#checkout"):
            self.assertIsNone(m.exact_detail("A_ACCUPASS",
                              src["detail"] + bad))

    def test_accupass_02_sibling_borrow_and_duplicate_hold(self):
        src = m.SOURCES["A_ACCUPASS"]
        listing = ('<a href="' + src["detail"] + '">' +
                   src["title"] + '</a>')
        detail = ('<article><h1>' + src["title"] + '</h1></article>'
                  '<article><h1>另一場活動</h1>'
                  '<p>2026.11.22 (Sun) 13:45 - 17:00</p>'
                  '<p>植境plantārium-複合式空間</p></article>')
        r = m.inspect_pair("A_ACCUPASS", listing, detail)
        self.assertEqual((r["same_id_review"], r["field_roles"]), (1, []))
        self.assertEqual(r["first_failure"], "AB_EVENT_LOCAL_FIELD_SCOPE_HOLD")
        self.assertEqual(m.inspect_pair("A_ACCUPASS", listing * 2,
                         detail)["same_id_review"], 0)

    def test_zepp_takase_160668_new_home_card_exact_rid(self):
        src = m.SOURCES["B_ZEPP_TAKASE"]
        # Official homepage is an event card, not an exact-title-only anchor.
        card = ('<main><a href="/hall/newtaipei/schedule/single/?rid=160668">'
                '2026 11.7 SAT 高瀬統也 ' + src["title"] +
                ' [OPEN] 17:00 [START] 18:00 READ MORE</a></main>')
        detail = '<main><article><h2>' + src["title"] + '</h2></article></main>'
        out = m.inspect_pair("B_ZEPP_TAKASE", card, detail)
        self.assertEqual((out["same_id_review"], out["formal_accepted_fields"]),
                         (1, 0))
        self.assertEqual(out["field_roles"], [])
        self.assertEqual(out["first_failure"], "AB_EVENT_LOCAL_FIELD_SCOPE_HOLD")
        for bad in ("?rid=167511", "?rid=160668&rid=167511",
                    "?rid=160668&checkout=1", "?rid=160668#buy"):
            self.assertIsNone(m.exact_detail("B_ZEPP_TAKASE",
                "/hall/newtaipei/schedule/single/" + bad))
        self.assertEqual(m.inspect_pair("B_ZEPP_TAKASE",
            card.replace("2026 11.7", "2026 11.8"), detail)["same_id_review"], 0)
        self.assertEqual(m.inspect_pair("B_ZEPP_TAKASE",
            card + card, detail)["same_id_review"], 0)

    def test_tixcraft_03_rotation_indexed_only_no_cross_event(self):
        src = m.SOURCES["A_TIXCRAFT"]
        listing = '<a href="/activity/detail/26_aftp">' + src["title"] + '</a>'
        detail = '<article><h1>' + src["title"] + '</h1></article>'
        out = m.inspect_pair("A_TIXCRAFT", listing, detail)
        self.assertEqual((out["same_id_review"], out["field_roles"],
                          out["formal_accepted_fields"]), (1, [], 0))
        for bad in ("/activity/detail/26_btskns",
                    "/activity/detail/26_aftp?session=1",
                    "https://other.example/activity/detail/26_aftp"):
            self.assertIsNone(m.exact_detail("A_TIXCRAFT", bad))
        self.assertEqual(m.inspect_pair("A_TIXCRAFT",
            listing.replace("26_aftp", "26_btskns"), detail)["same_id_review"], 0)

    def test_native_robots_denied_before_list(self):
        rr = dict(url="https://gutspromotion.kktix.cc/robots.txt",
                  http_status=200, body_bytes=25, body_sha256="a"*64,
                  observed_at_utc="2026-11-06T05:00:00+00:00")
        with patch.object(m.urllib.request, "build_opener"), patch.object(
                m, "read_public", return_value=("User-agent: *\nDisallow: /\n", rr)) as reader:
            r = m.run_native_once("A")
        self.assertEqual(reader.call_count, 1)
        self.assertEqual((r["native_list"], r["native_detail"], r["native_lkg"]), (0, 0, 0))
        self.assertIn("AB_ROBOTS_DISALLOW_HOLD", r["first_failure"])

    def test_native_a_success_is_still_review_only_no_lkg(self):
        def receipt(url, sha):
            return dict(url=url, http_status=200, body_bytes=123,
                        body_sha256=sha*64, observed_at_utc="2026-11-06T05:00:00+00:00",
                        content_type="text/html", transport="NATIVE_NO_REDIRECT_NO_RETRY")
        src = m.SOURCES["A"]
        answers = [("User-agent: *\nAllow: /\n",
                    receipt(src["origin"] + "/robots.txt", "a")),
                   (self.a_list, receipt(src["list"], "b")),
                   (self.a_detail, receipt(src["detail"], "c"))]
        with patch.object(m.urllib.request, "build_opener"), patch.object(
                m, "read_public", side_effect=answers) as reader:
            r = m.run_native_once("A")
        self.assertEqual(reader.call_count, 3)
        self.assertEqual((r["native_http200"], r["native_list"], r["native_detail"],
                          r["native_same_id_review"]), (2, 1, 1, 1))
        self.assertEqual(len(r["field_receipts"]), 3)
        self.assertEqual((r["native_lkg"], r["formal_accepted_fields"],
                          r["golden"], r["published"]), (0, 0, 0, 0))
        self.assertFalse(r["raw_html_saved"])


    def test_a_kimu_exact_organizer_list_detail_event_local_roles(self):
        source = m.SOURCES["A_KIMU"]
        listing = '<main><a href="/events/2026itmgameforum">' + source["title"] + '</a></main>'
        detail = ('<main><article><h1>' + source["title"] + '</h1>'
                  '<p>時間：2026/11/14（六）10:00 - 16:30</p>'
                  '<p>地點：世貿展覽館一館 / 1F數發部數產署主題館舞台區</p>'
                  '<p>費用：免費</p></article></main>')
        r = m.inspect_pair("A_KIMU", listing, detail)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(set(r["field_roles"]), {
            "FORUM_TIME_RANGE_REVIEW_NOT_TICKET_SESSION",
            "VENUE_TWTC_HALL1_STAGE_REVIEW"})
        self.assertEqual(r["formal_accepted_fields"], 0)
        self.assertNotIn("PRICE", repr(r))
        self.assertIsNone(m.exact_detail("A_KIMU", "/events/2026itmgameforum/registrations/new"))
        self.assertIsNone(m.exact_detail("A_KIMU", "/events/2026itmgameforum?session=1"))

    def test_a_kimu_rejects_cross_event_or_global_unowned_time(self):
        source = m.SOURCES["A_KIMU"]
        listing = '<main><a href="/events/2026itmgameforum">' + source["title"] + '</a></main>'
        wrong = listing.replace("2026itmgameforum", "2026itmgameforum-other")
        detail = ('<header><h1>' + source["title"] + '</h1></header>'
                  '<main><article><p>時間：2026/11/14（六）10:00 - 16:30</p>'
                  '</article></main>')
        self.assertEqual(m.inspect_pair("A_KIMU", wrong, detail)["same_id_review"], 0)
        self.assertEqual(m.inspect_pair("A_KIMU", listing, detail)["same_id_review"], 1)
        self.assertEqual(m.inspect_pair("A_KIMU", listing, detail)["field_roles"], [])

    def test_b_ntcam_exact_public_event_identity_without_inferred_field(self):
        source = m.SOURCES["B_NTCAM"]
        listing = '<main><a href="/event_content.aspx?id=E2609013">' + source["title"] + '</a></main>'
        detail = '<main><article><h1>' + source["title"] + '</h1><p>新北市美術館</p></article></main>'
        r = m.inspect_pair("B_NTCAM", listing, detail)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(r["field_roles"], [])
        self.assertEqual(r["formal_accepted_fields"], 0)
        self.assertIsNone(m.exact_detail("B_NTCAM", "/event_content.aspx?id=E2609014"))
        self.assertIsNone(m.exact_detail("B_NTCAM", "/event_content.aspx?id=E2609013&ticket=1"))

    def test_b_ntcam_dynamic_index_and_seo_only_are_hold(self):
        source = m.SOURCES["B_NTCAM"]
        detail = '<main><article><h1>' + source["title"] + '</h1></article></main>'
        self.assertEqual(m.inspect_pair("B_NTCAM", "<main><div id='app'></div></main>",
                                        detail)["same_id_review"], 0)
        listing = '<main><a href="/event_content.aspx?id=E2609013">' + source["title"] + '</a></main>'
        seo_only = '<head><title>' + source["title"] + '</title></head><main></main>'
        self.assertEqual(m.inspect_pair("B_NTCAM", listing, seo_only)["same_id_review"], 0)


    def test_zepp_exact_event_local_organizer_edge_not_checkout_or_session(self):
        source = m.SOURCES["B_ZEPP_TAKASE"]
        listing = ('<main><a href="' + source["detail"] + '">'
                   + source["title"] + ' 2026 11.7 18:00</a></main>')
        ticket = source["public_ticket_event"]
        detail = ('<main><article><h1>' + source["title"] + '</h1>'
                  '<a href="' + ticket + '">KKTIX</a>'
                  '<p>[DAY1] 2026年11月7日 開演 18:00</p>'
                  '<p>[DAY2] 2026年11月8日 開演 17:00</p>'
                  '<p>會場：Zepp New Taipei</p></article></main>')
        result = m.inspect_pair("B_ZEPP_TAKASE", listing, detail)
        self.assertEqual(result["same_id_review"], 1)
        self.assertEqual(result["ticket_event_edge_review"], 1)
        self.assertEqual(result["ticket_event_url"], ticket)
        self.assertEqual(result["decision"],
                         "REVIEW_SOURCE_DIRECT_TICKET_EDGE_NO_SESSION")
        self.assertEqual(result["first_failure"],
                         "AB_EVENT_LOCAL_DATE_HALL_AUTHORITY_HOLD")
        self.assertEqual(result["field_roles"], [])
        self.assertEqual(result["formal_accepted_fields"], 0)
        for altered in (
            detail.replace(ticket, ticket + "?registrations=new"),
            detail.replace(ticket, "https://evil.example/events/takasetoya202611"),
            detail.replace(">KKTIX</a>", ">Get Ticket</a>"),
            detail.replace('</article>', '<a href="' + ticket + '">KKTIX</a></article>'),
            ('<main><article><h1>' + source["title"] + '</h1></article>'
             '<article><a href="' + ticket + '">KKTIX</a></article></main>'),
        ):
            with self.subTest(altered=altered[-90:]):
                r = m.inspect_pair("B_ZEPP_TAKASE", listing, altered)
                self.assertEqual(r["ticket_event_edge_review"], 0)
                self.assertEqual(r["formal_accepted_fields"], 0)



if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

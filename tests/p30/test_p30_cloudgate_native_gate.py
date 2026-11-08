"""Cloud Gate official source identity and postponement safety tests (offline)."""
import unittest
from scripts import p30_cloudgate_native_gate as m

class CloudGateTests(unittest.TestCase):
    def setUp(self):
        self.list_html = ('<main><a href="/cgt/theater-event/1680">'
            + m.TITLE + '2026.10.17 - 12.19</a></main>')
        self.detail_html = ('<main><article><h1>'+m.TITLE+'</h1>'
            '<p>● 12月19日(六) 13:30</p>'
            '<p>※節目異動請留意，原11/14兩場講座延期至12/19</p>'
            '</article></main>')

    def test_exact_identity_and_postponement_review(self):
        r=m.inspect_pair(self.list_html,self.detail_html)
        self.assertEqual(r["same_id_review"],1)
        self.assertEqual(r["postponement_review"],1)
        self.assertEqual(r["formal_accepted_fields"],0)

    def test_official_cg_mirror_requires_exact_direct_list_edge(self):
        # The /cgt index can link to a same-ID /cg first-party mirror.
        # Caller HTML does not prove native GET or source freshness.
        mirror_list = self.list_html.replace(
            "/cgt/theater-event/1680", "/cg/theater-event/1680")
        result = m.inspect_pair(mirror_list, self.detail_html)
        self.assertEqual((result["same_id_review"],
                          result["list_derived_detail_url"]),
                         (1, m.DETAIL_MIRROR_URL))
        self.assertEqual(m.exact_detail("/cg/theater-event/1680"),
                         m.DETAIL_MIRROR_URL)
        for bad in ("/cg/theater-event/1681",
                    "/cg/theater-event/1680?from=search",
                    "https://evil.example/cg/theater-event/1680"):
            self.assertIsNone(m.exact_detail(bad))
        # Ambiguous dual paths must not be merged by similar titles.
        self.assertEqual(m.inspect_pair(
            self.list_html + mirror_list, self.detail_html)[
                "first_failure"], "CLOUDGATE_LIST_EXACT_ID_TITLE_HOLD")

    def test_foreign_id_query_checkout_hold(self):
        for bad in ("/cgt/theater-event/1681",
                    "/cgt/theater-event/1680?session=1",
                    "https://evil.example/cgt/theater-event/1680",
                    "/cgt/theater-event/1680/checkout"):
            self.assertIsNone(m.exact_detail(bad))
            self.assertEqual(m.inspect_pair(self.list_html.replace(
                "/cgt/theater-event/1680",bad),self.detail_html)["same_id_review"],0)

    def test_global_heading_and_old_date_not_authority(self):
        self.assertEqual(m.inspect_pair(self.list_html,
            "<header><h1>"+m.TITLE+"</h1></header>")["same_id_review"],0)
        r=m.inspect_pair(self.list_html,self.detail_html.replace(
            "延期至12/19","仍為11/14"))
        self.assertEqual(r["postponement_review"],0)
        self.assertEqual(r["same_id_review"],1)

    def test_sibling_article_postponement_cannot_borrow(self):
        # Regression: an unrelated sibling event must not supply the 12/19 role.
        foreign = ('<main><article><h1>'+m.TITLE+'</h1>'
                   '<p>原11/14演出，詳情待公告</p></article>'
                   '<article><h1>其他節目</h1>'
                   '<p>● 12月19日(六) 13:30</p>'
                   '<p>原11/14兩場講座延期至12/19</p>'
                   '</article></main>')
        r = m.inspect_pair(self.list_html, foreign)
        self.assertEqual(r["same_id_review"], 1)
        self.assertEqual(r["postponement_review"], 0)
        self.assertEqual(r["first_failure"],
                         "CLOUDGATE_POSTPONEMENT_LOCAL_AUTHORITY_HOLD")

    def test_main_only_heading_and_sibling_section_hold(self):
        main_only = ('<main><h1>'+m.TITLE+'</h1>'
                     '<p>● 12月19日</p>'
                     '<p>原11/14兩場講座延期至12/19</p></main>')
        r = m.inspect_pair(self.list_html, main_only)
        self.assertEqual(r["same_id_review"], 0)
        self.assertEqual(r["first_failure"],
                         "CLOUDGATE_EVENT_LOCAL_TITLE_SCOPE_HOLD")
        sibling = ('<main><section><h1>'+m.TITLE+'</h1></section>'
                   '<section><p>● 12月19日</p>'
                   '<p>原11/14兩場講座延期至12/19</p></section></main>')
        self.assertEqual(m.inspect_pair(
            self.list_html, sibling)["postponement_review"], 0)

    def test_nested_title_article_owns_correction(self):
        nested = ('<main><section><article><h1>'+m.TITLE+'</h1>'
                  '<p>● 12月19日(六) 13:30</p>'
                  '<p>原11/14兩場講座延期至12/19</p>'
                  '</article></section></main>')
        r = m.inspect_pair(self.list_html, nested)
        self.assertEqual((r["same_id_review"],
                          r["postponement_review"]), (1, 1))
        self.assertEqual(r["formal_accepted_fields"], 0)

    def test_duplicate_event_edges_hold(self):
        self.assertEqual(m.inspect_pair(self.list_html+self.list_html,
            self.detail_html)["same_id_review"],0)

if __name__=="__main__":
    unittest.main()

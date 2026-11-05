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

    def test_duplicate_event_edges_hold(self):
        self.assertEqual(m.inspect_pair(self.list_html+self.list_html,
            self.detail_html)["same_id_review"],0)

if __name__=="__main__":
    unittest.main()

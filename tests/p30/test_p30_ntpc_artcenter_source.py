"""NTPC official source role boundaries, injected HTML only."""
import unittest
from scripts import p30_ntpc_artcenter_source as m


class TestNTPCCanonicalVenue(unittest.TestCase):
    def setUp(self):
        self.url = ("/artcenter_chi/xmdoc/cont?sid=" + m.SID +
                    "&sq=&xsmsid=" + m.XSMSID)
        self.listing = '<main><a href="' + self.url + '">' + m.TITLE + '</a></main>'
        self.detail = ('<main><article><h3>' + m.TITLE + '</h3>'
                       '<p>★展覽地點：' + m.VENUE + '</p>'
                       '<time>2026-10-20</time></article></main>')

    def test_local_same_sid_and_venue_review_only(self):
        d = m.inspect_caller_html(self.listing, self.detail)
        self.assertEqual(d["same_id_review"], 1)
        self.assertEqual(d["venue_room_review"], 1)
        self.assertEqual(d["native_get"], 0)
        self.assertEqual(d["formal_accepted_fields"], 0)
        self.assertEqual(d["date_role"], "SHOW_DATE_HOLD_TITLE_MONTH_DAY_ONLY")
        self.assertEqual(d["bulletin_date_role"], "PUBLICATION_DATE_NOT_SHOW_DATE")

    def test_wrong_sid_and_cross_site_hold(self):
        for href in (self.url.replace(m.SID, "0Q293634176769376688"),
                     "https://evil.example" + self.url,
                     self.url + "&session=1"):
            with self.subTest(href=href):
                self.assertIsNone(m.exact_detail(href))

    def test_no_global_heading_authority(self):
        detail = "<header><h3>" + m.TITLE + "</h3></header><main><p>★展覽地點：" + m.VENUE + "</p></main>"
        self.assertEqual(m.inspect_caller_html(self.listing, detail)["same_id_review"], 0)

    def test_no_cross_card_or_venue_inference(self):
        wrong = self.listing.replace(m.TITLE, "其他展覽")
        self.assertEqual(m.inspect_caller_html(wrong, self.detail)["same_id_review"], 0)
        self.assertEqual(m.inspect_caller_html(self.listing, self.detail.replace(
            m.VENUE, "其他展覽室"))["venue_room_review"], 0)

    def test_duplicate_query_edge_fails_closed(self):
        doubled = self.listing.replace("</main>", '<a href="' + self.url +
                    '&sq=other">' + m.TITLE + '</a></main>')
        self.assertEqual(m.inspect_caller_html(doubled, self.detail)["same_id_review"], 1)
        # Invalid query is ignored; a second valid URL with differing canonical
        # representation is rejected rather than silently treated as a new event.
        other = self.listing.replace("</main>", '<a href="' + self.url.replace(
            "&sq=&", "&") + '">' + m.TITLE + '</a></main>')
        self.assertEqual(m.inspect_caller_html(other, self.detail)["same_id_review"], 0)


if __name__ == "__main__":
    unittest.main()

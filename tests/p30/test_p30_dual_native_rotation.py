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

    def test_invalid_line(self):
        with self.assertRaises(ValueError): m.run_next_native_once("C")
        with self.assertRaises(ValueError): m.inspect_next_pair("C","","")

if __name__ == "__main__":
    unittest.main()

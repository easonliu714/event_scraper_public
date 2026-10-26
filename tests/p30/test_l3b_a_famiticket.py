"""Source-bound FamiTicket L3B-A tests; no checkout or user session."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

file=Path(__file__).resolve().parents[2]/"scripts"/"p30_l3b_a_famiticket.py"
spec=importlib.util.spec_from_file_location("l3b_fami",file)
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

U="https://www.famiticket.com.tw/Home/Activity/Info/MABvAE4ALwBxAEkAcQB3ADkAawB0AHUASgBlAGwAZwA3AGkAOQBsAEwARgB2AE8ASwBTAGMAMQB5AEYAMQBOAE8AQgBBAHkAdwBaAEYAagBKAHMAawA9AA2"
HTML=("""<html><body><div class="hot">
<a href="/Home/Activity/Info/MABvAE4ALwBxAEkAcQB3ADkAawB0AHUASgBlAGwAZwA3AGkAOQBsAEwARgB2AE8ASwBTAGMAMQB5AEYAMQBOAE8AQgBBAHkAdwBaAEYAagBKAHMAawA9AA2">
<span>展覽</span><span>2026/11/06-2026/11/09</span><h3>2026 ITF 台灣國際旅展</h3><button>購票</button></a>
<a href="/Home/Activity/Info/RgBhADYAOABvAGoANQBDAEYAdQB0AEIAbwBVACsAOAB0AGUAUgBkADUAMABrADUAVABiAE0AMwB4ADcAcABMAHoAUgB2AGMAVABSAFEAbQB3AG8ARQA9AA2">
<span>展覽</span><h3>Ultra Taiwan 2026 超世代音樂節</h3></a>
<a href="/Login">登入</a><a href="https://attacker.invalid/Home/Activity/Info/ABC123">假活動</a>
</div></body></html>""").encode("utf-8")
DETAIL=b"<html><h2>2026 ITF \xe5\x8f\xb0\xe7\x81\xa3\xe5\x9c\x8b\xe9\x9a\x9b\xe6\x97\x85\xe5\xb1\x95</h2><button>\xe6\x88\x91\xe8\xa6\x81\xe8\xb3\xbc\xe7\xa5\xa8</button></html>"


class FakeResponse:
    def __init__(self,data,code=200,ctype="text/html; charset=utf-8",loc=None):
        self.status_code=code
        self.headers={"content-type":ctype}
        if loc:self.headers["location"]=loc
        self.data=data
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def iter_content(self,chunk_size=32768):yield self.data

class Session:
    def __init__(self,responses):
        self.responses=iter(responses)
        self.calls=[]
    def get(self,url,**kw):
        assert kw["allow_redirects"] is False and kw["stream"]
        self.calls.append(url)
        return next(self.responses)


class Tests(unittest.TestCase):
    def test_home_exact_https_allowlist(self):
        self.assertTrue(p.allowed(p.LIST))
        self.assertTrue(p.allowed(U,detail=True))
        for u in ("http://www.famiticket.com.tw/Home",
                  "https://www.famiticket.com.tw.evil.com/Home",
                  "https://www.famiticket.com.tw@evil.com/Home",
                  "https://www.famiticket.com.tw:8080/Home",
                  "https://www.famiticket.com.tw/admin",
                  "file:///etc/passwd"):
            self.assertFalse(p.allowed(u))
        for bad in ("https://www.famiticket.com.tw/Home/Activity/Search/242",
                    "https://www.famiticket.com.tw/Home/Activity/Info/bad",
                    "https://evil.com/Home/Activity/Info/MABvAE4ALwBxAEkAcQB3ADkAawB0AHUASgBlAGwAZwA3AGkAOQBsAEwARgB2AE8ASwBTAGMAMQB5AEYAMQBOAE8AQgBBAHkAdwBaAEYAagBKAHMAawA9AA2"):
            self.assertFalse(p.allowed(bad,detail=True))

    def test_list_card_identity_not_broad_navigation(self):
        rows,summary=p.parse_list(HTML)
        self.assertEqual(len(rows),2)
        self.assertEqual(summary["candidate_count"],2)
        self.assertEqual(rows[0]["title"],"2026 ITF 台灣國際旅展")
        self.assertEqual(rows[0]["official_url"],U)
        self.assertEqual(rows[0]["platform"],"FamiTicket")
        self.assertIsNone(rows[0]["dateStart"])
        self.assertEqual(rows[0]["ticketStatus"],"UNKNOWN")
        self.assertFalse(rows[0]["published"])

    def test_duplicate_detail_link_no_duplicate_activity(self):
        out,_=p.parse_list(HTML.replace(b"</body>",b'<a href="'+U.encode()+b'"><h3>2026 ITF \xe5\x8f\xb0\xe7\x81\xa3\xe5\x9c\x8b\xe9\x9a\x9b\xe6\x97\x85\xe5\xb1\x95</h3></a></body>'))
        self.assertEqual(len(out),2)

    def test_invalid_anchor_only_buy_cta(self):
        x='<a href="'+U+'">購票</a>'
        self.assertEqual(p.parse_list(x.encode("utf-8"))[0],[])

    def test_raw_dates_do_not_promote_to_official_schedule(self):
        x=p.parse_list(HTML)[0][0]
        self.assertEqual(x["rawScheduleRole"],"UNCLASSIFIED_LISTING_TEXT")
        self.assertTrue(x["rawScheduleText"])
        self.assertIsNone(x["dateStart"])
        self.assertIsNone(x["price"])

    def test_detail_title_verified_not_sold_status(self):
        row=p.parse_list(HTML)[0][0]
        result=p.sample_detail(DETAIL,row)
        self.assertEqual(result["state"],"DETAIL_TITLE_VERIFIED")
        self.assertEqual(result["ticketStatus"],"UNKNOWN")

    def test_detail_wrong_event_fails_closed(self):
        row=p.parse_list(HTML)[0][0]
        result=p.sample_detail("<h2>其他活動標題</h2>".encode(),row)
        self.assertEqual(result["state"],"TITLE_IDENTITY_HOLD")
        self.assertIsNone(result["dateStart"])

    def test_no_redirect_to_foreign_or_wrong_path(self):
        s=Session([FakeResponse(b"",code=302,loc="https://evil.com/")])
        html,meta=p.fetch(s,p.LIST)
        self.assertIsNone(html)
        self.assertEqual(meta["state"],"URL_NOT_ALLOWLISTED")
        self.assertEqual(len(s.calls),1)

    def test_403_429_never_retry(self):
        for code in (403,429):
            s=Session([FakeResponse(b"",code=code)])
            html,meta=p.fetch(s,p.LIST)
            self.assertIsNone(html)
            self.assertEqual(meta["http_status"],code)
            self.assertEqual(len(s.calls),1)

    def test_non_html_and_oversize_fail_closed(self):
        for resp,state in ((FakeResponse(b"{} ",ctype="application/json"),"NON_HTML"),
                           (FakeResponse(b"X"*(p.MAX_HTML+1)),"OVERSIZE_HTML")):
            html,meta=p.fetch(Session([resp]),p.LIST)
            self.assertIsNone(html)
            self.assertEqual(meta["state"],state)

    def test_one_page_one_detail_only_no_publish(self):
        session=Session([FakeResponse(HTML),FakeResponse(DETAIL)])
        with patch.object(p.time,"sleep") as sleep:
            rows,report=p.run(session)
        self.assertEqual(len(session.calls),2)
        self.assertEqual(len(rows),2)
        self.assertEqual(report["maxListGET"],1)
        self.assertEqual(report["maxDetailGET"],1)
        self.assertFalse(report["published"])
        self.assertFalse(report["goldenAccepted"])
        self.assertEqual(report["sample"]["state"],"DETAIL_TITLE_VERIFIED")
        sleep.assert_called_once()

    def test_empty_list_is_not_success(self):
        session=Session([FakeResponse(b"<html>nothing</html>")])
        rows,report=p.run(session)
        self.assertFalse(rows)
        self.assertEqual(report["sample"]["state"],"NOT_ATTEMPTED")

if __name__=="__main__":
    unittest.main()

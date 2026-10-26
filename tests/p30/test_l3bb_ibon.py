"""P30-L3-B-B ibon official public entertainment list scope, negative controls."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

p=Path(__file__).resolve().parents[2]/"scripts"/"p30_l3bb_ibon.py"
spec=importlib.util.spec_from_file_location("p30_l3bb",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
URL="https://ticket.ibon.com.tw/ActivityInfo/Details/40010"
URL2="https://ticket.ibon.com.tw/ActivityInfo/Details/39971"
SAMPLE="""<html><body>
 <section><a href="/ActivityInfo/Details/40010"><h3>2026 樂天桃猿感謝祭</h3><span>售票中</span></a></section>
 <div><a href="/Web/ActivityInfo/Details/39971"><h3>2026 OPEN！ DREAM WORLD 夢想音樂節</h3></a></div>
 <a href="/ActivityInfo/Details/40010"><h3>2026 樂天桃猿感謝祭</h3></a>
 <a href="/ActivityInfo/Details/40020">購票</a>
 <a href="https://other.host/ActivityInfo/Details/99999"><h3>假活動</h3></a>
 <a href="/Order/Checkout">前往訂購</a>
</body></html>"""
DETAIL="<h1>2026 樂天桃猿感謝祭</h1><p>2026/11/01 預計演出（未核對）</p>"
class Resp:
    def __init__(self,body=b"",status=200,typ="text/html; charset=utf-8",location=None):
        self.status_code=status
        self.headers={"content-type":typ}
        if location:self.headers["location"]=location
        self.body=body if isinstance(body,bytes) else body.encode("utf-8")
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def iter_content(self,chunk_size=32768):yield self.body
class Sess:
    def __init__(self,items):self.items=iter(items);self.called=[]
    def get(self,url,**kw):
        assert kw["allow_redirects"] is False and kw["stream"]
        self.called.append(url)
        return next(self.items)

class Case(unittest.TestCase):
    def test_exact_official_urls(self):
        self.assertTrue(m.role(m.LISTS[0],listing=True))
        self.assertTrue(m.role(m.LISTS[1],listing=True))
        self.assertTrue(m.role(URL,detail=True))
        self.assertTrue(m.role("https://ticket.ibon.com.tw/Web/ActivityInfo/Details/40010",detail=True))
        for v in ("http://ticket.ibon.com.tw/Index/entertainment",
                  "https://ticket.ibon.com.tw.evil.com/Index/entertainment",
                  "https://ticket.ibon.com.tw:8765/Index/entertainment",
                  "https://ticket.ibon.com.tw/Order/Checkout",
                  "https://ticket.ibon.com.tw/Activity/Index",
                  "file:///etc/passwd"):
            self.assertFalse(m.role(v,listing=True),v)
            self.assertFalse(m.role(v,detail=True),v)
    def test_id_bound_and_canonical(self):
        self.assertEqual(m.canonical_detail("/ActivityInfo/Details/40010",m.LISTS[0]),URL)
        self.assertEqual(m.canonical_detail("/Web/ActivityInfo/Details/40010",m.LISTS[0]),URL)
        self.assertIsNone(m.canonical_detail("/ActivityInfo/Details/notanid",m.LISTS[0]))
        self.assertIsNone(m.canonical_detail("https://evil.com/ActivityInfo/Details/40010",m.LISTS[0]))
        self.assertIsNone(m.canonical_detail("/ActivityInfo/Details/40010?orderId=1",m.LISTS[0]))
    def test_list_dedup_and_nonsale_inference(self):
        rows,stats=m.parse_list(SAMPLE,m.LISTS[0])
        self.assertEqual(len(rows),2)
        self.assertEqual(stats["detail_links_seen"],4)
        self.assertEqual(rows[0]["officialUrl"],URL)
        self.assertEqual(rows[0]["title"],"2026 樂天桃猿感謝祭")
        self.assertIsNone(rows[0]["dateStart"])
        self.assertEqual(rows[0]["ticketStatus"],"UNKNOWN")
        self.assertEqual(rows[0]["category"],"待分類")
        self.assertFalse(rows[0]["goldenVerified"])
    def test_no_cta_only(self):
        rows,_=m.parse_list("<a href='/ActivityInfo/Details/40010'>購票</a>",m.LISTS[0])
        self.assertEqual(rows,[])
    def test_html_shell_not_a_list(self):
        rows,stats=m.parse_list("<main>請使用 JavaScript</main>",m.LISTS[0])
        self.assertEqual(rows,[])
        self.assertEqual(stats["candidates"],0)
    def test_detail_title_exact(self):
        row=m.parse_list(SAMPLE,m.LISTS[0])[0][0]
        a=m.verify_detail(DETAIL,row)
        self.assertEqual(a["state"],"TITLE_MATCH")
        self.assertIsNone(a["dateStart"])
        self.assertEqual(a["ticketStatus"],"UNKNOWN")
    def test_detail_mismatch_hold(self):
        row=m.parse_list(SAMPLE,m.LISTS[0])[0][0]
        self.assertEqual(m.verify_detail("<div>模糊活動</div>",row)["state"],
                         "TITLE_MISMATCH_OR_HTML_SHELL_HOLD")
    def test_403_429_no_retry(self):
        for c in (403,429):
            s=Sess([Resp(status=c)])
            data,diag=m.get_html(s,m.LISTS[0],listing=True)
            self.assertIsNone(data)
            self.assertEqual(diag["http_status"],c)
            self.assertEqual(len(s.called),1)
    def test_foreign_redirect_denied(self):
        s=Sess([Resp(status=302,location="https://evil.com/")])
        data,diag=m.get_html(s,m.LISTS[0],listing=True)
        self.assertIsNone(data)
        self.assertEqual(diag["state"],"REDIRECT_REJECTED")
        self.assertEqual(len(s.called),1)
    def test_json_and_html_oversize(self):
        for response,expected in ((Resp("{}",typ="application/json"),"NON_HTML"),
            (Resp("a"*(m.MAX_BYTES+1)),"OVERSIZE_HTML")):
            data,diag=m.get_html(Sess([response]),m.LISTS[0],listing=True)
            self.assertIsNone(data)
            self.assertEqual(diag["state"],expected)
    def test_three_requests_cap(self):
        s=Sess([Resp(SAMPLE),Resp("<html>空的第二頁</html>"),Resp(DETAIL)])
        with patch.object(m.time,"sleep"):
            rows,diag=m.run(s)
        self.assertEqual(len(s.called),3)
        self.assertEqual(len(rows),2)
        self.assertEqual(diag["counts"]["listHTTP200"],2)
        self.assertEqual(diag["detail"]["state"],"TITLE_MATCH")
        self.assertEqual(diag["maxListGET"],2)
        self.assertEqual(diag["maxDetailGET"],1)
        self.assertFalse(diag["goldenAccepted"])
        self.assertFalse(diag["appDataPublished"])
        self.assertEqual(diag["autoHidden"],0)
    def test_empty_list_gets_no_detail(self):
        s=Sess([Resp("<html>shell</html>"),Resp("<html>shell</html>")])
        with patch.object(m.time,"sleep"):
            rows,diag=m.run(s)
        self.assertEqual(rows,[])
        self.assertEqual(len(s.called),2)
        self.assertEqual(diag["detail"]["state"],"NOT_ATTEMPTED")
    def test_delay_fail_closed(self):
        with self.assertRaises(ValueError):
            m.run(Sess([]),delay=0.2)

if __name__=="__main__":unittest.main()

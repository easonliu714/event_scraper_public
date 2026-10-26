"""P30-L7-D: only one postponed source, strict HTTP and date provenance guards."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

name=Path(__file__).resolve().parents[2]/"scripts"/"p30_l7d_official_fallback.py"
spec=importlib.util.spec_from_file_location("l7d",name)
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

TWTC="<h2>2026台北金融科技展【展覽延期】</h2><p>".encode("utf-8")+(
    "展出日期：2026/10/23 ~ 2026/10/24</p>".encode("utf-8"))
CO="""<article><h1>[重要通知]-因颱風影響，10/23-24 台北金融科技展延期舉行</h1>
<p>因颱風影響，台北金融科技展延期辦理，調整時間將於10月底前公告確認。</p></article>""".encode("utf-8")
INST="""<h1>〖活動延期通知〗FinTech Taipei 2026 台北金融科技展</h1>
<p>因應10月23日至24日的影響，台北金融科技展將延期至12月18日（五）至12月19日（六）辦理。</p>""".encode("utf-8")


def parent():
    rows=[]
    for i in range(5):
        rows.append({"id":"ck"+str(i),"platform":"中正紀念堂","title":"文化活動"})
    for i in range(39):
        bad=i==20
        rows.append({"id":"tw"+str(i),"platform":"台北世貿",
                     "title":"2026台北金融科技展【展覽延期】" if bad else "2026展覽"+str(i),
                     "officialUrl":p.ORIGINAL_URL if bad else f"https://twtc.com.tw/exhibition_more.aspx?id={33000+i}&p=home",
                     "rawPeriod":"延期未定" if bad else "11/06 ~ 11/09",
                     "dateEvidenceStatus":"LIST_DETAIL_PERIOD_CONFLICT" if bad else "DATE_VERIFIED_BY_OFFICIAL_DETAIL_CANDIDATE",
                     "dateStart":None if bad else "2026-11-06",
                     "dateEnd":None if bad else "2026-11-09"})
    return {"kind":p.BASE_KIND,"count":44,"items":rows,"dateVerifiedCount":38,
            "dateUnverifiedCount":1,"goldenAccepted":False,"published":False,
            "writerExecuted":False,"notificationExecuted":False,
            "autoHidden":0,"sourceRuntime":"DORMANT"}


class Response:
    def __init__(self,code=200,body=b"<html>ok</html>",ctype="text/html",loc=None):
        self.status_code=code
        self.body=body
        self.headers={"content-type":ctype}
        if loc:self.headers["location"]=loc
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def iter_content(self,chunk_size=16384):yield self.body


class Session:
    def __init__(self,responses):
        self.responses=iter(responses)
        self.calls=[]
    def get(self,url,**kw):
        self.calls.append(url)
        assert kw["allow_redirects"] is False and kw["stream"]
        return next(self.responses)


class P30L7DTests(unittest.TestCase):
    def test_allow_three_exact_official_https_documents(self):
        self.assertTrue(all(p.allow(url,url) for url in p.SOURCE_URLS))
        for bad in ("http://www.tfsr.org.tw/information/187",
                    "https://www.tfsr.org.tw/information/188",
                    "https://www.tfsr.org.tw:8080/information/187",
                    "https://www.tfsr.org.tw@evil.com/information/187",
                    "https://nccc.com.tw/wps/wcm/connect/zh/home/AboutNCCC/News/200261021-2",
                    "https://twtc.com.tw/exhibition_more.aspx?id=10000",
                    "file:///etc/passwd"):
            self.assertFalse(p.allow(bad,p.CO_ORGANIZER_URL))

    def test_original_same_format(self):
        self.assertEqual(p.parse_twtc_original(TWTC),("2026-10-23","2026-10-24"))

    def test_source_organization_postponement_notice(self):
        self.assertEqual(p.parse_co_organizer(CO),"POSTPONED_PENDING_FINAL_CONFIRMATION")

    def test_financial_institution_references_tentative(self):
        self.assertEqual(p.parse_financial_notice(INST),("2026-12-18","2026-12-19"))

    def test_missing_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"IDENTITY"):
            p.parse_co_organizer(b"<h1>other event</h1>")
        with self.assertRaisesRegex(ValueError,"IDENTITY"):
            p.parse_financial_notice("<p>延期至12月18日至12月19日</p>".encode("utf-8"))

    def test_date_changed_fails_closed(self):
        bad=INST.replace("12月18日".encode(),"12月21日".encode())
        with self.assertRaisesRegex(ValueError,"DATE_TEXT_CHANGED"):
            p.parse_financial_notice(bad)

    def test_redirect_outside_official_fails_closed_without_get(self):
        s=Session([Response(code=302,loc="https://malicious.example/")])
        html,meta=p.get_one(s,p.CO_ORGANIZER_URL)
        self.assertIsNone(html)
        self.assertEqual(meta["state"],"UNAPPROVED_REDIRECT")
        self.assertEqual(len(s.calls),1)

    def test_http_403_404_no_retry(self):
        for code in (403,404,429):
            with self.subTest(code=code):
                sess=Session([Response(code=code)])
                html,meta=p.get_one(sess,p.FINANCIAL_INSTITUTION_URL)
                self.assertIsNone(html)
                self.assertEqual(len(sess.calls),1)
                self.assertEqual(meta["http_status"],code)

    def test_size_and_mime_limit(self):
        for rsp,state in ((Response(ctype="application/json"),"NON_HTML"),
                          (Response(body=b"x"*(p.MAX_BYTES+1)),"HTML_SIZE_LIMIT"),
                          (Response(body=b""),"EMPTY_BODY")):
            html,meta=p.get_one(Session([rsp]),p.CO_ORGANIZER_URL)
            self.assertIsNone(html)
            self.assertEqual(meta["state"],state)

    def test_one_postponed_row_and_parent_flags(self):
        self.assertEqual(p.select_one(parent())["id"],"tw20")
        candidate=parent()
        candidate["published"]=True
        with self.assertRaisesRegex(ValueError,"PARENT_FLAG"):
            p.select_one(candidate)
        candidate=parent()
        candidate["items"][25]["officialUrl"]="https://evil.com/"
        with self.assertRaisesRegex(ValueError,"DETAIL_BINDING"):
            p.select_one(candidate)

    def test_overlay_44_38_one_without_false_confirmation(self):
        before=parent()
        restored,evidence=p.enrich(before,("2026-10-23","2026-10-24"),
                                  ("2026-12-18","2026-12-19"),
                                  "POSTPONED_PENDING_FINAL_CONFIRMATION",
                                  {"https://twtc.com.tw":"ok"})
        old=before["items"]
        new=restored["items"]
        self.assertEqual(len(new),44)
        self.assertEqual(sum(a!=b for a,b in zip(old,new)),1)
        self.assertEqual(restored["dateVerifiedCount"],38)
        self.assertIsNone(new[25]["dateStart"])
        self.assertIsNone(new[25]["confirmedDateStart"])
        self.assertEqual(new[25]["originalDateStart"],"2026-10-23")
        self.assertEqual(new[25]["tentativeDateEnd"],"2026-12-19")
        self.assertEqual(evidence["confirmed"],None)
        self.assertFalse(restored["published"])

    def test_secondary_official_status_only_without_tentative(self):
        restored,evidence=p.enrich(parent(),("2026-10-23","2026-10-24"),
                                  None,"POSTPONED_PENDING_FINAL_CONFIRMATION",{})
        x=restored["items"][25]
        self.assertIsNone(x["tentativeDateStart"])
        self.assertEqual(x["scheduleStatus"],"POSTPONED_PENDING_FINAL_CONFIRMATION")

    def test_no_verified_postponement_source_blocks_candidate(self):
        with self.assertRaisesRegex(ValueError,"NOTICE_UNVERIFIED"):
            p.enrich(parent(),("2026-10-23","2026-10-24"),None,None,{})


if __name__=="__main__":
    unittest.main()

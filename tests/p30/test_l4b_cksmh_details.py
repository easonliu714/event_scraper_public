"""P30 L4B offline identity, sessions, venue and fail-closed tests."""
import importlib.util
import unittest
from pathlib import Path

path=Path(__file__).resolve().parents[2]/"scripts"/"p30_l4b_cksmh_details.py"
spec=importlib.util.spec_from_file_location("p30_l4b_cksmh",path)
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

TANG="2026年第七屆唐獎榮耀展(免費入場)"
TANG_URL="https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId=61004"
HTML=("""<html lang="zh-Hant"><header><a>首頁</a> 活動明細</header>
<h2>"""+TANG+"""</h2>
<div>時間：2026年9月1日~2026年10月30日 地點：中正紀念堂1樓中央通廊</div>
<section><h3>場次資料</h3><p>場次: """+TANG+"""</p>
<span>2026/09/01 09:00 ~ 2026/10/30 18:00</span>
<p>場 地 <a href="https://maps.google.com/?q=cksmh">中央通廊</a></p></section>
<span>主辦單位：財團法人唐獎教育基金會</span>
<section><h3>活動內容介紹</h3><p>
2026年第七屆「唐獎榮耀展」以「以智慧為光 點亮全球」為核心概念，
結合科技與藝術，帶領大眾認識唐獎得主在永續發展、生技醫藥、漢學及法治四大領域的卓越成就。
</p></section><footer>地址：100012-臺北市中正區中山南路21號</footer>
</html>""").encode("utf-8")
MULTI=("""<h2>多場次講座活動</h2>
<h3>場次資料</h3><p>2026/11/07 13:00 ~ 2026/11/07 15:00</p>
<p>2026/11/14 14:00 ~ 2026/11/14 16:00</p>
<span>場 地 <a href="https://maps.google.com/?q=hall2">中央通廊</a></span>
<h3>活動內容介紹</h3><p>不同場次分開報名，確實以官方公告為準。</p>""").encode("utf-8")


def sample(title=TANG+"圖片說明",idx=61004):
    return {"id":"test"+str(idx),"platform":"中正紀念堂","title":title,
            "officialUrl":"https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId="+str(idx),
            "dateStart":None,"dateEnd":None,"ticketStatus":"UNKNOWN",
            "goldenVerified":False,"validity":"UNCERTAIN"}


def parent():
    ck=[sample("2026年第七屆唐獎榮耀展(免費入場)圖片說明" if i==0 else
               "活動 "+str(i),61004+i) for i in range(5)]
    tw=[{"id":"tw"+str(i),"platform":"台北世貿","title":"活動 "+str(i),
         "dateStart":"2026-11-06","dateEnd":"2026-11-09",
         "ticketStatus":"UNKNOWN","validity":"UNCERTAIN"} for i in range(39)]
    return {"kind":p.PARENT_KIND,"count":44,"items":ck+tw,
            "goldenAccepted":False,"published":False,"writerExecuted":False,
            "notificationExecuted":False,"autoHidden":0,"sourceRuntime":"DORMANT"}


def response_record(row,html=HTML):
    fields=p.extract(html,row)
    return {"id":row["id"],"title":row["title"],"officialUrl":row["officialUrl"],
            "http":{"state":"HTTP_OK","http_status":200,"sha256":"a"*64},
            "fields":fields}


class Tests(unittest.TestCase):
    def test_canonical_id_same_origin_and_session_sanitization(self):
        self.assertEqual(p.exact_act_id(TANG_URL),"61004")
        self.assertEqual(p.exact_act_id(TANG_URL.replace(".ctr?",".ctr;jsessionid=HELLO?")),"61004")
        for unsafe in ("http://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId=61004",
                       "https://evil.com/mocweb/reg/CKSMH/Detail.init.ctr?actId=61004",
                       "https://event.culture.tw@evil.com/mocweb/reg/CKSMH/Detail.init.ctr?actId=61004",
                       "https://event.culture.tw:8080/mocweb/reg/CKSMH/Detail.init.ctr?actId=61004",
                       "https://event.culture.tw/mocweb/reg/CKSMH/OtherPage?actId=61004",
                       "https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId=100&actId=200"):
            self.assertIsNone(p.exact_act_id(unsafe))

    def test_title_accessibility_suffix_safely_removed(self):
        self.assertEqual(p.short_title(TANG+"圖片說明"),TANG)
        fields=p.extract(HTML,sample())
        self.assertEqual(fields["state"],"DETAIL_TITLE_VERIFIED")
        self.assertEqual(fields["officialTitle"],TANG)

    def test_one_full_session_and_venue(self):
        fields=p.extract(HTML,sample())
        self.assertEqual(fields["dateStart"],"2026-09-01")
        self.assertEqual(fields["dateEnd"],"2026-10-30")
        self.assertEqual(fields["sessionCount"],1)
        self.assertEqual(fields["sessions"][0]["start"],"2026-09-01T09:00")
        self.assertEqual(fields["sessions"][0]["end"],"2026-10-30T18:00")
        self.assertEqual(fields["venue"],"中央通廊")
        self.assertEqual(fields["timeRole"],"OFFICIAL_SINGLE_SESSION")

    def test_summary_only_official_intro_not_footer(self):
        fields=p.extract(HTML,sample())
        self.assertIn("唐獎榮耀展",fields["summary"])
        self.assertNotIn("地址：",fields["summary"])
        self.assertEqual(fields["summaryRole"],"OFFICIAL_DETAIL_INTRO_EXCERPT")

    def test_missing_title_fails_all_fields(self):
        fields=p.extract(HTML,sample("完全不同活動"))
        self.assertEqual(fields["state"],"TITLE_IDENTITY_HOLD")
        self.assertIsNone(fields["dateStart"])
        self.assertIsNone(fields["venue"])

    def test_multisession_kept_as_individual_occurrences(self):
        f=p.extract(MULTI,sample("多場次講座活動"))
        self.assertEqual(f["dateStart"],"2026-11-07")
        self.assertEqual(f["dateEnd"],"2026-11-14")
        self.assertEqual(f["timeRole"],"OFFICIAL_MULTIPLE_SESSIONS_BOUNDS")
        self.assertEqual(len(f["sessions"]),2)
        self.assertEqual(f["sessions"][1]["start"],"2026-11-14T14:00")

    def test_invalid_chronology_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"INVERTED"):
            p.parse_dates(("2026/11/14","16:00","2026/11/14","14:00"))
        with self.assertRaises(ValueError):
            p.parse_dates(("2026/02/30","09:00","2026/03/01","12:00"))

    def test_parent_44_and_five_identity_validation(self):
        self.assertEqual(len(p.validate_parent(parent())),5)
        obj=parent()
        obj["published"]=True
        with self.assertRaisesRegex(ValueError,"PARENT_FLAG"):
            p.validate_parent(obj)
        obj=parent()
        obj["items"][1]["officialUrl"]=obj["items"][0]["officialUrl"]
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            p.validate_parent(obj)

    def test_overlay_only_five_frozen_source_events(self):
        original=parent()
        records=[response_record(x,HTML) if i==0 else
                 {"id":x["id"],"title":x["title"],"officialUrl":x["officialUrl"],
                  "http":{"state":"HTTP_ERROR","http_status":404},"fields":None}
                 for i,x in enumerate(original["items"][:5])]
        new,counts=p.enrich(original,records)
        self.assertEqual(new["count"],44)
        self.assertEqual(counts["date_bound"],1)
        self.assertEqual(counts["venue_bound"],1)
        self.assertEqual([x["id"] for x in original["items"]],[x["id"] for x in new["items"]])
        self.assertEqual(original["items"][0]["dateStart"],None)
        self.assertEqual(original["items"][5:],new["items"][5:])
        self.assertFalse(new["published"])

    def test_overlay_refuses_borrowed_event_fields(self):
        o=parent()
        fields=[response_record(x) for x in o["items"][:5]]
        fields[1]["title"]=TANG
        with self.assertRaisesRegex(ValueError,"TITLE_URL_MISMATCH"):
            p.enrich(o,fields)

    def test_no_verified_date_is_explicit_hold(self):
        o=parent()
        records=[{"id":x["id"],"title":x["title"],"officialUrl":x["officialUrl"],
                  "http":{"state":"HTTP_ERROR","http_status":404},"fields":None}
                 for x in o["items"][:5]]
        with self.assertRaisesRegex(ValueError,"NO_CKSMH_DATE_BOUND"):
            p.enrich(o,records)


class OfficialListIdentityFallback(unittest.TestCase):
    def test_official_list_actid_bound_date_and_venue(self):
        r=sample("自由花蕊(免費參觀)",51331)
        html=('''<main><div class="card"><a href="/mocweb/reg/CKSMH/Detail.init.ctr?actId=51331">自由花蕊(免費參觀)</a>
          <p>活動地點 常設展廳</p><p>活動時間 2025/11/24 ~ 2030/12/31</p></div>
          <div class="card"><a href="/mocweb/reg/CKSMH/Detail.init.ctr?actId=61004">其他活動</a>
          <p>活動地點 中央通廊</p><p>活動時間 2026/09/01 ~ 2026/10/30</p></div></main>''').encode("utf-8")
        bound=p.parse_list_bound(html,[r])
        self.assertEqual(bound["51331"]["dateStart"],"2025-11-24")
        self.assertEqual(bound["51331"]["dateEnd"],"2030-12-31")
        self.assertEqual(bound["51331"]["venue"],"常設展廳")
        self.assertNotIn("61004",bound)

    def test_wrong_list_anchor_title_cannot_fill_event(self):
        r=sample("自由花蕊(免費參觀)",51331)
        html=b'<div><a href="/mocweb/reg/CKSMH/Detail.init.ctr?actId=51331">Other</a><p>活動時間 2025/11/24 ~ 2030/12/31</p></div>'
        self.assertEqual(p.parse_list_bound(html,[r]),{})

    def test_exact_detail_title_prerequisite_for_list_overlay(self):
        original=parent()
        target=original["items"][0]
        item=response_record(target,HTML)
        records=[item]+[{"id":x["id"],"title":x["title"],"officialUrl":x["officialUrl"],
                         "http":{"state":"HTTP_ERROR","http_status":404},"fields":None}
                        for x in original["items"][1:5]]
        _,counts=p.enrich(original,records,{"61004":{"title":TANG,"actId":"61004",
                          "dateStart":"2026-09-01","dateEnd":"2026-10-30","venue":"中央通廊"}})
        self.assertEqual(counts["date_bound"],1)
        records[0]["fields"]["officialTitle"]="forged"
        with self.assertRaisesRegex(ValueError,"LIST_DETAIL_IDENTITY"):
            p.enrich(original,records,{"61004":{"title":TANG,"actId":"61004",
                          "dateStart":"2026-09-01","dateEnd":"2026-10-30","venue":"中央通廊"}})


if __name__=="__main__":
    unittest.main()

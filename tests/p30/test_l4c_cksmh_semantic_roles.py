"""P30-L4-C fail-closed semantic date role regression tests."""
import importlib.util
import unittest
from pathlib import Path

p=Path(__file__).resolve().parents[2]/"scripts"/"p30_l4c_cksmh_semantic_roles.py"
spec=importlib.util.spec_from_file_location("l4c",p)
import sys
sys.path.insert(0,str(p.parent))
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

LECTURE_TITLE="自由花蕊系列講座PartII：自己的房間（免費報名入場）"
LECTURE=b""+("""<h2>"""+LECTURE_TITLE+"""</h2><h3>場次資料</h3>
<div>場次: 〖1〗2026/11/07 (六) 1400-1600 《間隙中的她們》</div>
<p>場次介紹 女性視角的時代風景。</p>
<p>報 名 期 間 2026/10/16 11:30 ~ 2026/11/07 16:00</p>
<p>名額 150</p><p>場 地 中正紀念堂1樓演藝廳</p>
<div>場次: 〖2〗2026/11/13 (五) 1400-1600 《她的美麗探險》</div>
<p>報 名 期 間 2026/10/16 11:30 ~ 2026/11/13 16:00</p>
<p>名額 30</p><p>場 地 中正紀念堂1樓圖書室</p>
<h3>活動內容介紹</h3><p>長篇摘要不是場次資料。</p>""").encode("utf-8")
BOOK_TITLE="《民主大冒險》圖文書新書分享會"
BOOK=("""<h2>"""+BOOK_TITLE+"""</h2><h3>場次資料</h3>
<div>場次: 跨越世代的對談與交會 2026/11/04 14:40 ~ 2026/11/04 16:00</div>
<p>報　名　期　間 2026/10/01 10:00 ~ 2026/10/29 12:00</p>
<p>場 地 中正紀念堂演藝廳</p>
<div>場次: 聽見她們的勇氣 2026/11/07 14:00 ~ 2026/11/07 15:30</div>
<p>報 名 期 間 2026/10/19 12:00 ~ 2026/11/06 12:00</p>
<p>場 地 桃園市立圖書館總館3樓親子小學堂</p>
<h3>活動內容介紹</h3><p>開始活動內容。</p>""").encode("utf-8")
EXHIBITION="""<h2>自由花蕊(免費參觀)</h2><h3>活動內容介紹</h3><p>常設展。</p>""".encode("utf-8")


def row(act,title,date_start=None,role="UNKNOWN"):
    return {"id":str(act),"platform":"中正紀念堂","title":title,
            "officialUrl":"https://event.culture.tw/mocweb/reg/CKSMH/Detail.init.ctr?actId="+str(act),
            "dateStart":date_start,"dateEnd":date_start,"timeRole":role,
            "ticketStatus":"UNKNOWN","validity":"UNCERTAIN","goldenVerified":False}


def parent():
    ck=[row(61021,LECTURE_TITLE,"2026-10-16","OFFICIAL_MULTIPLE_SESSIONS_BOUNDS"),
        row(61024,BOOK_TITLE,"2026-10-01","OFFICIAL_MULTIPLE_SESSIONS_BOUNDS"),
        row(51331,"自由花蕊(免費參觀)","2025-11-24","OFFICIAL_LIST_ACTID_BOUND_DATE_RANGE"),
        row(61004,"2026年第七屆唐獎榮耀展(免費入場)","2026-09-01","OFFICIAL_SINGLE_SESSION"),
        row(61026,"樸書·曹淑美作品展(免費參觀)","2026-10-15","OFFICIAL_SINGLE_SESSION")]
    tw=[{"id":"tw"+str(i),"platform":"台北世貿","title":"展覽"+str(i),
         "ticketStatus":"UNKNOWN","dateStart":"2026-11-06","dateEnd":"2026-11-09"}
        for i in range(39)]
    return {"kind":m.PARENT_KIND,"count":44,"items":ck+tw,
            "published":False,"goldenAccepted":False,"writerExecuted":False,
            "notificationExecuted":False,"sourceRuntime":"DORMANT","autoHidden":0}


def make_records(src):
    result=[]
    for x in src["items"][:5]:
        act=m.exact_act_id(x["officialUrl"])
        roles=m.parse_event(LECTURE if act=="61021" else BOOK if act=="61024" else EXHIBITION,x)
        result.append({"id":x["id"],"title":x["title"],"officialUrl":x["officialUrl"],
                       "actId":act,"http":{"state":"HTTP_OK","sha256":"a"*64},"roles":roles})
    return result


class DateRoles(unittest.TestCase):
    def test_lecture_uses_november_sessions_not_october_registration(self):
        f=m.parse_event(LECTURE,row(61021,LECTURE_TITLE))
        self.assertEqual(f["state"],"OFFICIAL_EVENT_SESSIONS_VERIFIED")
        self.assertEqual(f["eventDateStart"],"2026-11-07")
        self.assertEqual(f["eventDateEnd"],"2026-11-13")
        self.assertEqual([s["start"] for s in f["sessions"]],
                         ["2026-11-07T14:00","2026-11-13T14:00"])
        self.assertEqual(f["registrationWindows"][0]["start"],"2026-10-16T11:30")

    def test_lecture_sessions_venue_distinct(self):
        x=m.parse_event(LECTURE,row(61021,LECTURE_TITLE))
        self.assertIn("演藝廳",x["sessions"][0]["venue"])
        self.assertIn("圖書室",x["sessions"][1]["venue"])

    def test_book_sessions_and_registration_windows_separate(self):
        x=m.parse_event(BOOK,row(61024,BOOK_TITLE))
        self.assertEqual(x["eventDateStart"],"2026-11-04")
        self.assertEqual(x["eventDateEnd"],"2026-11-07")
        self.assertEqual(len(x["sessions"]),2)
        self.assertEqual(len(x["registrationWindows"]),2)
        self.assertEqual(x["sessions"][1]["start"],"2026-11-07T14:00")
        self.assertEqual(x["registrationWindows"][1]["end"],"2026-11-06T12:00")

    def test_venue_nontransferrable_across_sessions(self):
        o=parent()
        new,counts=m.build(o,make_records(o))
        self.assertIsNone(new["items"][0]["venue"])
        self.assertIn("多場次",new["items"][0]["venueNote"])
        self.assertEqual(new["items"][0]["sessions"][0]["role"],"OFFICIAL_EVENT_SESSION_TIME")
        self.assertEqual(new["items"][0]["registrationWindows"][0]["role"],"OFFICIAL_REGISTRATION_WINDOW")

    def test_false_registration_only_never_becomes_event(self):
        raw=("""<h2>"""+LECTURE_TITLE+"""</h2><h3>場次資料</h3>
        <div>場次: 《活動未公告日期》 報 名 期 間 2026/10/16 11:30 ~ 2026/11/07 16:00</div>
        <h3>活動內容介紹</h3><p>文字敘述</p>""").encode("utf-8")
        f=m.parse_event(raw,row(61021,LECTURE_TITLE))
        self.assertEqual(f["state"],"HOLD_NO_OFFICIAL_EVENT_SESSION")
        self.assertIsNone(f["eventDateStart"])

    def test_no_sessions_keeps_official_listing_period_unclassified(self):
        x=m.parse_event(EXHIBITION,row(51331,"自由花蕊(免費參觀)"))
        self.assertEqual(x["state"],"NO_SESSION_SECTION")
        o=parent()
        new,c=m.build(o,make_records(o))
        flower=new["items"][2]
        self.assertEqual(flower["timeRole"],"OFFICIAL_LIST_PERIOD_UNCLASSIFIED")
        self.assertIsNone(flower["dateStart"])
        self.assertEqual(flower["listPeriodStart"],"2025-11-24")
        self.assertEqual(c["noSessionExhibitions"],1)

    def test_parse_title_wrong_fails_closed(self):
        f=m.parse_event(LECTURE,row(61021,"完全不同的活動"))
        self.assertEqual(f["state"],"HOLD_EVENT_TITLE_IDENTITY")

    def test_preserve_all_twtc_rows_exactly_and_44_ids(self):
        o=parent()
        data,c=m.build(o,make_records(o))
        self.assertEqual(len(data["items"]),44)
        self.assertEqual(o["items"][5:],data["items"][5:])
        self.assertEqual([r["id"] for r in o["items"]],[r["id"] for r in data["items"]])
        self.assertFalse(data["published"])

    def test_registration_must_be_explicitly_labelled(self):
        payload=LECTURE.replace("報 名 期 間".encode("utf-8"),"登記資料".encode("utf-8")).replace(
                "報 名 期 間".encode("utf-8"),"登記資料".encode("utf-8"))
        f=m.parse_event(payload,row(61021,LECTURE_TITLE))
        self.assertEqual(f["eventDateStart"],"2026-11-07")
        self.assertLess(len(f["registrationWindows"]),2)

    def test_bad_parent_flags_and_changed_id_rejected(self):
        o=parent()
        o["published"]=True
        with self.assertRaisesRegex(ValueError,"PARENT_FLAG"):
            m.verify_parent(o)
        o=parent()
        records=make_records(o)
        records[0]["actId"]="99999"
        with self.assertRaisesRegex(ValueError,"ACTID"):
            m.build(o,records)

    def test_invalid_and_reversed_dates_rejected(self):
        with self.assertRaises(ValueError):
            m.date_pair("2026/11/07","16:00","2026/11/07","14:00")
        with self.assertRaises(ValueError):
            m.date_pair("2026/02/30","09:00","2026/03/01","12:00")

    def test_header_and_full_date_duplicate_must_not_create_two_sessions(self):
        raw=("""<h2>"""+BOOK_TITLE+"""</h2><h3>場次資料</h3>
        <div>場次: 2026/11/04 14:40 ~ 2026/11/04 16:00</div>
        <p>報名期間 2026/10/01 10:00 ~ 2026/10/29 12:00</p>
        <h3>活動內容介紹</h3><p>完畢</p>""").encode("utf-8")
        f=m.parse_event(raw,row(61024,BOOK_TITLE))
        self.assertEqual(len(f["sessions"]),1)

if __name__=="__main__":
    unittest.main()
